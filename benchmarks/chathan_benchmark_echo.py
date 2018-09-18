from gevent.server import StreamServer
import multiprocessing
import time
import gevent
from gevent import socket, spawn
from gevent import queue
import os


NUM_CALLS = 10000  # * 50 * 2  # 0000
POOL = 100
SZ = 4096


server = None

def run_server():
    global server

    def _reader(f, q):
        print "on reader.."
        while True:
            data = f.read(1)
            print "#",
            if not data:
                break
            q.put(data)
    
    def _writer(f, q):
        print "on writer.."
        while True:
            data = q.get()
            f.write(data)

    def _listener(sock, address):
        q = queue.Queue()
        print(os.getpid(), 'New connection from %s:%s' % address)
        print sock.recv(10)
        rfileobj = sock.makefile(mode='r+')
        r = spawn(_reader, rfileobj, q)
        w = spawn(_writer, rfileobj, q)
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
def beam(fobj):
    fobj.write(data)
    response = fobj.read(SZ)
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
    sock.connect(('localhost', 2786))
    sock.send("12345")
    fobj =  sock.makefile(mode='r+')
    start = time.time()
    # [beam(session) for _ in range(NUM_CALLS)]
    parallel(fobj)

    dt = time.time() - start
    print('call: %d KB/s, dt=%.4f' % (NUM_CALLS * SZ / dt / 1024, dt))
    print "client: socker Close and sleep gevent for 2 sec"
    sock.close()
    gevent.sleep(2)

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
        gevent.sleep(1)
        p.terminate()
