import gevent
from gevent import socket
from streamux import Session

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol


class RemoteException(Exception):
    pass

rpc = JSONRPCProtocol()
class Proxy:
    def __init__(self, session):
        self.session = session
    def __getattr__(self, name):
        def f(*args, **kwargs):
            request = rpc.create_request(name, args, kwargs)
            stream = self.session.open_stream()
            #$print "opened", stream
            stream.write(request.serialize())
            response = rpc.parse_reply(stream.read())
            stream.close()
            if hasattr(response, 'error'):
                print response.error
                raise RemoteException(response.error)
            return (response.result)
        return f
    def __del__(self):
        self.session.close()

# sock = socket.create_connection(('localhost', 2786))
def create_conn():
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 2786))
    session = Session(sock.makefile('rw'), True)
    p = Proxy(session)
    return p




#=============================================
# import multiprocessing

NUM_CALLS = 1000


# def run_sum_server():
#     import zerorpc

#     class SumServer(object):
#         def sum(self, x, y):
#             return x + y

#     server = zerorpc.Server(SumServer())
#     server.bind("tcp://127.0.0.1:6000")
#     server.run()

def call():
    import time
    p = create_conn()
    start = time.time()
    [p.sum(1,2) for _ in range(NUM_CALLS)]
    print('call: %d qps' % (NUM_CALLS / (time.time() - start)))


if __name__ == '__main__':
    # p = multiprocessing.Process(target=run_sum_server)
    # p.start()

    # time.sleep(1)

    call()

    # p.terminate()
