#!/usr/bin/env python3.11

# based on my interpretation of Pybricks protocol
# https://github.com/pybricks/technical-info/blob/master/pybricks-ble-broadcast-observe.md

from ev3dev2.sound import Sound
from os import system
import struct
from time import sleep

MANUFACTURER_DATA = 'FF'
COMPANY_ID = '97 03'              # LEGO CID
SINGLE_OBJECT = '00'

hcidev = "hci1"                   # hci0 or hci1, needs to be properly checked at start


def get_representation(value):
    # returns length and hexadecimal representation of value

    # Pybricks protocol supports aonly these types:
    # bool, int (signed, 8/16/32 bits), float (32 bits single precision), str and bytes
    # It also support a tupple with any comnbination of these types
    # Maximum payload is 24 bytes so it is possible to send a 24-char string
    # but not 2 12-char strings because of the encoding overhead

    if isinstance(value, bool):
        # boolean
        if value == True:
            return(1, "20")
        else:
            return(1, "40")
    elif isinstance(value, int):
        if  -128 <= value <= 127:
            # 8-bit signed int
            buff = bytearray(1)
            struct.pack_into('b', buff, 0, value)
            return(2, f'61 {buff[0]:02x}')
        elif -32768 <= value <= 32767:
            # 16-bit signed int
            buff = bytearray(2)
            struct.pack_into('h', buff, 0, value)
            return(3, f'62 {buff[0]:02x} {buff[1]:02x}')
        else:
            # 32-bit signed int
            buff = bytearray(4)
            struct.pack_into('i', buff, 0, value)
            return(5, f'64 {buff[0]:02x} {buff[1]:02x} {buff[2]:02x} {buff[3]:02x}')
    elif isinstance(value, str):
        # string
        hexa = ' '.join(hex(ord(x))[2:] for x in value)
        return(len(value)+1, f'{(160 + len(value)):02x}' + " " + hexa)
    elif isinstance(value, float):
        # float
        buff = bytearray(4)
        struct.pack_into('f', buff, 0, value)
        return(5, f'84 {buff[0]:02x} {buff[1]:02x} {buff[2]:02x} {buff[3]:02x}')
    elif isinstance(value, bytes):
        # bytes
        value_hex = value.hex()
        hexa = ' '.join( value_hex[i:i+2] for i in range(0, len(value_hex), 2) )
        return(len(value)+1, f'{(192 + len(value)):02x}' + " " + hexa)


def prepare_ble_advertise():
    # prepares BLE for advertisement (broadcast)
    system("hcitool -i hci1 cmd 0x08 0x0006 35 00 35 00 00 00 00 00 00 00 00 00 00 07 02 >/dev/null 2>&1")


def define_ble_advertise(channel, value):

    payload  = f'{MANUFACTURER_DATA} {COMPANY_ID} {channel:02x}'
    size = 4

    if isinstance(value, tuple):
        # tuple of values
        for v in value:
            sz, rep_value = get_representation(v)
            size += sz
            payload = f'{payload} {rep_value}'
    else:
        # SINGLE_OBJECT
        sz, rep_value = get_representation(value)
        size += sz + 1
        payload = f'{payload} {SINGLE_OBJECT} {rep_value}'


    first_byte = f'{size+1:02x}'    # required by hcitool
    second_byte = f'{(size):02x}'   # required py Pybricks
    tail = '00 '*(30-size)          # required by hcitool

    system("hcitool -i "
        + hcidev
        + " cmd 0x08 0x0008 "
        + first_byte + " "
        + second_byte +" "
        + payload + " "
        + tail
        + " >/dev/null 2>&1"      # to prevent output
    )


def initiate_ble_advertise():
    system("hcitool -i " + hcidev + " cmd 0x08 0x000a 01 >/dev/null 2>&1")
#    system("btmgmt --index 1 advertising on >/dev/null 2>&1")


def stop_ble_advertise():
    system("hcitool -i " + hcidev + " cmd 0x08 0x000a 00 >/dev/null 2>&1")
#    system("btmgmt --index 1 advertising off >/dev/null 2>&1")


def pybricks_broadcast(channel, value):
    prepare_ble_advertise()
    define_ble_advertise(channel, value)
    initiate_ble_advertise()


def set_complete_name(name):
    # adds a Scan Response instance with "Complete Local Name" = name
    # looks good on a Scanner App but it seems to affect
    # stop_ble_advertise() to work so I'm not using

    first = f'{ (len(name) + 1) :02x}'
    payload = ''.join(hex(ord(x))[2:] for x in name)
    system("btmgmt --index 1 add-adv -s "
         + first
         + "09"
         + payload
         + " 1"
         + " >/dev/null 2>&1"      # to prevent output
    )


def unset_complete_name():
    # removes Advertising instance
    # WARNING: next time we add an instance the BT address will change
    system("btmgmt --index 1 rm-adv 1 >/dev/null 2>&1")


def main():
    stop_ble_advertise()          # just in case last execution left advertisement running
    sleep(1.0)
#    set_complete_name('PybricksEV3')

    print("Running...")
    try:
        count = 0
        while True:

#            pybricks_broadcast(1, True)
#            pybricks_broadcast(1, -30)
#            pybricks_broadcast(1, -3000)
#            pybricks_broadcast(1, -38000)
#            pybricks_broadcast(1, 'This is a 24-chr string!')
#            pybricks_broadcast(1, 3.14)
#            pybricks_broadcast(1, b'\xf0\xf1\xf2\xf3\xf4\xf5\xf6')
#            pybricks_broadcast(1, (True, -20, 250, 100000, 3.14, 'A', b'\xf0\xf1') )

            pybricks_broadcast(1, str(count))
            stop_ble_advertise()
            sleep(0.1)
            count +=1

    except KeyboardInterrupt:
        stop_ble_advertise()
    finally:
        print("End.")


if __name__ == "__main__":
    main()
