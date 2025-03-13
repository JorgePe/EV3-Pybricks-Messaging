# EV3-Pybricks-Messaging
My attempts to use LEGO MINDSORMS EV3 to communicate with Pybricks messaging protocol


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

This is somewhat easy with just some system calls to linux bluez commands [will document it
later].

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
you can see in the video, when returning to channel 1, that some previous messages were
read instead of discarded.


