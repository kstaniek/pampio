"""This is CAN/Ampio frame implementation."""

import struct
import hashlib


class FixedField:
    """This is a FixedField descriptor implementation."""

    def __init__(self, fmt_char, offset):
        """Init the descriptor."""
        self.fmt_char = fmt_char
        self.offset = offset

    def __get__(self, obj, objtype):
        """Get value."""
        value = struct.unpack_from(self.fmt_char, obj.frame, self.offset)
        return value[0]

    def __set__(self, obj, val):
        """Set value."""
        struct.pack_into(self.fmt_char, obj.frame, self.offset, val)


class VariableByteField:
    """This is a VariableByteField descriptor implementation."""

    def __init__(self, offset, callback):
        """Init the descriptor."""
        self.offset = offset
        self.callback = callback

    def __set__(self, obj, val):
        """Set value."""
        # get the end index from instance attribute
        try:
            end = obj.__end
        except AttributeError:
            # id not exists store the offset (zero length)
            obj.__end = end = self.offset

        # delete the previous data
        del obj.frame[self.offset:end]

        if isinstance(val, str):
            byte_value = bytearray(val, encoding='ascii')
        elif isinstance(val, FrameClass):
            byte_value = val.frame
        else:
            byte_value = bytearray(val)

        # store the new field end index into instance attribute
        obj.__end = self.offset + len(byte_value)
        # insert new value into instance frame starting from offset
        obj.frame[:self.offset] += byte_value
        self._callback(obj)

    def __get__(self, obj, objtype):
        """Get value."""
        return obj.frame[self.offset:obj.__end]

    def _callback(self, obj):
        """Call back."""
        callback = getattr(obj, self.callback)
        if hasattr(callback, '__call__'):
            callback()


class FrameClass:
    """This is a base class for frames."""

    # Broadcast types (d1)
    B_TEMP = 0x05
    B_TEMP_F_1_3 = 0x06
    B_TEMP_F_4_6 = 0x07
    B_BYTE_1_6 = 0x0c
    B_BYTE_7_12 = 0x0d
    B_BYTE_13_18 = 0x0e
    B_BINARY = 0x0f
    B_TIME = 0x10
    B_NTP = 0x11
    B_LORA = 0x2a
    B_FLAGS = 0x80
    B_ZONE = 0xc8
    B_ZONE1 = 0xc9
    B_ZONE2 = 0xca
    B_ZONE3 = 0xcb
    B_ZONE4 = 0xcc
    B_ZONE5 = 0xcd
    B_ZONE6 = 0xce
    B_ZONE7 = 0xcf
    B_ZONE8 = 0xd0
    B_ZONE9 = 0xd1
    B_ZONE10 = 0xd2
    B_ZONE11 = 0xd3
    B_ZONE12 = 0xd4
    B_ZONE13 = 0xd5
    B_ZONE14 = 0xd6
    B_ZONE15 = 0xd7
    B_ZONE16 = 0xd8
    B_INTEGRA_1_48 = 0x1b
    B_INTEGRA_49_96 = 0x1c
    B_INTEGRA_97_128 = 0x1d
    B_MULTISENSE = 0x18

    _size = 13

    def __init__(self, raw=None):
        """Init the frame."""
        if raw:
            self.frame = bytearray(raw)
        else:
            self.frame = bytearray(self._size)

    def __repr__(self):
        """Provide the text representation of the frame."""
        return ":".join("{:02x}".format(c) for c in self.frame)


