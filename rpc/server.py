from gevent.server import StreamServer
import gevent
from streamux import Session
from msgpack import packb, unpackb

class Server(object):
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

        self.serve = self.stream_server._serve_forever

        self._map = {}

    def register(self, fn):
        self._map[fn.__name__] = fn
        return fn

    def __del__(self):
        self.session.close()



    def stream_handle(self, stream):
        data = stream.read()
        stream.write(handle_incoming_message(data))
        stream.close()


    @staticmethod
    def create_session(addr):
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        session = Session(sock.makefile('rw'), True)
        return session





def foo(name):
    return "hello %s" % name

@dispatch.public
def echo(name):
    return name

@dispatch.public
def bar(sec):
    gevent.sleep(sec)
    return sec
