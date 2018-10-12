from gevent.server import StreamServer
import gevent
from gevent import socket
from streamux import Session
from msgpack import packb, unpackb

class Server(object):
    _k_map = {}
    def __init__(self, address):
        host, port = address.split(":")

        def listener(socket, address):
            #$print('New connection from %s:%s' % address)
            rfileobj = socket.makefile(mode='rb')
            session = Session(rfileobj, False, keep_alive_interval=100,
                            keep_alive_timeout=100)
            while not session.is_closed():
                stream = session.accept_stream()
                #$print "accepted", stream
                gevent.spawn(self.stream_handle, stream)
            session.close()

        self._stream_server = StreamServer((host, int(port)), listener)

        self.serve = self._stream_server.serve_forever

        self._map = self._k_map

    @classmethod
    def register(cls, fn):
        cls._k_map[fn.__name__] = fn
        return fn

    def __del__(self):
        # self.session.close()
        pass

    def stream_handle(self, stream):
        data = stream.read()
        name, args, kwargs = unpackb(data, raw=False)
        result, error = None, None
        try:
            result = self._map[name](*args, **kwargs)
        except Exception as oops:
            error = repr(oops)
        stream.write(packb((result, error)))
        stream.close()

    @staticmethod
    def create_session(addr):
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        session = Session(sock.makefile('rw'), True)
        return session
