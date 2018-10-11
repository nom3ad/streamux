from gevent.event import Event
from gevent.queue import Queue
from gevent import sleep
from frame import *
from  exceptions import *
from io import BytesIO


class Stream(object):
    def __init__(self, id, framesize, session):
        self._id = id
        self._died = False
        self.session = session
        self.framesize = framesize
        self.read_q = Queue()
        self.read_event = Event()
        self.rstflag = False

    def __repr__(self):
        return "<Stream [%d] of %r>" % (self.id, self.session)

    @property
    def id(self):
        return self._id

    def read(self):
        if self._died:
            return BrokenPipeError()
        if self.read_q.empty and self.rstflag:
            raise EOFError()
        data = self.read_q.get()
        return data

    def pushBytes(self, data):
        self.read_q.put(data)

    def close(self):
        if self._died:
            BrokenPipeError()
        self.session.on_stream_closed(self.id)
        # sending cmd_fin via unorthodox way after closing stream.
        self.session.write_frame(self.id, CMD_FIN)

    def session_close(self):
        self._died = True

    def write(self, data):
        if self._died:
            raise BrokenPipeError()

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
                ((self.id, CMD_PSH, slice), ev)
            )
            ev.wait()

    def mark_rst(self):
        #$print "resetted %r" % self
        self.rstflag = True

    def recycle_tokens(self):
        pass
