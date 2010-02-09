import zlib

crc32 = lambda x: zlib.crc32(x) & 0xffffffff