class CAN(FrameClass):
    """This is a CAN frame format transmit over TCP."""

    _size = 13

    # CAN ID (MAC address)
    mac = FixedField("<I", 0)
    # Frame Length <= 8
    length = FixedField("B", 4)
    d0 = FixedField("B", 5)
    d1 = FixedField("B", 6)
    d2 = FixedField("B", 7)
    d3 = FixedField("B", 8)
    d4 = FixedField("B", 9)
    d5 = FixedField("B", 10)
    d6 = FixedField("B", 11)
    d7 = FixedField("B", 12)

    # d1 alias
    type = FixedField("B", 6)
    # big-endian id for destination address
    # alias for (d0 << 24) + (d1 << 16) + (d2 << 8) + d3
    mac2 = FixedField(">I", 5)

    def __repr__(self):
        """Provide the text representation of the frame."""
        return "[CAN]: ID={:04x} len={:01x} d0={:02x} d1={:02x} d2={:02x} d3={:02x} d4={:02x} d5={:02x} d6={:02x} " \
               "d7={:02x}".format(self.mac, self.length, self.d0, self.d1, self.d2, self.d3, self.d4, self.d5, self.d6,
                                  self.d7)

    @property
    def inputs(self):
        """Return 24-bit value with particular bits representing input state."""
        return ((self.d4 << 16) | (self.d3 << 8) | self.d2) & 0xffffff

    @property
    def outputs(self):
        """Return 24-bit value with particular bits representing output state."""
        return ((self.d7 << 16) | (self.d6 << 8) | self.d5) & 0xffffff

    @property
    def temp(self):
        """Return the list of temperature values."""
        return list(map(lambda x: x - 100, self.bytes))

    @property
    def tempF(self):
        """Return the list of temperature values represented in float."""
        return [((self.frame[i] + self.frame[i + 1] * 256) - 1000) / 10 for i in range(7, 13, 2)]

    @property
    def bytes(self):
        """Return list of byte values."""
        return [i for i in self.frame[7:]]

    @property
    def year(self):
        """Return a year."""
        return 2000 + self.d2

    @property
    def month(self):
        """Return a month."""
        return self.d3

    @property
    def day(self):
        """Return a day."""
        return self.d4

    @property
    def weekday(self):
        """Return a weekday."""
        return self.d5

    @property
    def hour(self):
        """Return a hour."""
        return self.d6 & 0x1f

    @property
    def minute(self):
        """Return a minute."""
        return self.d7

    @property
    def flags(self):
        """Return a flags."""
        return ((self.d7 << 40) |
                (self.d6 << 32) |
                (self.d5 << 24) |
                (self.d4 << 16) |
                (self.d3 << 8) |
                (self.d2 << 0)) & 0xffffffffffff

    @property
    def zones(self):
        """Return a status of zones."""
        return ((self.d5 << 24) | (self.d4 << 16) | (self.d3 << 8) | self.d2) & 0xffff

    @property
    def zone_measured_temp(self):
        """Return a zone measured temperature."""
        return (((self.d3 << 8) | self.d2) & 0xff) / 10

    @property
    def zone_target_temp(self):
        """Return a zone target temperature."""
        return (((self.d5 << 8) | self.d4) & 0xff) / 10

    @property
    def is_zone_active(self):
        """Return true if zone is active."""
        return bool(self.d7 & 0x01)

    @property
    def is_zone_heating(self):
        """Return true if zone is heating."""
        return bool(self.d7 & 0x02)

    @property
    def is_zone_day(self):
        """Return true if zone is in day mode."""
        return bool(self.d7 & 0x04)

    @property
    def zone_mode(self):
        """Return zone mode.

        0 - Calendar/Auto
        1 - Manual
        2 - Semi-Manual - to next calendar change
        3 - Holiday
        4 - Blocked
        """
        return (self.d7 >> 4) & 0x7


class ServerBinaryOut(CAN):
    """This is frame used to set binary/digital output on the server.

    0000   2d d4 0d 00 00 00 05 00 00 00 01 00 02 ff 00 00
    0010   00 2f 01

    0000   2d d4 0d 00 00 00 05 00 00 00 01 00 02 00 00 00
    0010   00 30 00

    """

    def __init__(self, mask, value):
        """Initialize ServerBinaryOut frame object."""
        CAN.__init__(self)
        self.mac = 0x01000000
        self.length = 0
        self.d0 = mask
        self.d1 = value


