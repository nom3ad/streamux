

deafult_config = {
    'KeepAliveInterval': 10,  # Second
    'KeepAliveTimeout': 30,  # Second
    'MaxFrameSize': 4096,
    'MaxReceiveBuffer': 4194304,
}

# VerifyConfig is used to verify the sanity of configuration


def VerifyConfig(config):
    if config['KeepAliveInterval'] == 0:
        raise Exception("keep-alive interval must be positive")
    if config['KeepAliveTimeout'] < config['KeepAliveInterval']:
        raise Exception("keep-alive timeout must be larger than keep-alive interval")
    if config['MaxFrameSize'] <= 0:
        raise Exception("max frame size must be positive")
    if config['MaxFrameSize'] > 65535:
        raise Exception("max frame size must not be larger than 65535")

    if config['MaxReceiveBuffer'] <= 0:
        raise Exception("max receive buffer must be positive")


class Session:
    def __init__(self, socket, **config):
        VerifyConfig(config)
        self._socket = socket
        self.config = deafult_config.copy()
        self.config.update(config)
        self.bucket = 0 # token bucket
        self.nextStreamID = 1 #next stream identifier
        self.dataReady = 0

        
