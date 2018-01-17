from gevent.server import StreamServer
import gevent
from streamux import Session

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc import BadRequestError, RPCBatchRequest
from tinyrpc.dispatch import RPCDispatcher
# the code below is valid for all protocols, not just JSONRPC:

rpc = JSONRPCProtocol()

def handle_incoming_message(data):
    try:
        request = rpc.parse_request(data)
    except BadRequestError as e:
        # request was invalid, directly create response
        response = e.error_respond(e)
    else:
        # we got a valid request
        # the handle_request function is user-defined
        # and returns some form of response
        if hasattr(request, 'create_batch_response'):
            response = request.create_batch_response(
                handle_request(req) for req in request
            )
        else:
            response = handle_request(request)
    # now send the response to the client
    if response != None:
        return response.serialize()


def handle_request(request):
    try:
        # do magic with method, args, kwargs...
        f = dispatch.get_method(request.method)
        result = f(*request.args, **request.kwargs)
        return request.respond(result)
    except Exception as e:
        # for example, a method wasn't found
        return request.error_respond(e)

def stream_handle(stream):
     data = stream.read()
     stream.write(handle_incoming_message(data))
     stream.close()

def listener(socket, address):
    #$print('New connection from %s:%s' % address)
    rfileobj = socket.makefile(mode='rb')
    session = Session(rfileobj, False, keep_alive_interval=100,
                      keep_alive_timeout=100)
    while not session.is_closed():
        stream = session.accept_stream()
        #print "accepted", stream
        gevent.spawn(stream_handle, stream)
    print "server: active strems", session.stream_count
    # session.close()


dispatch = RPCDispatcher()

@dispatch.public
def foo(name):
    return "hello %s" % name

@dispatch.public
def echo(name):
    return name

@dispatch.public
def bar(sec):
    gevent.sleep(sec)
    return sec


@dispatch.public
def sum(a,b):
    return a+b

def main():
    server = StreamServer(('0.0.0.0', 2786), listener)
    server.serve_forever()


if __name__ == '__main__':
    main()
