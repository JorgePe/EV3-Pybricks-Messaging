# EV3-Pybricks-Messaging
My attempts to use LEGO MINDSORMS EV3 to communicate with Pybricks messaging protocol

# WARNING: this is still very incomplete, as I am still reviewing my notes

## Intro

The [Pybricks](https://pybricks.com/) project implemented a [connection-less protocol](https://github.com/pybricks/technical-info/blob/master/pybricks-ble-broadcast-observe.md)
that allows exchanging short messages between LEGO hubs running the Pybricks firmware.

Other devices can also "talk" this protocol - Raspberry Pi, Raspberry Pi Pico, some
Arduino-like boards like some Adafruit or ESP32. [todo: add links]

I've ben trying to use MINDSTORMS EV3.

The easier way: get an external device and use it as a gateway. A Raspberry Pi 2 Zero,
for example - I've used it with Python and Bleak and connected it to the EV3 through USB
using a HID library and the EV3 receives Pybricks messages as if they were type on 
a USB keyboard. [will demo/document it later]

The stubborn way: use just the EV3 and a USB BT dongle that supports BLE. It's possible...
 but seriously, it's also crazy!

## Limitations

[ev3dev](https://www.ev3dev.org/) is based on a now obsolet Debian version for a CPU
architecture (armel) no longer supported, so keeping up with modern python libraries is
at least very difficult if not impossible. And some of the first python BLE libraries
I've used (mostly with SBricks and WeDo 2.0) seem to be no longer mantained.

So I tried several different approaches until I got something reasonably useful. And even
so, I don't have a unified solution - I am now using system calls for broadcasting and 
a python library (Bleak) for observing.

But at least it is possible.


## Achievements

- broadcasting (i.e. sending) is working fine
- observing (i.e receiving) is working - but not yet as I desire

Broadcasting is somewhat easy with just some system calls to linux Bluez commands.

It will probably work much better with higher level mechanisms that use DBus to interface
with the Bluez API - but I don't know how to do it and didn't find any proper python
library.

Observing is more demanding. It might be possible also with system calls but I could not
achieve good results for more than just a few seconds (using python 'pexpect' to interact
with Bluez 'bluetootctl').

I also tried DBus directly but I do not understand enough of it so I had to try python
with some Dbus library. I found several examples with pydbus and got some results but
also for just a short duration.

I am now using Bleak (and dbus-fast) with much better results. More about that later.


## Some boring technical background

### HCI

Host Controller Interface (HCI) is a standard for Bluetooth (BT) communication.

The MINDSTORMS EV3 already has an internal HCI device but unfortunately it's very
old and only supports BT 2.x so it does not support the Bluetooth Low Energy (BLE)
features that were introduced with BT 4.0 version.

When using ev3dev linux, this HCI device is identified as 'hci0'.

We need a USB BT 4.0 or higher dongle that supports BLE. ev3dev will recognize
most of the dongles available in the market but for this purpose the best option is
to use one with a Cambridge Silicon Radio (CSR) chipset.

If ev3dev supports your dongle it will show up in dmesg:

```
robot@ev3dev:~$ sudo dmesg
(...)
[117423.073627] usb 1-1.3: New USB device found, idVendor=0a12, idProduct=0001, bcdDevice=88.91
[117423.073680] usb 1-1.3: New USB device strings: Mfr=0, Product=2, SerialNumber=0
[117423.073708] usb 1-1.3: Product: CSR8510 A10
```

It will also show up in 'hciconfig':

```
hci1:	Type: Primary  Bus: USB
	BD Address: 00:1A:7D:DA:71:13  ACL MTU: 310:10  SCO MTU: 64:8
	UP RUNNING 
	RX bytes:770891 acl:0 sco:0 events:128176 errors:0
	TX bytes:2022153 acl:0 sco:0 commands:128176 errors:0
	Features: 0xff 0xff 0x8f 0xfe 0xdb 0xff 0x5b 0x87
	Packet type: DM1 DM3 DM5 DH1 DH3 DH5 HV1 HV2 HV3 
	Link policy: RSWITCH HOLD SNIFF PARK 
	Link mode: SLAVE ACCEPT 
	Name: ''
	Class: 0x000100
	Service Classes: Unspecified
	Device Class: Computer, Uncategorized
	HCI Version: 4.0 (0x6)  Revision: 0x22bb
	LMP Version: 4.0 (0x6)  Subversion: 0x22bb
	Manufacturer: Cambridge Silicon Radio (10)

hci0:	Type: Primary  Bus: UART
	BD Address: 00:16:53:52:BD:66  ACL MTU: 1021:4  SCO MTU: 180:4
	DOWN 
	RX bytes:4082 acl:0 sco:0 events:255 errors:0
	TX bytes:23417 acl:0 sco:0 commands:255 errors:0
	Features: 0xff 0xfe 0x2d 0xfe 0x9b 0xff 0x79 0x87
	Packet type: DM1 DM3 DM5 DH1 DH3 DH5 HV1 HV2 HV3 
	Link policy: RSWITCH HOLD SNIFF 
	Link mode: SLAVE ACCEPT
```

In the past, linux sometimes switched the 'hci' device order at startup and
the USB device could be 'hci0' instead of 'hci1'. I am not seeing that happen
with my current ev3dev versions but I am not yet 100% sure that we can
always assume 'hci1' for the USB dongle so it's better to check (if
using 'hciconfig -a', the internal hci device will always be the one
with 'Bus: UART' and the external hci device the one with 'Bus: USB')


### HCI commands

The HCI standard implements several commands. Those are grouped in Opcode Groups
and each Opcode Group has a set of Opcode Commands. So a command have two parts or
fields: a OGF and a OCF.

Pybricks [protocol definition](https://github.com/pybricks/technical-info/blob/master/pybricks-ble-broadcast-observe.md)
states a few conditions:

    Advertisements should be sent using a 100ms interval.
    Advertisements should be sent on all 3 radio channels.
    Advertisements should be sent using advertising data type of ADV_NONCONN_IND (undirected, not scannable, not connectable).
    Payload must contain only one advertisement data structure with type of Manufacturer Specific Data (0xFF).
    Manufacturer Specific Data must use LEGO company identifier (0x0397).

All the advertisement commands needed to ensure this are in the
OGF 8 ("LE Only Commands"):
- OCF 06 for LE Set Advertising Parameters
- OCF 08 for LE Set Advertising Data
- OCF 10 for LE Set Advertise Enable

So broadcasting (i.e. advertising) is possible with just a small set
of HCI commands. And the best part is this commands being essentially
the same needed to implement a BLE beacon (Pybricks protocol is indeed
just a particular implementation of a beacon) and there are several
examples of doing it with a Raspberry Pi or a linux laptop.


### hcitool

ev3dev linux has several Bluez tools, I am using 'hcitool' to issue HCI commands:

```
robot@ev3dev:~$ hcitool
hcitool - HCI Tool ver 5.50
Usage:
	hcitool [options] <command> [command parameters]
```

```
robot@ev3dev:~$ hcitool -i hci1 cmd
cmd: too few arguments (minimal: 2)
Usage:
	cmd <ogf> <ocf> [parameters]
```

it's an old version (my Ubuntu with Bluez 5.72 has a 5.72 version and there
are several later versions). Although it is possible to build and install
Bluez 5.72 on ev3dev it will not install hcitool unless you chose to also
build the deprecated tools.

But since after hcitool has been deprecated few (if any) changes have been
made and I didn't find anything suggesting I would benefit from a recent
version I am still using this old one (5.50).

hcitool requires root permission to be used. To avoid using 'sudo' and also
allow using it in my scripts I removed this need:

```
sudo setcap cap_net_raw+ep /usr/bin/hcitool
```

## Broadcasting

### Set LE Advertising Parameters

    Advertisements should be sent using a 100ms interval.
    Advertisements should be sent on all 3 radio channels.
    Advertisements should be sent using advertising data type of ADV_NONCONN_IND (undirected, not scannable, not connectable).

To set this 3 parameters we use the HCI command with OGF 0x08 and OCF 0x0006:

```
hcitool -i hci1 cmd 0x08 0x0006 A0 00 A0 00 03 00 00 00 00 00 00 00 00 07 02
```

The first four bytes set the Min and Max Advertisement Interval as 140
(A0 00 = 0x00A0 = 140) unities of time. In Bluez each unit of time is 0.625
ms so we need 140 units to achieve 100 ms.

The fifth byte ('03') sets a group of flags required for ADV_NONCONN_IND
The 14th byte ('07') selects the 3 radio channels used by Bluetooth with
advertisements (there are more channels, for other purposes)

Actually I am using a slightly different command to relicate the behavior I
see when using Nordic nRF Connect tool on my Android phone to scan Pybricks
hubs:

```
hcitool -i hci1 cmd 0x08 0x0006 35 00 35 00 00 00 00 00 00 00 00 00 00 07 02
```
(33 ms instead of 100 ms and ADV_IND instead of ADV_NONCONN_IND)

But both commands seem to work fine.


### Set LE Advertising Data

For the actual payload of each advertisement we use the HCI command with 
OGF 0x08 and OCF 0x0008:

```
hcitool -i hci1 cmd 0x08 0x0008 payload
```

As an example of a payload, if we want so send just "True' on channel 1

i.e. the same as this Pybricks command:

```
hub.ble.broadcast(True)
```

the required 32-byte payload for the HCI "LE Set Advertising Data" will be:

"08 06 FF 97 03 01 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"

The firt byte (08) defines the real length of the advertisement data (8 bytes, all the rest is
just padding zeros).

From the second byte onward we follow Pybricks definition:

06 FF 97 03 01 00 20

The first byte is also a length: 6 bytes will follow
The second byte indicates we will be advertising "Manufacturer Data" (one of the
several types of BLE Advertisements)
The third and fourth bytes are the Company Identifier (0x0397 = 919 is from LEGO)
The fifth byte is the channel id (01)
The sixth byte means 'SINGLE_OBJECT'
The seventh byte means the object is of type 'Bool' and it is 'True'

The payload must have a 32-byte length to will need to add some leading zeros.

So the complete hcitool command:

```
hitool -i hci1 cmd 0x08 0x0008 08 06 FF 97 03 01 00 20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```


### Set LE Advertise Enable

And finally to initiate the advertisement we issue the command OGF 0x08 | OCF 0x0A

```
hcitool -i hci1 cmd 0x08 0x000a 01
```

From now on the MINDSTORMS EV3 will be advertising Manufacturer Data with the LEGO
Company Identifier and the Pybricks message every 100 ms until we terminate
the advertisement with another OCF 0x0A command:

```
hcitool -i hci1 cmd 0x08 0x000a 00
```

When my MINDSTORMS EV3 is advertising like this and a LEGO Technic Hub is also
advertising 'True' I get this with Nordic nRF Connect App:

<img src="https://github.com/JorgePe/EV3-Pybricks-Messaging/blob/main/brodcast_ch1_True.jpeg" width=250>

'PybricksGP4' is the name I chose when I installed Pybricks firmware on the Technic Hub.
'PybricksEV' is the 'Shortened Local Name' I gave to my EV3 hci1 device - you can do that with 

```
sudo btmgmt --index 1
[hci1] name PybricksEV3
[hci1] exit
```

or with

```
hcitool -i hci1 cmd 0x03 0x0013 50 79 62 72 69 63 6B 73 45 56 33
```

but it only works after restarting bluetooth service or restarting
hci1 with

```
hciconfig -a hci1 down
hciconfig -a hci1 up
```

'Shortened Local Name' is not the same as 'Complete Local Name' but the only way
I found to advertise 'Complete Local Name' is also issuing a 0x08 0x0008 command:

```
hcitool -i hci1 cmd 0x08 0x0008 0d 0c 09 50 79 62 72 69 63 6b 73 45 56 33 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

but this replaces the 'Manufacturer Data' command so no Pybricks message will be
advertised.

To advertise both types simultaneously I need to mix both advertisements in just one:

```
hcitool -i hci1 cmd 0x08 0x0008 14 06 FF 97 03 01 00 20 0c 09 50 79 62 72 69 63 6b 73 45 56 33 00 00 00 00 00 00 00 00 00 00 00
```

- '14' is the total payload size (20 bytes)

- '6 FF 97 03 01 00 20' is the same Manufacturer Data advertisement ('FF' is the
Manufacturer Data type)

- '0c 09 50 79 62 72 69 63 6b 73 45 56 33' is the 'Complete Local Name' advertisement
('09' is the type)

but this leaves just 11 bytes more. Not a problem for most SINGLE_OBJECT data types
(Long Int or Float use just 4 bytes) but string-type or bytes-type values will need
to be kept shorter than 12 bytes. Not much for a string value.

I tested with Pybricks IDE and the maximum string size allowed to be broadcasted was 24.
With a 25-char string I got:

```
ValueError: payload limited to 26 bytes
```

So Pybricks is using a better way to advertise 'Complete Local Name' and
'Manufacturer Data'.

Following a suggestion I found, I tried advertising one then the other but Nordic
nRF Connect keeps showing one then the other - not mixing both in one.

Perhaps the STM microcontroller allows several simultaneous advertisements?

Nope. Much simpler than that: 'Complete Local Name' is not being advertised
at all. It is defined as a 'Scan Response'.

Don't know yet how to do it with 'hcitool' but I can do it with 'btmgmt', another
tool from Bluez (also deprecated, also using version 5.50 with my EV3)

```
robot@ev3dev:~$ sudo btmgmt --index 1 add-adv -s 0c095079627269636b73455633 1
Instance added: 1
```

Since I don't need to advertise 'Complete Local Name', I have the whole 24-bytes
available for Pybricks variables, like a 24-chr string:

<img src="https://github.com/JorgePe/EV3-Pybricks-Messaging/blob/main/brodcast_ch1_24c_string.jpeg" width=250>

After finding the EV3, the scanner (in this case the Nordic nRF Connect App) asks 
EV3 for more details and that's when it gets the 'Complete Local Name'

0c 09 5079627269636b73455633

- '0C' is the total length (12 bytes)
- '09' means 'Complete Local Name'
- '5079627269636b73455633' = "PybricksEV3"

We can remove the requirement for sudo permissions on 'btmgmt' with

```
sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/bin/btmgmt
```

### A whole implementation


This [script](https://github.com/JorgePe/EV3-Pybricks-Messaging/blob/main/broadcaster.py)
makes use of hcitool to broadcast BLE messages in Pybricks format.

It fully implements the protocol so it can use single values or tuples with any combination
of all the supported types (as long as the total payload is lower than 25 bytes).

When setting a Scan Response with the Complete Local Name I am having problems and cannot
stop advertisements with hcitool. Removing the Scan Response fixes it but if I set again
a Scan Response it will create a new BT address. So if using a Scanner App like Nordic
nRF Connect there will appear several instances of the device, one for each address.

Until I found a proper way to deal with this I will use Complete Local Name response
only when I need to some nice screenshots :D

Please note that the script doesn't validate the lenght of string or bytes values
and also doesn't check the final length of a combination of several values (for example
while a 24-char string is supported, a tupple of two 12-char strings will break because
of the overhead of representing two values instead of a SINGLE_OBJECT)

An example of the script above with my EV3 controlling a Pybricks [StarterBot](https://pybricks.com/learn/building-a-robot/)
through hand claps and whistles (thanks to an old MINDSTORMS NXT sound sensor - 3 generations
in the same video :D )

[![Pybricks StarterBot remote controlled with hand claps/whistles](http://img.youtube.com/vi/qCcJQUrwS6E/0.jpg)](https://youtu.be/qCcJQUrwS6E "Pybricks StarterBot remote controlled with hand claps/whistles")

## Observing (i.e. receiving)

This is almost impossible with just system calls to linux bluez commands. The best I could
do was using pexpect to iteract with bluetoothctl but just for a few seconds... Bluez generates
too much messages to handle.

It is also possible acessing Bluez through DBus. I got some results with pydbus but usually just
for some minutes. Bluez generates too much messages to handle and I think I also find some
odd Bluez/DBus/pydbus/Glib/Gobject bug.

I decided to try Bleak. Bleak also uses dbus to access Bluez but is uses other library
(dbus-fast, that "aims to be a performant fully featured high level library").

To my suprise, I could install it with python 3.7. Not the most recent version but it worked...
for a few seconds, sometimes minutes.

Then I found this [ev3dev discussion](https://github.com/ev3dev/ev3dev/issues/1635) about a
custom ev3dev image with a more recent kernel and a more recent python version (3.11)... and
achieved much better results. I could even compile and install a much newer Bluez version
(5.72 instead of 5.50), not yet 100% sure but I think it also helped.

This video shows 3 Technic hubs broadcasting on 3 different channels and the EV3 observing
on each channel:

[![MINDSTORMS EV3 observing Pybricks messages](http://img.youtube.com/vi/TA4MAE_XB7M/0.jpg)](http://www.youtube.com/watch?v=TA4MAE_XB7M "MINDSTORMS EV3 observing Pybricks messages")

The EV3 python script is available [here](https://github.com/JorgePe/EV3-Pybricks-Messaging/blob/main/test-bleak-v4.py).

not yet perfect: I need to find a way of clearing cached messages when switching channels -
you can see in the video, the first time I return to channel 1, that 5 previous messages were
read instead of discarded. The second time I return to channel 1 there were no messages
in cache because I didn't wait so much on the other channels.


