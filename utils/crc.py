import zlib

def crc32_of_file(path):
    with open(path, "rb") as f:
        return format(zlib.crc32(f.read()) & 0xFFFFFFFF, "08x")
