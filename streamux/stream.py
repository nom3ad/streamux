from gevent.event import Event
from gevent.queue import Queue
from gevent import sleep
from frame import *
from io import BytesIO

class Stream(object):
    def __init__(self, id, framesize, session):
        self._id = id
        self.session = session
        self.framesize = framesize
        self.read_q = Queue()
        self.read_event= Event()
        self.rstflag = False

    def __repr__(self):
        return "<Stream [%d] of %r>" % (self.id, self.session)
    @property
    def  id(self):
        return self._id

    def read(self):
        data = self.read_q.get()
        return data

    def pushBytes(self, data):
        self.read_q.put(data)

    def close(self):
        pass

    def write(self, data):
        sent = 0
        slices = [data]
        for slice in slices:
            ev = Event()
            self.session.write_q.put(
                ((self.id, CMD_PSH, slice ),ev)
                )
            ev.wait()
            # sent +=

    # def split(self, data, cmd):
    #     header = header_fmt.pack(
    #         VERSION,
    #         cmd,
    #         self.id,
    #         len(data)
    #     )
    #     return [header + data]

    def markRST(self):
        self.rstflag = True
