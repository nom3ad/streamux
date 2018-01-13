import multiprocessing

import time
import gevent


NUM_CALLS = 10000
POOL=1
import test_server
import test_client

def parallel(p):
    pool = gevent.pool.Pool(POOL)
    print "add"
    [pool.spawn(p.echo, "aloha") for _ in range(NUM_CALLS)]
    print "join"
    pool.join()

def call():
    p = test_client.rpc_client('localhost', 2786)
    start = time.time()
    [p.sum(1,2) for _ in range(NUM_CALLS)]
    # parallel(p)
    print('call: %d qps' % (NUM_CALLS / (time.time() - start)))


if __name__ == '__main__':
    p = multiprocessing.Process(target=test_server.main)
    p.start()

    time.sleep(1)

    call()

    p.terminate()
