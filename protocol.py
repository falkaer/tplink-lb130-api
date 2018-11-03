import json
import socket
from abc import abstractmethod, ABC
from typing import Union, Any, Tuple

from encryption import encrypt_headed, decrypt_headed, encrypt, decrypt

class TPLinkProtocol(ABC):
    port = 9999
    buf_size = 2048
    
    def __init__(self, ip):
        self.ip = ip
    
    @abstractmethod
    def __enter__(self):
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @abstractmethod
    def send(self, msg: Union[dict, str]) -> Any:
        pass
    
    @abstractmethod
    def recv(self) -> Tuple[dict, str]:
        pass
    
    def __eq__(self, other):
        return type(self) == type(other) and self.ip == other.ip and self.port == other.port
    
    def __hash__(self):
        return hash(type(self)) ^ hash(self.ip) ^ hash(self.port)

class TCP(TPLinkProtocol):
    
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
        enc_msg, addr = self.sock.recv(self.buf_size)
        
        # not interested in top level namespaces, discard them
        return json.loads(decrypt_headed(enc_msg)).popitem()[1].popitem()[1], addr

class UDP(TPLinkProtocol):
    
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
        enc_msg, addr = self.sock.recv(self.buf_size)
        
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
