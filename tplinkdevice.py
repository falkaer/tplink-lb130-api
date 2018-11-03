from typing import Any, Union

from protocol import TPLinkProtocol

class TPLinkDevice:
    sysinfo = None
    
    def __init__(self, protocol: TPLinkProtocol, sysinfo: dict = None):
        
        self.protocol = protocol
        
        if sysinfo is not None:
            self.sysinfo = sysinfo
    
    def __eq__(self, other):
        
        return type(self) == type(other) and self.protocol == other.protocol
    
    def __hash__(self):
        
        return hash(type(self)) ^ hash(self.protocol)
    
    def send(self, msg: Union[str, dict]) -> Any:
        
        with self.protocol as conn:
            
            r = conn.send(msg)
            
            # if we're using TCP, send returns the bulb's response
            if r is not None:
                
                if r['err_code'] is not 0:
                    raise ValueError(r['err_code'], r['err_msg'])
                
                del r['err_code']
            
            return r
    
    def get_sysinfo(self):
        
        self.sysinfo = self.send({
            'system': {
                'get_sysinfo': None
            }
        })
        
        return self.sysinfo
    
    def reboot(self, delay: int = None):
        
        self.send({
            'smartlife.iot.common.system': {
                'reboot': {
                    'delay': delay
                }
            }
        })
