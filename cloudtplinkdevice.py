from typing import Any

from tplinkdevice import TPLinkDevice

class CloudTPLinkDevice(TPLinkDevice):
    
    def get_cloud_info(self) -> dict:
        
        return self.send({
            'smartlife.iot.common.cloud': {
                'get_info': None
            }
        })
    
    def bind_cloud(self, username, password) -> Any:
        
        return self.send({
            'smartlife.iot.common.cloud': {
                'bind': {
                    'username': username,
                    'password': password
                }
            }
        })
    
    def unbind_cloud(self) -> Any:
        
        return self.send({
            'smartlife.iot.common.cloud': {
                'unbind': None
            }
        })
    
    def get_firmware_list(self) -> dict:
        
        return self.send({
            'smartlife.iot.common.cloud': {
                'get_intl_fw_list': None
            }
        })['fw_list']
    
    def has_latest_firmware(self) -> bool:
        
        # empty firmware list means we have the latest firmware
        return not self.get_firmware_list()
    
    def update_firmware(self) -> Any:
        
        fw_list = self.get_firmware_list()
        
        if fw_list:
            
            url = fw_list[0]['fwUrl']
            
            self.send({
                'system': {
                    'download_firmware': {
                        'url': url # will only accept urls from TPLink servers
                    }
                }
            })
