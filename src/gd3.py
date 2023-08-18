import struct


class GD3:
    version: int
    track_name: str
    track_name_orig: str
    game_name: str
    game_name_orig: str
    system_name: str
    system_name_orig: str
    author: str
    author_orig: str
    release_date: str
    ripper: str
    notes: str

    def __init__(self, data: bytes):
        assert data[0:4] == b'Gd3 '
        (self.version, data_length) = struct.unpack_from("LL", data, 4)

        (
            self.track_name,
            self.track_name_orig,
            self.game_name,
            self.game_name_orig,
            self.system_name,
            self.system_name_orig,
            self.author,
            self.author_orig,
            self.release_date,
            self.ripper,
            self.notes
        ) = (
            string.decode('utf-8')
            for string in data[12:12+data_length].decode('utf-16-le').encode('utf-8').split(b'\x00')[:11]
        )

    @property
    def track_info(self) -> str:
        return f'{self.track_name} - {self.author} - {self.game_name} ({self.ripper})'
