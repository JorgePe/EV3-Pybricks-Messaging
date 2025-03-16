# EV3-Pybricks-Messaging
My attempts to use LEGO MINDSORMS EV3 to communicate with Pybricks messaging protocol

# WARNING: this is still very incomplete, as I an still reviewing my notes

## Intro

The Pybricks project implemented a [connection-less protocol](https://github.com/pybricks/technical-info/blob/master/pybricks-ble-broadcast-observe.md)
that allows to exchange short messages between LEGO hubs running the Pybricks firmware.
Other devices can also "talk" this protocol - Raspberry Pi, Raspberry Pi Pico, some
Arduino-like boards like some Adafruit or ESP32.

I've ben trying to use MINDSTORMS EV3.

The easier way: get an external device and use it as a gateway. A Raspberry Pi 2 Zero,
for example - I've used it with Python and Bleak and connected it to the EV3 through USB
using a HID library and the EV3 receives Pybricks messages as if they were type on 
a USB keyboard. [will demo/document it later]

The stubborn way: use just the EV3 and a USB BT dongle that supports BLE. It's possible...
 but seriously, it's also crazy!

ev3dev is based on a now obsolet Debian version for a CPU archtecture (armel) no longer
supported, so keeping up with modern python libraries is at least verry difficult if
not impossible. And some of the first python BLE libraries I've used (mostly with SBricks
and WeDo 2.0) seem to be no longer mantained so I had to try a lot of until getting
something reasonably useful.

## Broadcasting (i.e. sending)

This is somewhat easy with just some system calls to linux bluez commands.
It will probably work much better with higher level mechanisms that use Dbus to interface
with the Bluez API - but I don't know how to do it and didn't find any proper python
library.

### HCI

Host Controller Interface (HCI) is a standard for Bluetooth (BT) communication.

The MINDSTORMS EV3 already has an internal HCI device but unfortunately it's very
old and only supports BT 2.x so it does not support the Bluetooth Low Energy (BLE)
features that were introduced with BT 4.0 version.

When using ev3dev linux, this HCI device is identified as 'hci0'.

We need a USB BT 4.0 or higher dongle that suuports BLE. ev3dev will recognize
most of the dongles available in the market but for this purpose best option is
using one with a Cambridge Silicon Radio (CSR) chipset.

If ev3dev supports your dongle it will show in dmesg:

It will also show in 'hciconfig':

In the past, linux sometimes switched the 'hci' order at startup so sometimes the
USB device would be 'hci1' and sometimes 'hci0'. I am not seeing that happen
with my current ev3dev versions but I am not yet 100% sure that we can
always assume 'hci1' for the USB dongle so it's better to check.

### HCI commands

The HCI standard implements several commands. These are grouped in Opcode Groups
and each Opcode Group has a set of Opcode Commands. So a command have two parts or
fields: a OGF and a OCF.

Pybricks protocol states:

    Advertisements should be sent using a 100ms interval.
    Advertisements should be sent on all 3 radio channels.
    Advertisements should be sent using advertising data type of ADV_NONCONN_IND (undirected, not scannable, not connectable).
    Payload must contain only one advertisement data structure with type of Manufacturer Specific Data (0xFF).
    Manufacturer Specific Data must use LEGO company identifier (0x0397).

All the advertisement commands needed are from the OGF 8 ("LE Only Commands"):
- OCF 06 for LE Set Advertising Parameters
- OCF 08 for LE Set Advertising Data
- OCF 10 for LE Set Advertise Enable


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


