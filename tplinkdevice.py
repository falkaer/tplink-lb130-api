import json
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
            
            # depending on the protocol there might not be a response
            r = conn.send(msg)
            
            if r is not None:
                if r == 'Module not support':
                    
                    if type(msg) is str:
                        msg = json.dumps(msg)
                    
                    raise ValueError('Device does not support module "' + next(iter(msg)) + '"')
                
                if isinstance(r, dict):
                    
                    if r['err_code'] is not 0:
                        raise ValueError(r['err_code'], r['err_msg'])
                    
                    del r['err_code']
            
            return r
    
    def get_sysinfo(self) -> dict:
        
        self.sysinfo = self.send({
            'system': {
                'get_sysinfo': None
            }
        })
        
        return self.sysinfo
    
    def reboot(self, delay: int = None) -> Any:
        
        return self.send({
            'smartlife.iot.common.system': {
                'reboot': {
                    'delay': delay
                }
            }
        })
    
    def set_dev_alias(self, alias: str) -> Any:
        
        return self.send({
            'system': {
                'set_dev_alias': {
                    'alias': alias
                }
            }
        })
