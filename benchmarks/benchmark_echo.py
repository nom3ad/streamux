from gevent.server import StreamServer
import gevent
from gevent import socket, spawn
from gevent import queue
import multiprocessing
import time
import os

"""

(4765, 'New connection from 127.0.0.1:59612')
on reader..
on writer..
call: 762043 KB/s, dt=1.2598
client: socker Close and sleep gevent for 0.5 sec
server: transport exit
server endof serve!!!
The end

"""

NUM_CALLS = 20000  # * 50 * 2  # 0000
POOL = 100
SZ = 4096  * 12

host = 'localhost'
server = None

def run_server():
    from gevent.server import StreamServer
    import gevent
    from gevent import socket, spawn
    from gevent import queue
    global server

    def _reader(f, q):
        print "on reader.."
        while True:
            data = f.recv(SZ)
            if not data:
                break
            # TODO: check this on other interfaces
            if len(data) != SZ:
                print len(data)
            q.put(data)
    
    def _writer(f, q):
        print "on writer.."
        while True:
            data = q.get()
            f.send(data)

    def _listener(sock, address):
        q = queue.Queue()
        print(os.getpid(), 'New connection from %s:%s' % address)
        r = spawn(_reader, sock, q)
        w = spawn(_writer, sock, q)
        r.join()
        print "server: transport exit"
        w.kill()
        server.close()
        gevent.sleep(0.5)
        print "XXX Should not be here.  server force Halt!!"
        exit()
    
    server = StreamServer(('0.0.0.0', 2786), _listener)
    server.serve_forever()
    print "server endof serve!!!"


# ===================================

data = b'a' * SZ
def beam(sock):
    sock.send(data)
    response = sock.recv(SZ)
    # assert len(data) == len(response)
    # print "*",

def parallel(fobj):
    # pool = gevent.pool.Pool(POOL)
    # [pool.spawn(beam, fobj) for _ in range(NUM_CALLS)]
    # pool.join()
    [beam(fobj) for _ in range(NUM_CALLS)]



def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, 2786))
    # fobj =  sock.makefile(mode='r+')
    start = time.time()
    # [beam(session) for _ in range(NUM_CALLS)]
    parallel(sock)

    dt = time.time() - start
    print('call: %d KB/s, dt=%.4f' % (NUM_CALLS * SZ / dt / 1024, dt))
    print "client: socker Close and sleep gevent for 0.5 sec"
    sock.close()
    gevent.sleep(0.5)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == 'server':
        run_server()
        exit()
    elif len(sys.argv) == 2 and sys.argv[1] == 'client':
        run_client()
        exit()
    else:
        try:
            p = multiprocessing.Process(target=run_server)
            p.start()
            gevent.sleep(0.2)
            run_client()
        finally:
            gevent.sleep(0.4)
            p.terminate()
            p.join()

    print "The end"
