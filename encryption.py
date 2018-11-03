from typing import Union

encryption_key = 0xAB

def encrypt(msg: str) -> bytearray:
    l = len(msg)
    enc_msg = bytearray(l)
    
    key = encryption_key
    
    for i in range(l):
        enc_msg[i] = key ^ ord(msg[i])
        key = enc_msg[i]
    
    return enc_msg

def decrypt(enc_msg: Union[bytearray, bytes]) -> str:
    l = len(enc_msg)
    msg = bytearray(l)
    
    key = encryption_key
    
    for i in range(l):
        msg[i] = key ^ enc_msg[i]
        key = enc_msg[i]
    
    return str(msg, 'utf-8')

def encrypt_headed(msg: str) -> bytearray:
    # encode first four bytes as length of the packet in big-endian
    enc_msg = bytearray(len(msg).to_bytes(4, 'big'))
    enc_msg.extend(encrypt(msg))
    
    return enc_msg

def decrypt_headed(enc_msg: Union[bytearray, bytes]) -> str:
    return decrypt(enc_msg[4:])
