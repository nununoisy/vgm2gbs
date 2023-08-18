import struct
from typing import Iterator
from gd3 import GD3


class VGM:
    def __init__(self, data: bytes):
        self.data = data

        assert self.data[0:4] == b'Vgm '
        assert self.version >= 0x161

        gd3_offset = self._relative_offset(0x14)
        self.gd3_metadata = GD3(self.data[gd3_offset:])

    def _relative_offset(self, offset: int) -> int:
        return struct.unpack_from('L', self.data, offset)[0] + offset

    @property
    def version(self) -> int:
        return struct.unpack_from('L', self.data, 0x8)[0]

    @property
    def version_string(self) -> str:
        major = self.version >> 8
        minor = self.version & 0xFF

        return f'{major:x}.{minor:02x}'


    @property
    def sample_count(self) -> int:
        return struct.unpack_from('L', self.data, 0x18)[0]

    @property
    def loop_offset(self) -> int:
        return self._relative_offset(0x1C)

    @property
    def loop_samples(self) -> int:
        return struct.unpack_from('L', self.data, 0x20)[0]

    @property
    def lr35902_clock(self) -> int:
        return struct.unpack_from('L', self.data, 0x80)[0]

    def commands(self) -> Iterator[tuple]:
        offset = self._relative_offset(0x34)
        eof = self._relative_offset(0x4)

        while offset < eof:
            if offset == self.loop_offset:
                yield 'loop-offset'

            match self.data[offset]:
                case 0x61:
                    n = struct.unpack_from('H', self.data, offset + 1)[0]
                    offset += 2
                    yield 'wait', n
                case 0x62: yield 'wait', 735
                case 0x63: yield 'wait', 882
                case 0x66: break
                case 0x67:
                    dtype, size = struct.unpack_from('xBL', self.data, offset + 1)
                    offset += 6
                    block = self.data[offset+1:offset+1+size]
                    yield 'data-block', dtype, block
                case 0x70: yield 'wait', 1
                case 0x71: yield 'wait', 2
                case 0x72: yield 'wait', 3
                case 0x73: yield 'wait', 4
                case 0x74: yield 'wait', 5
                case 0x75: yield 'wait', 6
                case 0x76: yield 'wait', 7
                case 0x77: yield 'wait', 8
                case 0x78: yield 'wait', 9
                case 0x79: yield 'wait', 10
                case 0x7A: yield 'wait', 11
                case 0x7B: yield 'wait', 12
                case 0x7C: yield 'wait', 13
                case 0x7D: yield 'wait', 14
                case 0x7E: yield 'wait', 15
                case 0x7F: yield 'wait', 16
                case 0xB3:
                    addr, val = struct.unpack_from('BB', self.data, offset + 1)
                    offset += 2
                    yield 'write', 0xFF10 + addr, val
                case _:
                    raise RuntimeError(f"Unknown VGM command ${self.data[offset]:02X}!")
            offset += 1
