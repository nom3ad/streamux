from zerorpc import Context
import gevent
from gevent import socket
from streamux import Session
from msgpack import packb, unpackb


class Client(object):
    def __init__(self, address):
        host, port = address.split(":")
        self.session = self.create_session((host, int(port)))

    def __getattr__(self, name):
        def f(*args, **kwargs):
            requestb = packb((name, args, kwargs),)
            stream = self.session.open_stream()
            #$print "opened", stream
            stream.write(requestb)
            result, error = unpackb(stream.read())
            stream.close()
            if error:
                raise Exception(error)
            return result
        return f

    def __del__(self):
        self.session.close()

    @staticmethod
    def create_session(addr):
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        session = Session(sock.makefile('rw'), True)
        return session
