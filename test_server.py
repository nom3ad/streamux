from gevent.server import  StreamServer

from streamux import Session


def listener(socket, address):
    print('New connection from %s:%s' % address)
    rfileobj = socket.makefile(mode='rb')
    session = Session(rfileobj, False)
    stream = session.accept_stream()
    print "accepted", stream
    print repr(stream.read())
    stream.write('pong')


def main():
    server = StreamServer(('0.0.0.0', 2786), listener)
    server.serve_forever()

if __name__ == '__main__':
    main()
