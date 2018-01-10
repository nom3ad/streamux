from struct import Struct

VERSION = 0x01

CMD_SYN = 0x01 # stream open
CMD_FIN = 0x02 # stream close, a.k.a EOF mark
CMD_PSH = 0x03 # data push
CMD_NOP = 0x04 # no operation


# version =b'\x01'

# cmdSYN = b'\x01'  # stream open
# cmdFIN = b'\x02'  # stream close, a.k.a EOF mark
# cmdPSH = b'\x03'  # data push
# cmdNOP = b'\x04'  # no operation

SZ_VERSION = 1
SZ_CMD = 1
SZ_LENGTH = 2
SZ_SID = 4

HEADER_SIZE = SZ_VERSION + SZ_CMD + SZ_LENGTH + SZ_SID
MAX_STREAM_ID = (1 << SZ_SID*8) - 1
# version[1B] | cmd[1B] | length[2B] | stream_id[4B]
header_fmt = Struc(
    '!' # network (= big-endian)	standard size
    'B' # version[1B]
    'B' # cmd[1B]
    'H' # length[2B]
    'L' # stream_id[4B]
)


def upack_header(header):
    """ returns
    version,cmd,length,stream_id
    """
    return header_fmt.unpack(header)