class DeviceByteOut(CAN):
    """This is frame used to set analog/byte output on the device other than server.

    0000   2d d4 10 00 00 00 01 64 00 00 00 08 00 00 13 05
    0010   14 73 01 00 39 01

    0000   2d d4 10 00 00 00 01 64 00 00 00 08 00 00 13 05
    0010   14 93 01 00 59 01

    """

    def __init__(self, mac, mask, value):
        """Initialize DeviceByteOut frame object."""
        CAN.__init__(self)
        self.mac = 0x00000064
        self.mac2 = mac
        self.length = 8
        self.d4 = 0x14
        self.d5 = value
        self.d6 = mask & 0xff
        self.d7 = (mask >> 8) & 0xff


class CANLong(FrameClass):
    """This is CAN Long frame."""

    _size = 15
    # CAN ID (MAC address)
    mac = FixedField(">I", 0)
    srv_info = FixedField("B", 4)
    length = FixedField("B", 5)
    radio_type = FixedField("B", 6)
    radio_length = FixedField("B", 7)
    slave = FixedField("B", 8)
    slave_addr = FixedField("B", 9)
    slave_ctrl = FixedField("B", 10)
    sub_type = FixedField("B", 11)
    function = FixedField("B", 12)
    value = FixedField("B", 13)
    mask = FixedField("B", 14)


class LoRaBinaryOut(CANLong):
    """This is a CAN frame for LoRa communication."""

    def __init__(self, slave_addr, mask, value):
        """Initialize LoRaBinaryOut frame."""
        CANLong.__init__(self)
        self.mac = 0x00000001
        self.srv_info = 0x0e  # 0x0e - info for srv it goes to radio module
        self.length = 0x09
        self.radio_type = 0x03  # 0x03 - information type in radio module
        self.radio_length = 0x04
        self.slave = 0x01  # 0x01 - sending to slave
        self.slave_addr = slave_addr  # 0x02 - slave address
        self.slave_ctrl = 0x11  # 0x11 - info for slave it will be controlled
        self.sub_type = 0x00  # 0x00 - should be 0
        self.function = 0x00  # 0x00 - simple function
        self.value = value & 0xff
        self.mask = mask & 0xff


####################################


class CANSetBinaryToDevice(CAN):
    """Frame to set binary for device (not server).

    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 0d 01 07 03 74 00
    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 0d 02 00 00 6b 00
    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 0d 03 0b 33 aa 00
    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 0d 04 01 14 82 00

    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 0d 03 02 e9 57 00

    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 0d 00 04 00 6d 00
    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 0d 00 04 00 6d 00
                                                                ^^^^^ CRC
                                                          ^^ byte
                                                        ^^ mask
                                                    ^^ opcode
                                        ^^^^^^^^^^^ device mac
                                     ^^ length
                         ^^^^^^^^^^^ special mac (sent to server)

    """

    def __init__(self, mac, mask, value):
        """Initialize CANSetBinaryToDevice frame."""
        CAN.__init__(self)
        self.mac = 0x0f000000
        self.mac2 = mac
        self.d4 = 0x07
        self.d5 = 0x00
        self.d6 = 0x00
        self.d7 = 0x00
        # self.d6 = 0x01
        # self.d7 = 0x14


class CANSetByte(CAN):
    """Frame to set byte."""

    def __init__(self, mac, mask, value):
        """Initialize CANSetByte frame."""
        CAN.__init__(self)
        self.mac = mac
        self.length = 8
        self.d0 = mask
        self.d1 = value


