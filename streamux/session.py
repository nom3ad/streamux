
# verify_config is used to verify the sanity of configuration
import os
import warnings

import gevent
from gevent import sleep
from gevent.event import Event
from gevent.queue import Queue

from .exceptions import *
from .frame import *
from .stream import *


class Session:
    default_accept_backlog = 1024
    deafult_config = {
        'keep_alive_interval': 10,  # Second
        'keep_alive_timeout': 30,  # Second
        'max_frame_size': 4096,
        'max_receive_buffer': 4194304,
    }

    def __init__(self, conn, client, **config):
        self.transport = conn
        self.config = Session.deafult_config.copy()
        self.config.update(config)
        self.verify_config()

        self.bucket = self.config['max_receive_buffer']   # token bucket
        self.bucket_notify_event = Event()

        self.dataReady = False

        self._died = False
        self._streams = {}  # id -> stream
        self.accept_q = Queue()  # of streams
        self.write_q = Queue()

        self.next_stream_id = 1 if client else 0
        gevent.spawn(self.recvLoop)
        gevent.spawn(self.sendLoop)
        gevent.spawn(self.keepalive)

    def verify_config(self):
        config = self.config
        if config['keep_alive_interval'] == 0:
            raise Exception("keep-alive interval must be positive")
        if config['keep_alive_timeout'] < config['keep_alive_interval']:
            raise Exception("keep-alive timeout must be larger than keep-alive interval")
        if config['max_frame_size'] <= 0:
            raise Exception("max frame size must be positive")
        if config['max_frame_size'] > 65535:
            raise Exception("max frame size must not be larger than 65535")
        if config['max_receive_buffer'] <= 0:
            raise Exception("max receive buffer must be positive")

    def __repr__(self):
        return "<Session with %r>" % (self.transport)

    def open_stream(self):
        if self._died:
            raise BrokenPipeError()

        # generate stream id
        self.next_stream_id += 2
        if self.next_stream_id > MAX_STREAM_ID:
            raise StreamIdOverFlowError()

        sid = self.next_stream_id
        stream = Stream(sid, self.config['max_frame_size'], self)
        self.write_frame(sid, CMD_SYN)
        self._streams[sid] = stream
        return stream

    def accept_stream(self, timeout=None):
        if self._died:
            return BrokenPipeError()
        stream = self.accept_q.get(timeout=timeout)
        if not stream:
            raise BrokenPipeError()
        return stream

    def close(self):
        print "@@@ [", os.getpid(), "] closing session"
        if self._died:
            return
        for s in self._streams.values():
            s.session_close()
        self._died = True
        self.bucket_notify_event.set()
        # unblock accept_stream, which raise BrokenPipeError
        # print "sendloop"
        self.accept_q.put(None)
        # exits sendLoop
        self.write_q.put(None)
        self.transport.close()

    @property
    def stream_count(self):
        if self._died:
            return 0
        else:
            return len(self._streams)


    def closed(self):
        # do notcheck transport closed status
        #
        if self._died:
            return True
        return False

    def on_stream_closed(self, sid):
        """ this method is to notify the session that a stream has closed
            returns remaining tokens to the bucket
        """
        # n = self._streams[sid].recycle_tokens()
        # if n > 0:
        #     self.bucket = n
        #     self.bucket_notify_event.set()
        #$print("closing %r" % self._streams[sid])
        del self._streams[sid]

    def on_return_tokens(self, n):
        """
        is called by stream to return token after read
        """
        self.bucket = n
        self.bucket_notify_event.set()


    def _read_frame(self, timeout=None):
        """
        may raise ReadFrameError,InvalidProtocolError, on which recvloop should
        close session and exit
        ReadFrameError can wrap underlying transport errors.
        if session is closed,raise BrokenPipeError, on which recvloop should exit

        returns (stream_id:int, cmd:int, data:bytes)
        """
        try:
            header = self.transport.read(HEADER_SIZE)
            if len(header) != HEADER_SIZE:
                    if self._died:
                        raise BrokenPipeError()
                    else:
                        raise ReadFrameError('could not parse header')
            version, cmd, length, stream_id = upack_header(header)
            # #$print (repr(header)), " => ", (version, cmd, length, stream_id)
            if version != VERSION:
                raise InvalidProtocolError('version doesnot match')
            if length > 0:
                data = self.transport.read(length)
                # #$print "data!!! %r" % data
                if len(data) != length:
                    if self._died:
                        raise BrokenPipeError()
                    # TODO: if self.transport.closed: session.close, raise BrokenPipeError
                    raise ReadFrameError('data length is in sufficient')
                return(stream_id, cmd, data)
            return (stream_id, cmd, '')
        except IOError as oops:
            raise ReadFrameError(repr(oops))
        print "@@@ [", os.getpid(), "] reading frame.."

    def recvLoop(self):
        """
        runs in a coroutine. keeps on reading from underlying transport
        if tokens are available.
        if _read_frame raises InvalidProtocolError or  ReadFrameError,
        close the rouge session and exit coroutine with a waring being raised.
        if got BrokenPipeError, exit coroutine
        raise all unhandled excptions, after closing the  sesssion.
        """
        while not self._died:
            # while self.bucket <= 0:
            #     self.bucket_notify_event.wait()
            #     self.bucket_notify_event.clear()
            try:
                # print "@@@ [", os.getpid(), "] reading frame.."
                sid, cmd, data = self._read_frame()  # block
                # print "@@@ [", os.getpid(), "] readframe ", sid, cmd,len(data)
                self.dataReady = True
                #$print "stream[%d] rcv %s (%r) \n" % ( sid, ['SYN','FIN','PSH','NOP'][cmd-1], data)
                if cmd == CMD_SYN:
                    if sid not in self._streams:
                        stream = Stream(sid, self.config['max_frame_size'], self)
                        self._streams[sid] = stream
                        self.accept_q.put(stream)
                elif cmd == CMD_FIN:
                    if sid in self._streams:
                        stream = self._streams[sid]
                        stream.mark_rst_and_close()
                elif cmd == CMD_PSH:
                    if sid in self._streams:
                        stream = self._streams[sid]
                        stream.pushBytes(data)
                elif cmd == CMD_NOP:
                    pass
                else:
                    raise InvalidProtocolError('invalid commnad %r' % cmd)
            except (InvalidProtocolError, ReadFrameError) as oops:
                # _read_frame was successful, so session is alive but rogue.
                # cant go further with compromised session.
                # note: transport may be dead in situation.
                # TODO warnings.warn('%s is closing due to %r' % (self, oops))
                self.close()
                break
            except BrokenPipeError:
                break
            except:
                self.close()
                raise
        print "@@@ [", os.getpid(), "] exits rcvloop of %r" % self


    def keepalive(self):
        while not self._died:
            sleep(self.config['keep_alive_interval'])
            self.write_frame(0,CMD_NOP)
            self.bucket_notify_event.set() # force a signal to the recvLoop
            if self.dataReady:
                self.dataReady = False
            else:
                # no rcv in keepalive interval
                #$print "no keep alive. seesion closing"
                self.close()
        print "@@@ [", os.getpid(), "] exits keepalive loop of %r" % self

    def sendLoop(self):
        while not self._died:
            # LBL or AFTP?
            item = self.write_q.get()  # block
            if not item:
                break
            sid, cmd, data,ev = item
            try:
                # data: shud be a memoryview
                # ev.oops = None
                if data:
                    frame = header_fmt.pack(VERSION, cmd, len(data), sid) + data.tobytes()
                else:
                    frame = header_fmt.pack(VERSION, cmd, 0, sid)

                self.transport.write(frame)
                self.transport.flush()
                #$print "stream[%d] writes %s (%r) " % (sid, ['SYN','FIN','PSH','NOP'][cmd-1], data and data.tobytes())
            except Exception as oops:
                # ev.oops = oops
                raise
                pass
            finally:
                ev.set()
        print "@@@ [", os.getpid(), "] exits sendloop of %r" % self


    def write_frame(self,sid, cmd):
        # writeFrame writes the frame to the underlying transport
        # and returns the number of bytes written if successful
        ev = Event()
        self.write_q.put(
            (sid, cmd, '',ev)
            )
        ev.wait()
