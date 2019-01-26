A Python 3 API for interfacing with TP-Link LB130 smart bulbs. I also included a command line script called "l", which can be used to control all LB130 bulbs on your home network.

Most of the reverse engineering was adapted from [Reverse Engineering the TP-Link HS110](https://www.softscheck.com/en/reverse-engineering-tp-link-hs110/). The LB130 also has support for scheduling and anti-burglary measures, but I haven't implemented those features in this library. I _might_ some other time

## Overview

The library is designed to support several kinds of networking protocols, which are represented as instances of the TPLinkProtocol class. An instance of a LB130 controller uses a given protocol to communicate with one or more physical LB130 bulbs.

### TPLinkProtocol

Abstract class representing a method of communicating with LB130 bulbs. Must implement the send function, and perform setup and cleanup in \_\_enter\_\_ and \_\_exit\_\_ functions.

Implemented and tested protocols accepted by the LB130 are:

* TCP           - A one-to-one TCP connection protocol between the client and an LB130 bulb. Will also fetch the bulb's response with every send.
* UDP           - A one-to-one UDP protocol between the client and an LB130 bulb.
* UDP Broadcast - A one-to-many UDP broadcast on ip 255.255.255.255.
* Cloud         - A one-to-one connection using the TP-Link cloud API with token-based web requests. Tokens can be acquired given TP-Link login credentials.

### TPLinkDevice

Base class for all TP-Link devices.

### CloudTPLinkDevice

Base class for cloud-enabled TP-Link devices.

Supports registering the device with a TP-Link account and updating the device.

### LB130

Controller using a TPLinkProtocol to communicate with one or more LB130 bulbs. Also has discover_local and discover_cloud functions to scan for LB130 bulbs on the local network or a registered cloud account.

### encryption

Houses the four functions used by the LB130 to "encrypt" communication between the bulb and the user using an autokey XOR cipher. Discovered by the people from softScheck, though the LB130 expects headed messages for TCP connections, where the length of the packet is encoded into the 4-byte header in big endian, whereas the HS110 just requires any 4-byte header.

Made in my spare time for my own home setup and only tested on Manjaro Linux with Python 3.7 :)