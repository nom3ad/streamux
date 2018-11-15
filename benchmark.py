from gevent.server import StreamServer
from streamux import Session, BrokenPipeError
import multiprocessing
import time
import gevent
from gevent import socket, spawn
import os,sys

"""
(6985, 'New connection from 127.0.0.1:59630')
call: 84093 KB/s, dt=0.9513
client: active strems 0
client: SessionClose and sleep gevent for 2 sec
@@@ [ 6984 ] closing session
@@@ [ 6984 ] exits sendloop of <Session with <gevent._socket2._fileobject object at 0x7f55f658e3b0>>
@@@ [ 6984 ] closing session
@@@ [ 6984 ] exits rcvloop of <Session with <gevent._socket2._fileobject object at 0x7f55f658e3b0>>
client : final stream count 0
@@@ [ 6985 ] closing session
@@@ [ 6985 ] exits rcvloop of <Session with <gevent._socket2._fileobject object at 0x7f55f6fabb90>>
server: XXXX BrokenPipeError 
server: transport exit
server: active strems 0
@@@ [ 6985 ] closing session
@@@ [ 6985 ] exits sendloop of <Session with <gevent._socket2._fileobject object at 0x7f55f6fabb90>>
server endof serve!!!

[Done] exited with code=0 in 3.503 seconds

[Running] /home/gandalf/.local/share/virtualenvs/streamux-RdR6tGpu/bin/python -u "/home/gandalf/Desktop/PROJECTS/streamux/benchmark.py"

(6989, 'New connection from 127.0.0.1:59632')
call: 76556 KB/s, dt=1.0450
client: active strems 0
client: SessionClose and sleep gevent for 2 sec
@@@ [ 6988 ] closing session
@@@ [ 6988 ] exits sendloop of <Session with <gevent._socket2._fileobject object at 0x7f887659e3b0>>
@@@ [ 6988 ] closing session
@@@ [ 6988 ] exits rcvloop of <Session with <gevent._socket2._fileobject object at 0x7f887659e3b0>>
client : final stream count 0
@@@ [ 6989 ] closing session
@@@ [ 6989 ] exits rcvloop of <Session with <gevent._socket2._fileobject object at 0x7f8876fbbb90>>
server: XXXX BrokenPipeError 
server: transport exit
server: active strems 0
@@@ [ 6989 ] closing session
@@@ [ 6989 ] exits sendloop of <Session with <gevent._socket2._fileobject object at 0x7f8876fbbb90>>
server endof serve!!!

"""
server = None

def run_server():
    global server

    def _stream_handle(stream):
        data = stream.read()
        stream.write(data)
        stream.close()


    def _listener(sock, address):
        print(os.getpid(), 'New connection from %s:%s' % address)
        session = Session(sock.makefile(mode='rw'), False, keep_alive_interval=100,keep_alive_timeout=100)
        oops = None
        try:
            while not session.closed():
                try:
                    stream = session.accept_stream()
                    spawn(_stream_handle, stream)
                except BrokenPipeError as oops:
                    raise
        except:
            raise

        finally:
            print "SERVER: session closed=%s.  reason = %r. activeStreams=%d" % (session.closed(), oops, session.stream_count)
            session.close()
            server.close()
            gevent.sleep(0.2)
            print "SERVER: XXX Should not be here.  server force Halt!!"
            exit()

    server = StreamServer(('0.0.0.0', 2786), _listener)
    server.serve_forever()
    print "SERVER: endof serve!!!"


# ===================================
NUM_CALLS = 10000  # * 50 * 2  # 0000
POOL = 100
SZ = 4096 * 2
data = 'a' * SZ
CONTENT = b"a"

def beam(session):
    try:
        stream = session.open_stream()
        #$print "opened", stream
        stream.write(data)
        response = stream.read()
        # assert len(data) == len(response)
        stream.close()
    except BrokenPipeError as oops:
        print "CLIENT: session closed=%s.  reason = %r. activeStreams=%d" % (session.closed(), oops, session.stream_count)
        exit()

def parallel(session):
    pool = gevent.pool.Pool(POOL)
    [pool.spawn(beam, session) for _ in range(NUM_CALLS)]
    pool.join()


def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect(('localhost', 2786))
    session = Session(sock.makefile('rw'), True)
    start = time.time()

    # [beam(session) for _ in range(NUM_CALLS)]
    parallel(session)

    dt = time.time() - start
    print('call: %d KB/s, dt=%.4f' % (NUM_CALLS * SZ / dt / 1024, dt))
    print "client: active strems", session.stream_count
    print "client: SessionClose and await exit"
    session.close()
    gevent.sleep(0.1)
    print "client: final stream count", session.stream_count


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == 'server':
        run_server()
        exit()
    elif len(sys.argv) == 2 and sys.argv[1] == 'client':
        run_client()
        exit()

    try:
        p = multiprocessing.Process(target=run_server)
        p.start()
        gevent.sleep(0.1)
        run_client()
    finally:
        gevent.sleep(0.3)
        p.terminate()
