#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner, exc
from ev3dev2.sound import Sound
from ev3dev2.motor import MediumMotor, OUTPUT_A

myHubName = 'Pybricks'
idLEGO = 919

spkr = Sound()
m = MediumMotor(OUTPUT_A)
max_position=0
channel = 1
executing = False
msg_received = False


def listening_on_ch(ch):
   spkr.speak("Listening on channel " + str(ch) )


async def read_channel():
    global channel

    while True:
        if executing:
            pos = m.position
            if pos < max_position/3:
               current_channel = 1
            elif pos < 2*max_position/3:
                current_channel = 2
            else:
                current_channel = 3
            if channel != current_channel:
                channel = current_channel
                listening_on_ch(channel)
                print('Listening to ch:', channel)

        await asyncio.sleep(5)


async def main():
    stop_event = asyncio.Event()
    global msg_received
    global max_position
    global executing
    global msg_received

    def callback(device, advertising_data):
        if myHubName in str(advertising_data.local_name):
            if idLEGO in advertising_data.manufacturer_data:
                stop_event.set()
                payload = list(advertising_data.manufacturer_data[idLEGO])
                msg_channel = payload[0]
                if msg_channel == channel:
                    msg_sender = chr(payload[3])
                    msg_type = chr(payload[4])
                    if msg_type == 'S':
                        msg_speak = bytes(payload[5:]).decode()
                        print(msg_speak)
                        spkr.speak(msg_speak)
                        msg_received=True


    asyncio.create_task(read_channel())

    # initialize channel selector
    m.on(speed=-20)
    m.wait_until('stalled')
    m.stop()
    m.position=0
    await asyncio.sleep(1)

    m.on(speed=20)
    m.wait_until('stalled')
    m.stop()
    await asyncio.sleep(1)
    max_position = m.position

    m.on_to_position(20, 10)
    m.stop_action = 'coast'
    m.stop()

    listening_on_ch(channel)
    print('Listening on channel:', channel)
    executing = True

    msg_received=False
    while True:
        async with BleakScanner(callback, adapter='hci1') as scanner:
            await stop_event.wait()

        if msg_received:
            msg_received=False
            await asyncio.sleep(0.2)
            stop_event.clear()
        else:
            await asyncio.sleep(0.05)         #
            stop_event.clear()

if __name__ == "__main__":
    asyncio.run(main())
