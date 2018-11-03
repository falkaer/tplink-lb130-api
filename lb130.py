import socket
import sys
import time

from typing import Callable, Any
from multiprocessing.pool import ThreadPool
from threading import Thread

from cloudtplinkdevice import CloudTPLinkDevice
from protocol import UDPBroadcast, TCP, CloudProtocol

class LB130(CloudTPLinkDevice):
    
    def get_light_state(self) -> dict:
        
        r = self.send({
            'smartlife.iot.smartbulb.lightingservice': {
                'get_light_state': None
            }
        })
        
        if 'dft_on_state' in r:
            r.update(r['dft_on_state'])
            del r['dft_on_state']
        
        return r
    
    def transition_light_state(self, hue: int = None, saturation: int = None, brightness: int = None,
                               color_temp: int = None, on_off: bool = None, transition_period: int = None,
                               mode: str = None, ignore_default: bool = None) -> Any:
        
        # copy all given argument name-value pairs as a dict
        d = {k: v for k, v in locals().items() if k is not 'self' and v is not None}
        
        r = self.send({
            'smartlife.iot.smartbulb.lightingservice': {
                'transition_light_state': d
            }
        })
        
        if r is None:
            return
        
        # if the bulb is updated while in its off state
        # most of the bulbs status information is put 
        # into the dft_on_state namespace for no reason
        if 'dft_on_state' in r:
            r.update(r['dft_on_state'])
            del r['dft_on_state']
        
        return r
    
    def get_light_details(self) -> dict:
        
        return self.send({
            'smartlife.iot.smartbulb.lightingservice': {
                'get_light_details': None
            }
        })
    
    def on(self) -> Any:
        
        return self.transition_light_state(on_off=True)
    
    def off(self) -> Any:
        
        return self.transition_light_state(on_off=False)
    
    # TODO: scheduling and anti-burglary?

def discover_local(callback: Callable[[LB130, int], None], 
                   repeat: int, 
                   response_timeout: float, 
                   max_bulbs: int = sys.maxsize) -> int:
    
    total_time = repeat * response_timeout
    deviceIds = set()
    
    with UDPBroadcast() as conn:
        
        while repeat == 0 or total_time > 0:
            
            # broadcast system info request
            conn.send({
                'system': {
                    'get_sysinfo': {}
                }
            })
            
            response_time = response_timeout if repeat == 0 else min(total_time, response_timeout)
            
            # wait for responses in loop
            while response_time > 0:
                
                before = time.time()
                
                try:
                    
                    conn.sock.settimeout(response_time)
                    
                    # wait for response
                    response, addr = conn.recv()
                    
                    if 'LB130' in response['model']:
                        if not response['deviceId'] in deviceIds:
                            
                            deviceIds.add(response['deviceId'])
                            Thread(target=callback, 
                                   args=(LB130(TCP(addr[0]), sysinfo=response), len(deviceIds))).start()
                            
                            if len(deviceIds) == max_bulbs:
                                return len(deviceIds)
                            
                except socket.timeout:
                    pass
                
                elapsed = time.time() - before
                response_time -= elapsed
                total_time -= elapsed
    
    return len(deviceIds)

def discover_cloud(callback: Callable[[LB130, int], None], token: str) -> int:
    def cb(sysinfo, num):
        if 'LB130' in sysinfo['deviceModel']:
            # shared token - might matter for rate limiting? haven't tested the API extensively
            p = CloudProtocol(deviceId=sysinfo['deviceId'], token=token)
            
            # the cloud response sysinfo is different from regular sysinfo, 
            # but could still be useful, so keep it
            callback(LB130(p, sysinfo), num)
    
    with CloudProtocol(token=token) as conn:
        
        deviceList = conn.post('getDeviceList')['result']['deviceList']
        
        with ThreadPool(len(deviceList)) as p:
            for num, sysinfo in enumerate(deviceList):
                p.apply_async(cb, (sysinfo, num))
            
            p.close()
            p.join()
        
        return len(deviceList)
