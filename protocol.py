import json
import socket
from abc import abstractmethod, ABC
from typing import Union, Any, Tuple
from uuid import uuid4
import requests

from encryption import encrypt_headed, decrypt_headed, encrypt, decrypt

class TPLinkProtocol(ABC):
    @abstractmethod
    def __enter__(self):
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @abstractmethod
    def send(self, msg: Union[dict, str]) -> Any:
        pass

class LocalProtocol(TPLinkProtocol, ABC):
    port = 9999
    buf_size = 2048
    
    def __init__(self, ip):
        self.ip = ip
    
    @abstractmethod
    def recv(self) -> Tuple[dict, str]:
        pass
    
    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.ip == other.ip and self.port == other.port
    
    def __hash__(self) -> int:
        return hash(type(self)) ^ hash(self.ip) ^ hash(self.port)

class TCP(LocalProtocol):
    def __init__(self, ip: str, timeout: int = 0.5):
        super().__init__(ip)
        self.timeout = timeout
    
    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        
        self.sock.connect((self.ip, self.port))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()
    
    def send(self, msg: Union[dict, str]) -> dict:
        if type(msg) is dict:
            msg = json.dumps(msg)
        
        enc_msg = encrypt_headed(msg)
        
        self.sock.send(enc_msg)
        return self.recv()[0]
    
    def recv(self) -> Tuple[dict, str]:
        enc_msg, addr = self.sock.recvfrom(self.buf_size)
        
        # not interested in top level namespaces, discard them
        return json.loads(decrypt_headed(enc_msg)).popitem()[1].popitem()[1], addr

class UDP(LocalProtocol):
    def __enter__(self):
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()
    
    def send(self, msg: Union[dict, str]) -> None:
        if type(msg) is dict:
            msg = json.dumps(msg)
        
        enc_msg = encrypt(msg)
        self.sock.sendto(enc_msg, (self.ip, self.port))
    
    # if you use this, make sure to set an appropriate timeout value
    def recv(self) -> Tuple[dict, str]:
        enc_msg, addr = self.sock.recvfrom(self.buf_size)
        
        # not interested in top level namespaces, discard them
        return json.loads(decrypt(enc_msg)).popitem()[1].popitem()[1], addr

class UDPBroadcast(UDP):
    def __init__(self):
        super().__init__('255.255.255.255')
    
    def __enter__(self):
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        return self

class CloudProtocol(TPLinkProtocol):
    baseUrl = 'https://wap.tplinkcloud.com'
    uuid = uuid4().hex
    
    def __init__(self, deviceId: str = None, token: str = None):
        
        self.deviceId = deviceId
        self.token = token
        self.url = self.baseUrl
        
        # add token to url
        if self.token is not None:
            self.url = self.url + '?token=' + self.token
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def send(self, r: Union[dict, str]) -> dict:
        
        if self.token is None:
            raise ConnectionError('No token available')
        
        if self.deviceId is None:
            raise ConnectionError('No target deviceId specified')
        
        if isinstance(r, dict):
            r = json.dumps(r)
        
        resp = self.post('passthrough', {'deviceId': self.deviceId, 'requestData': r})
        
        # not interested in top level namespaces, discard them
        return json.loads(resp['result']['responseData']).popitem()[1].popitem()[1]
    
    def post(self, method: str, params: dict = None) -> dict:
        
        msg = {'method': method, 'params': params} if params is not None else {'method': method}
        r = requests.post(self.url, json=msg).json()
        
        if r['error_code'] is not 0:
            raise ValueError(r['error_code'], r['msg'])
        
        return r
    
    def __eq__(self, other) -> bool:
        return type(self) == type(other) and \
               self.deviceId == other.deviceId and \
               self.token == other.token
    
    def __hash__(self) -> int:
        return hash(type(self)) ^ \
               hash(self.deviceId) ^ \
               hash(self.token)

def get_cloud_token(username: str, password: str) -> str:
    with CloudProtocol() as conn:
        r = conn.post('login', {
            'appType'      : 'Kasa_Android',
            'cloudUserName': username,
            'cloudPassword': password,
            'terminalUUID' : conn.uuid
        })
        
        return r['result']['token']
