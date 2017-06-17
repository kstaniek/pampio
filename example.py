"""
To test Ampio Client
"""

import asyncio
import logging
import multiprocessing

from pampio.ampioip import AmpioIPClient
from pampio.frame import CAN


HOST = '172.31.20.1'
PORT = 1234


logging.basicConfig(format='%(asctime)-15s %(levelname)8s: %(message)s', level=logging.INFO)


def mask_to_indices(mask):
    """Generate list of indices of bits set to one in the mask."""
    i = 1

    while mask > 0:
        if bool(mask & 0x1):
            yield i
        mask >>= 1
        i *= 2
    return


def frame_received(frame):
    print("Frame received: {}".format(":".join("{:02x}".format(c) for c in frame)))


def binary(mac, index, type, data):
    print("Event received: MAC={:04x} T={} I={} D={}".format(mac, type, index, data))


def temp(mac, index, type, data):
    print("Event received: MAC={:04x} Temperature T={} I={} D={}".format(mac, type, index, data))


def panel_led(mac, index, type, data):
    print("Event received: MAC={:04x} Panel Led T={} I={} D={}".format(mac, type, index, data))


def mled(mac, index, type, data):
    print("Event received: MAC={:04x} MLED T={} I={} D={}".format(mac, type, index, data))


def can_received(frame):
    can = CAN(raw=frame)
    # 1ecc SATEL
    #if can.mac != 0x1ecc:
    #    return

    if can.type == CAN.B_BINARY:
        print("Event received: MAC={:04x} Binary Inputs={:024b} Outputs:{:024b}".format(can.mac, can.inputs, can.outputs))
        print("CAN: {}".format(can))
    elif can.type == CAN.B_TEMP:
        print("Event received: MAC={:04x} Temperature: {}".format(can.mac, can.temp))
    elif can.type == CAN.B_TEMP_F_1_3:
        print("Event received: MAC={:04x} Temperature: 1-3: {}".format(can.mac, can.tempF))
    elif can.type == CAN.B_TEMP_F_4_6:
        print("Event received: MAC={:04x} Temperature: 4-6: {}".format(can.mac, can.tempF))
    elif can.type == CAN.B_BYTE_1_6:
        print("Event received: MAC={:04x} Byte: 1-6: {}".format(can.mac, can.bytes))
        print(can)
    elif can.type == CAN.B_BYTE_7_12:
        print("Event received: MAC={:04x} Byte: 7-12: {}".format(can.mac, can.bytes))
        print(can)
    elif can.type == CAN.B_BYTE_13_18:
        print("Event received: MAC={:04x} Byte: 13-18: {}".format(can.mac, can.bytes))
    elif can.type == CAN.B_TIME:
        print("Event received: MAC={:04x} Date/Time  {}-{}-{}, Weekday: {}, {}:{}".format(
            can.mac, can.year, can.month, can.day, can.weekday, can.hour, can.minute))
    elif can.type == CAN.B_FLAGS:
        print("Event received: MAC={:04x} Flags: {:048b}".format(can.mac, can.flags))
    elif can.type == CAN.B_LORA:
        print("Event received: MAC={:04x} LoRa {}".format(can.mac, can.bytes))
    elif can.type == CAN.B_MULTISENSE:
        value = ((can.d5 << 8) | can.d4) & 0xffff
        if can.d3 == 0:
            print("Event received: MAC={:04x} MULTI_SENSE Humidity {}%".format(can.mac, value))
        elif can.d3 == 1:
            print("Event received: MAC={:04x} MULTI_SENSE Pressure {}hPa".format(can.mac, value))
        else:
            print("Unknown")

        print(can)
    elif can.type == CAN.B_ZONE:
        print("Event received: MAC={:04x} ZONE: {:032b}".format(can.mac, can.zones))
        print("CAN: {}".format(can))
    elif CAN.B_ZONE1 <= can.type <= CAN.B_ZONE16:
        state = 'Active' if (can.d7 & 0x01) else 'Not Active'
        heating = 'Yes' if (can.d7 & 0x2) else 'No'
        mode = can.d7 & 0x70

        print("Event received: MAC={:04x} ZONE={} MEASURED={}C TARGET={}C ACTIVE={} HEATING={} DAY={}, MODE={}".format(
            can.mac, can.type - CAN.B_ZONE,
            can.zone_measured_temp,
            can.zone_target_temp,
            can.is_zone_active,
            can.is_zone_heating,
            can.is_zone_day,
            can.zone_mode
        ))
        print("CAN: {}".format(can))

    elif can.type == CAN.B_INTEGRA_1_48:
        print("Event received: MAC={:04x} INTEGRA INPUTS 1-48: {:048b}".format(can.mac, can.flags))
        print("Event received: MAC={:04x} INTEGRA INPUTS 1-48: {:08x}".format(can.mac, can.flags))
        for i in mask_to_indices(can.flags):
            print("{:0x} ".format(i), end='')
        print()

        print(can)
    elif can.type == CAN.B_INTEGRA_49_96:
        print("Event received: MAC={:04x} INTEGRA INPUTS 49-96: {:048b}".format(can.mac, can.flags))
        print("Event received: MAC={:04x} INTEGRA INPUTS 49-96: {:08x}".format(can.mac, can.flags))
        for i in mask_to_indices(can.flags):
            print("{:0x} ".format(i), end='')
        print()
        print(can)
    elif can.type == CAN.B_INTEGRA_97_128:
        print("Event received: MAC={:04x} INTEGRA INPUTS 97-128: {:048b}".format(can.mac, can.flags))
        print(can)
    else:
        print("Unknown Frame: {}".format(can))

    print("-" * 20)




