from struct import Struct

version = 0x01

cmdSYN = 0x01 # stream open
cmdFIN = 0x02 # stream close, a.k.a EOF mark
cmdPSH = 0x02 # data push
cmdNOP = 0x03 # no operation


# version =b'\x01'

# cmdSYN = b'\x01'  # stream open
# cmdFIN = b'\x02'  # stream close, a.k.a EOF mark
# cmdPSH = b'\x03'  # data push
# cmdNOP = b'\x04'  # no operation

sizeOfVer    = 1
sizeOfCmd    = 1
sizeOfLength = 2
sizeOfSid    = 4
headerSize   = sizeOfVer + sizeOfCmd + sizeOfSid + sizeOfLength

# version[1B] | cmd[1B] | length[2B] | stream_id[4B]
header_fmt = Struct(
    '!' # network (= big-endian)	standard size
    'B' # version[1B]
    'B' # cmd[1B]
    'H' # length[2B]
    'L' # stream_id[4B]
)


def upack_header(frame):
    """ returns 
    version,cmd,length,stream_id
    """
    return header_fmt.unpack(frame[:8])
