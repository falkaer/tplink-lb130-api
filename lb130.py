import socket
import time

from typing import Callable

from protocol import UDPBroadcast, TCP
from tplinkdevice import TPLinkDevice

class LB130(TPLinkDevice):
    
    def get_light_state(self):
        
        r = self.send({
            'smartlife.iot.smartbulb.lightingservice': {
                'get_light_state': None
            }
        })
        
        if r is None:
            return
        
        if 'dft_on_state' in r:
            r.update(r['dft_on_state'])
            del r['dft_on_state']
        
        return r
    
    def transition_light_state(self, hue: int = None, saturation: int = None, brightness: int = None,
                               color_temp: int = None, on_off: bool = None, transition_period: int = None,
                               mode: str = None, ignore_default: bool = None):
        
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
    
    def on(self):
        
        return self.transition_light_state(on_off=True)
    
    def off(self):
        
        return self.transition_light_state(on_off=False)
    
    # TODO: scheduling and anti-burglary?

def discover(callback: Callable[[LB130], None], repeat: int, response_timeout: float):
    total_time = repeat * response_timeout
    
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
                        callback(LB130(TCP(addr[0]), sysinfo=response))
                
                except socket.timeout:
                    
                    pass
                
                finally:
                    
                    elapsed = time.time() - before
                    response_time -= elapsed
                    total_time -= elapsed
