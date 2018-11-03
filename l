#!/usr/bin/env python3

import colorsys
import string
import sys

# SET YOUR NUMBER OF KNOWN BULBS HERE
known_bulbs = 4

from argparse import ArgumentParser, ArgumentTypeError
from lb130 import discover

def hex_to_hsb(hexcode):
    r, g, b = int(hexcode[:2], 16), int(hexcode[2:4], 16), int(hexcode[4:6], 16)
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

def hsb_to_hex(hsb):
    r, g, b = map(lambda c: int(c * 255), colorsys.hsv_to_rgb(*hsb))
    return '%02x%02x%02x' % (r, g, b)

def interval_checker(min_val, max_val, name):
    def func(value):
        
        x = int(value)
        
        if min_val <= x <= max_val:
            return x
        else:
            raise ArgumentTypeError(name + ' must be in the interval (' + str(min_val) + '-' + str(max_val) + ')')
    
    return func

def hex_checker(value):
    # check if length is 6 and all chars in string are valid hex chars
    if len(value) == 6 and all(ch in string.hexdigits for ch in value):
        return value
    else:
        raise ArgumentTypeError('Invalid hex triplet specified for color argument')

parser = ArgumentParser(add_help=False)

meg = parser.add_mutually_exclusive_group(required=False)
meg.add_argument('-on', action='store_true', dest='on_off', help='Turn bulbs on', default=None)
meg.add_argument('-off', action='store_false', dest='on_off', help='Turn bulbs off', default=None)

parser.add_argument('-t', action='store', dest='color_temp', type=interval_checker(2500, 9000, 'Color temperature'),
                    default=None,
                    help='Set the white light temperature (2500-9000)')
parser.add_argument('-h', action='store', dest='hue', type=interval_checker(0, 360, 'Hue'), default=None,
                    help='Set the hue (0-360)')
parser.add_argument('-s', action='store', dest='saturation', type=interval_checker(0, 100, 'Saturation'), default=None,
                    help='Set the saturation (0-100)')
parser.add_argument('-b', action='store', dest='brightness', type=interval_checker(0, 100, 'Brightness'), default=None,
                    help='Set the brightness/value (0-100)')

parser.add_argument('-c', action='store', dest='color', help='Set the color to a hex triplet', type=hex_checker,
                    default=None)
parser.add_argument('--help', action='store_true')

args = parser.parse_args()

if args.help:
    parser.print_help()
    sys.exit()

if args.color:
    
    if args.hue or args.saturation or args.brightness or args.color_temp:
        parser.error('Color option cannot be used with hue, saturation, brightness or color_temp')
    
    (h, s, b) = hex_to_hsb(args.color)
    args.hue = int(360 * h)
    args.saturation = int(100 * s)
    args.brightness = int(100 * b)
    
    del args.color

if (args.hue or args.saturation) and args.color_temp:
    parser.error('Hue or saturation cannot be used with color_temp')

# if the bulb already has color_temp set, it won't show the new color until color_temp=0 is passed
if args.hue or args.saturation:
    args.color_temp = 0

d = {arg: getattr(args, arg) for arg in vars(args) if arg != 'help' and getattr(args, arg) is not None}

discovered = set()

def callback(bulb):
    if bulb in discovered:
        return
    
    if not d:
        
        ls = bulb.get_light_state()
        
        if ls['color_temp'] == 0:
            
            (h, s, b) = (ls['hue'], ls['saturation'], ls['brightness'])
            hexcode = hsb_to_hex((h / 360, s / 100, b / 100))
            print('Bulb', bulb.sysinfo['deviceId'], 'at', bulb.protocol.ip, 'reporting color', '#' + hexcode, (h, s, b),
                  '(OFF)' if ls['on_off'] == 0 else '')
        
        else:
            
            print('Bulb', bulb.sysinfo['deviceId'], 'at', bulb.protocol.ip, 'reporting white with temperature',
                  str(ls['color_temp']) + 'K', 'and brightness', ls['brightness'])
    
    else:
        
        bulb.transition_light_state(**d)
        print('Updated bulb', bulb.sysinfo['deviceId'], 'at', bulb.protocol.ip)
    
    discovered.add(bulb)
    
    if len(discovered) == known_bulbs:
        sys.exit()

discover(callback, 10, 0.1)
print('Timed out, only', len(discovered), 'bulbs were discovered')
