# transitions between red -> green -> blue -> red... 
# every 5 seconds, for a total of 15 seconds in a roundtrip

known_bulbs = 4

import socket
import time
from multiprocessing.pool import ThreadPool

bulbs = set()

from lb130 import discover_local

def cb(bulb, _):
    print('Discovered bulb at', bulb.protocol.ip)
    bulbs.add(bulb)

discover_local(cb, 10, 0.1, known_bulbs)
interval = 5

# red -> green -> blue
h = 0
s = 60
b = 60

def transition(bulb, h, s, b, interval):
    
    i = interval
    st = time.time()
    
    while True:
        try:
            
            bulb.transition_light_state(h, s, b, transition_period=int(i * 1000))
            break
            
        except socket.timeout:
            
            t = time.time()
            i = st + interval - t
            
            if i < 1: # less than one second left
                break
            
with ThreadPool(len(bulbs)) as p:
    while True:
        
        print('Transitioning lights to HSB(%d, %d, %d) over %d seconds' % (h, s, b, interval))
        
        for bulb in bulbs:
            p.apply_async(transition, (bulb, h, s, b, interval))
        
        h = (h + 120) % 360
        time.sleep(interval + 0.1)  # give it +0.1 to account for TCP latency (no jerky transitions)
