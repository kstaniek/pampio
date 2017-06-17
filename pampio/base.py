"""This is a base Ampio Client class implementation."""
import abc
import logging
import asyncio

from pampio.utils import frame_to_str


class AmpioClient(asyncio.Protocol):
    """This is a base class for Ampio client."""

    def __init__(self, loop):
        """Initialize the AmpioClient object."""
        self.loop = loop
        self.connected = False
        self.transport = None
        self.out_queue = asyncio.Queue(loop=self.loop)
        self.in_queue = asyncio.Queue(loop=self.loop)
        self._ready = asyncio.Event(loop=self.loop)
        self.listeners = []

    def connection_made(self, transport):
        """Call back when connection is made."""
        logging.info("Connected successfully")
        self.transport = transport
        self.connected = True
        asyncio.ensure_future(self._send_messages(), loop=self.loop)
        self._ready.set()

    def data_received(self, data):
        """Call back when data received."""
        logging.debug("[I][RAW] {}".format(frame_to_str(data)))
        for char in data:
            self.in_queue.put_nowait(char)
        return

    def connection_lost(self, exc):
        """Call back when connection lost."""
        logging.debug(exc)
        self.connected = False
        logging.info('The server closed the connection')
        logging.info('Reconnect in 5 sec')
        self.reconnect(5)

    def __call__(self):
        """Call by loop.create_connection.

        This is a protocol factory.
        """
        return self

    def exception_handler(self, loop, context):
        """Handle exception."""
        logging.debug('Exception: {}'.format(context))
        # exc = context['exception']
        if not self.connected:
            logging.info('Could not connect.')
            self.reconnect(5)
        self.connected = False

    @classmethod
    @abc.abstractmethod
    def connect(cls):
        """Connect to AMPIO Server.

        This needs to be implemented in specific client implementation.
        """
        pass

    @abc.abstractmethod
    def reconnect(self, delay):
        """Reconnect to AMPIO Server.

        This needs to be implemented in specific client implementation.
        """

    @asyncio.coroutine
    def send_message(self, data):
        """Put data to the output queue."""
        yield from self.out_queue.put(data)

    @asyncio.coroutine
    def _send_messages(self):
        """Send message to server."""
        yield from self._ready.wait()
        while True:
            data = yield from self.out_queue.get()
            logging.debug("[O][RAW] {}".format(frame_to_str(data)))
            self.transport.write(data)

    def register_listener(self, func):
        """Register event listener."""
        if func not in self.listeners:
            self.listeners.append(func)
            return True
        return False

    def unregister_listener(self, func):
        """Unregister event listenet."""
        if func in self.listeners:
            self.listeners.remove(func)
            return True
        return False

    def received_message(self, can):
        """Call listeners on received message."""
        for listener in self.listeners:
            listener(can)
