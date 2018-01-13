import gevent
from gevent import socket
from streamux import Session

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol


class RemoteException(Exception):
    pass


rpc = JSONRPCProtocol()


class Proxy:
    def __init__(self, session):
        self.session = session

    def __getattr__(self, name):
        def f(*args, **kwargs):
            request = rpc.create_request(name, args, kwargs)
            stream = self.session.open_stream()
            #$print "opened", stream
            stream.write(request.serialize())
            response = rpc.parse_reply(stream.read())
            stream.close()
            if hasattr(response, 'error'):
                raise RemoteException(response.error)
            return (response.result)
        return f


def rpc_client(host, port):
# sock = socket.create_connection(('localhost', 2786))
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    session = Session(sock.makefile('rw'), True)
    p = Proxy(session)
    return p


def main():
    p = rpc_client('localhost', 2786)
    print(p.foo('arun'))
    print (p.bar(5))
    print (p.foo('arun'))
    #$print p.foo('arun')
    #$print p.foo('arun')
    #$print p.foo('arun')

    session.close()
    pass

if __name__ == '__main__':
    main()