@asyncio.coroutine
def feed_messages(protocol):
    """ An example function that sends the same message repeatedly. """

    value = True
    analog = 0

    while True:
        #yield from protocol.binary_output(0x0001, 15, value)
        #yield from protocol.byte_output(0x196a, 2, analog)
        #yield from protocol.byte_output(0x196a, 2, analog)

        #yield from protocol.binary_output(0x0002, 1, value)

        yield from asyncio.sleep(5)
        value = not value
        #value = 255 if value == 0 else 255
        #analog = analog + 10 if analog < 250 else 0
        analog = 1 if analog == 0 else 0

# MAC: 0x0000111f MDOT-9
# MAC: 0x00000001 MSERV-3s
# MAC: 0x00001305 MLED-1S

def client():

    loop = asyncio.get_event_loop()
    amp = AmpioIPClient.connect(loop, HOST, PORT, username='admin', password='ampio')

    amp.register_listener(can_received)

    # # LCD Panel Touch
    # amp.register_listener(0x111f, 0, 'input', binary)
    # amp.register_listener(0x111f, 1, 'input', binary)
    # amp.register_listener(0x111f, 4, 'input', binary)
    #
    # # LCD Panel LEd
    # amp.register_listener(0x111f, 0, 'output', panel_led)
    # amp.register_listener(0x111f, 8, 'output', panel_led)
    #
    # # Server temp
    # amp.register_listener(0x0001, 1, 'tempF', temp)
    #
    # # Server output
    # amp.register_listener(0x0001, 0, 'output', binary)
    # amp.register_listener(0x0001, 1, 'output', binary)
    #
    #
    # # MLED binary
    # amp.register_listener(0x1305, 0, 'output', binary)
    # amp.register_listener(0x1305, 0, 'output', binary)
    #
    # # MLED
    # amp.register_listener(0x1305, 1, 'byte', mled)
    # amp.register_listener(0x1305, 2, 'byte', mled)

    # asyncio.async(feed_messages(amp))
    asyncio.ensure_future(feed_messages(amp), loop=loop)

    loop.run_forever()
    loop.close()


def main():
    client_process = multiprocessing.Process(target=client, name='client')
    client_process.start()
    input("Press Enter to continue...\n")

    try:
        client_process.join(1)
    finally:
        client_process.terminate()
        client_process.join()


if __name__ == '__main__':
    main()

