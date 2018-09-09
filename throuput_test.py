from gevent.server import StreamServer
from streamux import Session, BrokenPipeError
import multiprocessing
import time
import gevent
from gevent import socket, spawn
import os

def stream_handle(stream):
    data = stream.read()
    stream.write(data)
    stream.close()



def listener(socket, address):
    print(os.getpid(), 'New connection from %s:%s' % address)
    rfileobj = socket.makefile(mode='rb')
    session = Session(rfileobj, False, keep_alive_interval=100,
                      keep_alive_timeout=100)
    while not session.closed():
        try:
            stream = session.accept_stream()
            spawn(stream_handle, stream)
        except BrokenPipeError:
            print "server: XXXX BrokenPipeError "
    print "server: transport exit"
    print "server: active strems", session.stream_count
    session.close()


def server():
    server = StreamServer(('0.0.0.0', 2786), listener)
    server.serve_forever()


# ===================================
NUM_CALLS = 1 #* 50 * 2  # 0000
POOL = 100
SZ = 4096
data = 'a' * SZ


def beam(session):
    stream = session.open_stream()
    #$print "opened", stream
    stream.write(data)
    response = stream.read()
    assert len(data) == len(response)
    stream.close()


def parallel(session):
    pool = gevent.pool.Pool(POOL)
    [pool.spawn(beam, session) for _ in range(NUM_CALLS)]
    pool.join()


def call():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 2786))
    session = Session(sock.makefile('rw'), True)

    start = time.time()

    [beam(session) for _ in range(NUM_CALLS)]
    # parallel(session)

    dt = time.time() - start
    print('call: %d KB/s, dt=%.4f' % (NUM_CALLS * SZ / dt / 1024, dt))
    print "client: active strems", session.stream_count
    print "client: SessionClose and sleep gevent for 2 sec"
    session.close()
    gevent.sleep(2)
    print "client : final stream count", session.stream_count


if __name__ == '__main__':
    try:
        p = multiprocessing.Process(target=server)
        p.start()
        gevent.sleep(0.1)
        call()
    finally:
        gevent.sleep(5)
        p.terminate()
