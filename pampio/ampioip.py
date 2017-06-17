"""This is IP gateway implementation Ampio Server."""

import asyncio
import logging

from pampio.base import AmpioClient
from pampio.frame import UserFrame, PasswordFrame, ServerFrame, ServerBinaryOut, DeviceByteOut
from pampio.utils import frame_to_str

FRAME_TO_APP = 0x02


class AmpioIPClient(AmpioClient):
    """This is a main Client class implementation."""

    def __init__(self, loop, host, port, username, password):
        """Initialize the AmpioIPClient class."""
        AmpioClient.__init__(self, loop)
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.frame = bytearray(65535)

        asyncio.ensure_future(self._send_messages(), loop=self.loop)

    def connection_made(self, transport):
        """Call when connection is made."""
        AmpioClient.connection_made(self, transport)

        asyncio.ensure_future(self.deserializer())
        asyncio.ensure_future(self.send_message(UserFrame(username=self.username).frame))
        asyncio.ensure_future(self.send_message(PasswordFrame(password=self.password, hashed=True).frame))
        # get XML state
        # asyncio.async(self.send_message(ServerFrame(108, b'\x00').frame))
        # asyncio.async(self.send_message(InfoFrame().frame))

    @asyncio.coroutine
    def deserializer(self):
        """Deserialize frame from input queue."""
        yield from self._ready.wait()
        state = 0
        while True:
            data = yield from self.in_queue.get()
            if state == 0:
                if data == 0x2d:
                    state = 1
                continue
            elif state == 1:
                if data == 0xd4:
                    state = 2
                    index = 0
                    length = 0
                else:
                    logging.error("Frame error")
                    state = 0
                continue

            # get frame length (incl. CRC)
            elif state == 2:
                length = length | (data << (index << 3))
                index += 1
                if index == 4:
                    state = 3
                    index = 0
                    length &= 0xffffffff
                    payload_size = length - 3  # (1 byte type and 2 byte crc)
                continue

            # get frame type
            elif state == 3:
                frame_type = data
                crc = 0x2d
                index = 0
                # if frame to app (CAN) get the sequence number
                if frame_type == FRAME_TO_APP:
                    state = 4
                    sequence = 0
                # else frame is not CAN
                else:
                    state = 5
                continue

            # get sequence number
            elif state == 4:
                sequence = sequence | (data << (index << 3))
                index += 1
                crc += data
                if index == 2:
                    index = 0
                    state = 5
                    payload_size -= 2  # 1 byte sequence number
                continue

            # get payload
            elif state == 5:
                self.frame[index] = data
                crc += data
                index += 1
                if index == payload_size:
                    state = 6
                    index = 0
                    crc_received = 0
                    continue

            # get crc
            elif state == 6:
                crc_received = crc_received | (data << (index << 3))
                index += 1
                if index == 2:
                    state = 0
                    crc_received &= 0xffff
                    if crc_received != crc:
                        logging.error("CRC Error")
                        continue
                    if frame_type == FRAME_TO_APP:  # CAN Frame
                        index = 0
                        while index < payload_size:
                            logging.debug("[I][CAN] {}".format(frame_to_str(self.frame[index:index + 13])))
                            self.received_message(self.frame[index:index + 13])
                            index += 13
                    else:
                        logging.debug("[I][UNK] {}".format(self.frame[0:payload_size]))

    @asyncio.coroutine
    def binary_output(self, mac, mask, value):
        """Set binary output on AMPIO server.

        Args:
            mac (dword): CAN ID (mac) of the device.
            mask (byte): Bitmask.
            value (byte): 0x00 or 0xff.

        Returns:
            None.

        """
        if mac > 1:
            logging.error("Setting binary out on module other than server not implemented yet.")
            # logging.debug("Binary output to module")
            # mask = (1 << index) & 0xff
            # value = value
            # can = CANSetBinaryToDevice(mac, mask, value=value)
            # frame = ServerFrame(type=0, payload=can.frame)
            # yield from self.out_queue.put(frame.frame)
            # pass
        else:
            can = ServerBinaryOut(mask, value=value)
            frame = ServerFrame(type=5, payload=can.frame)
            yield from self.out_queue.put(frame.frame)

    @asyncio.coroutine
    def byte_output(self, mac, mask, value):
        """Set byte output on AMPIO device."""
        if mac > 1:
            can = DeviceByteOut(mac, mask, value)
            frame = ServerFrame(type=1, payload=can.frame)
            yield from self.out_queue.put(frame.frame)
        else:
            logging.error("Setting analog output on server not supported.")

    @classmethod
    def connect(cls, loop, host, port, username='admin', password='ampio'):
        """Connect to AMPIO Server over TCP."""
        logging.info('Connecting to {}:{}'.format(host, port))
        client = cls(loop, host, port, username, password)
        loop.set_exception_handler(client.exception_handler)
        coro = loop.create_connection(client, host, port)
        asyncio.ensure_future(coro, loop=loop)
        return client

    def reconnect(self, delay):
        """Reconnect to AMPIO server over TCP."""
        self.loop.call_later(delay, self.connect, self.loop, self.host, self.port)
