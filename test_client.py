from gevent import socket
from streamux import Session


def main():
    # sock = socket.create_connection(('localhost', 2786))
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 2786))
    session = Session(sock.makefile('rw'), True)
    stream = session.open_stream()
    print "opened", stream
    stream.write('ping')
    print repr(stream.read())

if __name__ == '__main__':
    main()
