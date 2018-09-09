class BrokenPipeError(Exception):
    """
    raises when session is closed.
    """
    pass


class InvalidProtocolError(Exception):
    pass

class StreamIdOverFlowError(Exception):
    pass

class ReadFrameError(Exception):
    pass

class StreamClosedError(Exception):
    pass
