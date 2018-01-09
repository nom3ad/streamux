from gevent.socket import create_connection
from streamux import Session


def listener(socket, address):
    print('New connection from %s:%s' % address)
    rfileobj = socket.makefile(mode='rb')
    


def main():
    conn = create_connection('localhost:2786')
    session = Session(conn)
    stream = session.open_stream()
    stream.write('ping')
    print stream.read()

if __name__ == '__main__':
    main()