class BrokenPipeError(Exception):
    """
    raises when session is closed.
    """
    pass
    def __repr__(self):
        return "BrokenPipeError(%r)" % self.message

class InvalidProtocolError(Exception):
    pass

class StreamIdOverFlowError(Exception):
    pass

class ReadFrameError(Exception):
    pass

class StreamClosedError(Exception):
    pass
