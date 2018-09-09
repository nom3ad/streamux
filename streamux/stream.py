from gevent.event import Event
from gevent.queue import Queue
from gevent import sleep
from .frame import *
from  .exceptions import *
from io import BytesIO


class Stream(object):
    def __init__(self, id, framesize, session):
        self._id = id
        self._session_died = False
        self.session = session
        self.framesize = framesize
        self.read_q = Queue()
        self._rst_flag = False

    def __repr__(self):
        return "<Stream [%d] of %r>" % (self.id, self.session)

    @property
    def id(self):
        return self._id

    def read(self):
        if self.read_q.empty():
            if self._session_died:
                return BrokenPipeError()
            if self._rst_flag:
                raise StreamClosedError()

        data = self.read_q.get()
        if data is None:  # stream is closed
            if self._session_died:
                raise BrokenPipeError()
            if self._rst_flag:
                raise StreamClosedError()
        return data

    def pushBytes(self, data):
        self.read_q.put(data)

    def close(self):
        if self._session_died:
            raise BrokenPipeError()
        if self._rst_flag:
            return True
        # remove stream info from session, and reclaim tockens
        self.session.on_stream_closed(self.id)
        # # sending cmd_fin via unorthodox way after closing stream.
        self._rst_flag = True
        self.read_q.put(None)
        # send FIN
        self.session.write_frame(self.id, CMD_FIN)
        # # print "closed", self

    def mark_rst_and_close(self):
        # FIN is recieved.
        # print "resetted %r" % self
        self._rst_flag = True
        self.read_q.put(None)
        self.session.on_stream_closed(self.id)

    def session_close(self):
        # print "Session close info to stream"
        self._session_died = True
        self.read_q.put(None)

    def write(self, data):
        if self._session_died:
            raise BrokenPipeError()
        if self._rst_flag:
            raise StreamClosedError()

        data = memoryview(data)
        slices = []
        a=0
        for b in xrange(self.framesize, len(data), self.framesize):
            slices.append(data[a:b])
            a = b
        if a < len(data):
            slices.append(data[a:])

        for slice in slices:
            ev = Event()
            self.session.write_q.put(
                (self.id, CMD_PSH, slice, ev)
            )
            ev.wait()



    def recycle_tokens(self):
        pass
