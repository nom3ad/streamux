from gevent.server import  StreamServer

from streamux import Session


def listener(socket, address):
    print('New connection from %s:%s' % address)
    # rfileobj = socket.makefile(mode='rb')
    session = Session(socket)
    stream = session.accept_stream()
    print stream.read()
    stream.write('pong')


def main():
    server = StreamServer(('0.0.0.0', '2786'), listener)

if __name__ == '__main__':
    main()