class CANSetByteToDevice(CAN):
    """Frame to set byte for device (not server).

                                        d0 d1 d2 d3 d3 d5 d6 d7
    2d d4 10 00 00 00 00 0f 00 00 00 08 00 00 13 05 07 01 02 00 66 00
                                                                ^^^^^ CRC
                                                          ^^ byte
                                                       ^^ mask
                                                    ^^ opcode
                                        ^^^^^^^^^^^ device mac
                                     ^^ length
                         ^^^^^^^^^^^ special mac (sent to server)


    """

    def __init__(self, mac, mask, value):
        """Initialize CANSetByteToDevice frame."""
        CAN.__init__(self)
        self.mac = 0x0f000000
        self.mac2 = mac
        self.length = 8
        self.d4 = 7
        self.d5 = mask
        self.d6 = value

        # self.d4 = 20
        # self.d5 = value
        # self.d6 = mask & 0xff
        # self.d7 = (mask >> 8) & 0xff


class ServerFrame(FrameClass):
    """This is a ServerFrame.

    This frame is used to encapsulate server function and CAN frames.
    """

    _size = 9
    preamble = FixedField("<H", 0)
    size = FixedField("I", 2)
    type = FixedField("B", 6)
    payload = VariableByteField(7, 'update')
    crc = FixedField("<H", -2)

    def __init__(self, type, payload):
        """Initialize ServerFrame with payload."""
        FrameClass.__init__(self)
        self.preamble = 0xd42d
        self.type = type
        self.payload = payload
        self.update()

    def update(self):
        """Update frame.

        Calculate the CRC and frame size.
        """
        self._calc_crc()
        self._calc_size()

    def _calc_crc(self):
        crc = 0x2d
        for b in self.payload:
            crc += b
        self.crc = crc

    def _calc_size(self):
        self.size = 3 + len(self.payload)


class UserFrame(ServerFrame):
    """This is a UserFrame."""

    def __init__(self, username=b'admin'):
        """Initialize the username frame."""
        ServerFrame.__init__(self, 10, username)
        # super(UserFrame, self).__init__(10, username)


class PasswordFrame(ServerFrame):
    """This is a PasswordFrame."""

    def __init__(self, password, hashed=False):
        """Initialize the PasswordFrame."""
        if isinstance(password, str):
            password = password.encode()
        if hashed:
            m = hashlib.md5()
            m.update(password)
            password = m.hexdigest().encode()
        ServerFrame.__init__(self, 11, password)


class InfoFrame(ServerFrame):
    """This is an InfoFrame."""

    def __init__(self):
        """Initialize InfoFrame."""
        ServerFrame.__init__(self, 12, b'ok')

#######################################################


class CANSer(FrameClass):
    """This is a CANSer frame class."""

    Temp = 0x05
    TempF1_3 = 0x06
    TempF4_6 = 0x07
    Byte1_6 = 0x0c
    Byte7_12 = 0x0d
    Byte13_18 = 0x0e
    Binary = 0x0f
    Time = 0x10
    NTP = 0x11
    Wireless = 0x2a
    Flags = 0x80

    _size = 12
    mac = FixedField("I", 0)
    d0 = FixedField("B", 4)
    d1 = FixedField("B", 5)
    type = FixedField("B", 5)
    d2 = FixedField("B", 6)
    d3 = FixedField("B", 7)
    d4 = FixedField("B", 8)
    d5 = FixedField("B", 9)
    d6 = FixedField("B", 10)
    d7 = FixedField("B", 11)

    def __repr__(self):
        """Provide the text representation of the frame."""
        return "[CAN]: MAC={:04x} d0={:02x} d1={:02x} d2={:02x} d3={:02x} d4={:02x} d5={:02x} d6={:02x} " \
               "d7={:02x}".format(self.mac, self.d0, self.d1, self.d2, self.d3, self.d4, self.d5, self.d6, self.d7)

    @property
    def inputs(self):
        """Return binary inputs states."""
        return (self.d4 << 16 | self.d3 << 8 | self.d2) & 0xffffff

    @property
    def outputs(self):
        """Return binary output states."""
        return (self.d7 << 16 | self.d6 << 8 | self.d5) & 0xffffff

    @property
    def temp(self):
        """Return a list of temperature values (integer)."""
        return list(map(lambda x: x - 100, self.bytes))

    @property
    def tempF(self):
        """Return the list of float temperature values."""
        return [((self.frame[i] + self.frame[i + 1] * 256) - 1000) / 10 for i in range(6, 12, 2)]

    @property
    def bytes(self):
        """Return a list of bytes."""
        return [i for i in self.frame[6:]]

    @property
    def year(self):
        """Return year."""
        return 2000 + self.d2

    @property
    def month(self):
        """Return month."""
        return self.d3

    @property
    def day(self):
        """Return day."""
        return self.d4

    @property
    def weekday(self):
        """Return weekday."""
        return self.d5

    @property
    def hour(self):
        """Return hour."""
        return self.d6

    @property
    def minute(self):
        """Return minute."""
        return self.d7

    @property
    def flags(self):
        """Return flags."""
        return (self.d7 << 48 | self.d6 << 32 | self.d5 << 24 | self.d4 < 16 | self.d3 << 8 | self.d2) & 0xffffffffffff


