import multiprocessing

import time
import gevent


NUM_CALLS = 50 # 0000
POOL = 100
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
    [p.sum(1, 2) for _ in range(NUM_CALLS)]
    # parallel(p)
    dt = time.time() - start
    print "client: active strems", p.session.stream_count
    print('call: %d qps, dt=%.4f' % (NUM_CALLS / dt, dt))
    # print p.session.close()
    gevent.sleep(1)
    print p.session.stream_count


if __name__ == '__main__':
    try:
        p = multiprocessing.Process(target=test_server.main)
        p.start()
        time.sleep(0.5)
        call()
    finally:
        time.sleep(0.5)
        p.terminate()