class CANSetBinarySer(CANSer):
    """Set binary output to serial."""

    _size = 12
    dst = FixedField(">I", 4)

    def __init__(self, mac, mask, value):
        """Initialize CANSetBinarySer frame."""
        CANSer.__init__(self)
        self.mac = 0x0f000000
        self.dst = mac
        self.d4 = 20
        self.d5 = value
        self.d6 = mask & 0xff
        self.d7 = (mask >> 8) & 0xff


class CANSetByteSer(CANSer):
    """Set binary output to serial."""

    _size = 12
    dst = FixedField(">I", 4)

    def __init__(self, mac, mask, value):
        """Initialize CANSetByteSer frame."""
        CANSer.__init__(self)
        self.mac = 0x0f000000
        self.dst = mac
        self.d4 = 20
        self.d5 = value
        self.d6 = mask & 0xff
        self.d7 = (mask >> 8) & 0xff


class SerialFrame(FrameClass):
    """This is a SerialFrame.

    This frame is used to encapsulate CAN Frame to be sent over serial (AMPIO Programmer) interface..
    2d:d4:0e:01:05:13:00:00:fe:0c:ff:00:00:00:00:00:5d
    """

    _size = 5
    preamble = FixedField("<H", 0)
    size = FixedField("B", 2)
    type = FixedField("B", 3)
    payload = VariableByteField(4, 'update')
    crc = FixedField("B", -1)

    def __init__(self, type, payload):
        """Initialize the frame."""
        FrameClass.__init__(self)
        self.preamble = 0xd42d
        self.type = type
        self.payload = payload
        self.update()

    def update(self):
        """Update the frame.

        Calculate the size and CRC.
        """
        self._calc_size()
        self._calc_crc()

    def _calc_crc(self):
        crc = 0x2d + self.type + self.size
        for b in self.payload:
            crc += b
        self.crc = crc & 0xff

    def _calc_size(self):
        self.size = 2 + len(self.payload)


"""
Frames to port 1234

type = 01

mac = 64:00:00:00  - little-endian
length = 8
mac2 = 00:00:13:05 - big-endian

function = 14 (20 dec)
value = 73
output = 01


0000   2d d4 10 00 00 00 01 64 00 00 00 08 00 00 13 05
0010   14 73 01 00 39 01

0000   2d d4 10 00 00 00 01 64 00 00 00 08 00 00 13 05
0010   14 93 01 00 59 01

0000   2d d4 10 00 00 00 01 64 00 00 00 08 00 00 13 05
0010   14 54 01 00 1a 01

0000   2d d4 10 00 00 00 01 64 00 00 00 08 00 00 13 05
0010   14 ff 02 00 c6 01

type = 05
mac = 0x00000001 - big endian
length = 0
mask = 02
value = ff

0000   2d d4 0d 00 00 00 05 00 00 00 01 00 02 ff 00 00
0010   00 2f 01

0000   2d d4 0d 00 00 00 05 00 00 00 01 00 02 00 00 00
0010   00 30 00

0000   2d d4 0d 00 00 00 05 00 00 00 01 00 01 ff 00 00
0010   00 2e 01

"""

# can = LoRaBinaryOut(0x02, 0x01, 0x01)
# print(can)
# frame = ServerFrame(0x05, payload=can.frame)
# print(frame)
# can = ServerBinaryOut(0x02, 0xff)
# print(can)
# frame = ServerFrame(0x05, payload=can.frame)
# print(frame)


# frame = PasswordFrame(b'pampio', hash=True)
# print(frame)


# can = CANSetBinarySer(mac=0xeeeeeeee, mask=1, value=255)
# print(can)
# can = CANSer(raw=b'\x05\x13\x00\x00\xfe\x0c\xff\x00\x00\x00\x00\x00')
# print(can)
# frame = SerialFrame(1, payload=can.frame)
# print(frame
# )

"""

Rolety:

    def __init__(self, mac, mask, value):
        CAN.__init__(self)
        self.mac = 0x00000064
        self.mac2 = mac
        self.length = 8
        self.d4 = 0x14
        self.d5 = value
        self.d6 = mask & 0xff
        self.d7 = (mask >> 8) & 0xff

Rolety góra:

0x0040:  f75c 2dd4 1000 0000 0164 0000 0008 0000  .\-......d......
0x0050:  196a 1401 0200 3301


Rolety dół:

0x0040:  f798 2dd4 1000 0000 0164 0000 0008 0000  ..-......d......
0x0050:  196a 1400 0200 3201


Rolety stop:  mask 0x02
0x0000:  4500 004a 1a7b 4000 3f06 a9d8 ac1f 0b1b  E..J.{@.?.......
0x0010:  ac1f 1401 f8bb 04d2 9f51 e271 f96a 78b9  .........Q.q.jx.
0x0020:  8018 1000 361f 0000 0101 080a 440c 542a  ....6.......D.T*
0x0030:  0770 895f 2dd4 1000 0000 0164 0000 0008  .p._-......d....
0x0040:  0000 1968 1400 0200 3001

Rolety stop: mask 0x04
0x0000:  4500 004a 79e7 4000 3f06 4a6c ac1f 0b1b  E..Jy.@.?.Jl....
0x0010:  ac1f 1401 f8bb 04d2 9f51 e21c f968 1737  .........Q...h.7
0x0020:  8018 1000 984d 0000 0101 080a 440c 5039  .....M......D.P9
0x0030:  0770 88fb 2dd4 1000 0000 0164 0000 0008  .p..-......d....
0x0040:  0000 1968 1400 0400 3201                 ...h....2.

Rolety góra:
0x0000:  4500 004a ac54 4000 3f06 17ff ac1f 0b1b  E..J.T@.?.......
0x0010:  ac1f 1401 f8be 04d2 2601 6d48 36b3 11eb  ........&.mH6...
0x0020:  8018 1000 ec88 0000 0101 080a 440f 6146  ............D.aF
0x0030:  0770 d7d1 2dd4 1000 0000 0164 0000 0008  .p..-......d....
0x0040:  0000 1968 1402 0400 3401                 ...h....4.

Rolety dół:
0x0000:  4500 004a 714e 4000 3f06 5305 ac1f 0b1b  E..JqN@.?.S.....
0x0010:  ac1f 1401 f8c1 04d2 307a 0fb0 c5c4 ef61  ........0z.....a
0x0020:  8018 1000 2a04 0000 0101 080a 4411 d076  ....*.......D..v
0x0030:  0771 16b8 2dd4 1000 0000 0164 0000 0008  .q..-......d....
0x0040:  0000 1968 1401 0200 3101                 ...h....1.

"""
