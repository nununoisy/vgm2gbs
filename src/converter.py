from typing import List, Tuple, Optional
from pathlib import Path
from vgm import VGM


_GBS_BANK_SIZE = 0x3FFF
_WAIT_CMD = 0x80
_NEXT_BANK_CMD = 0xA0
_LOOP_CMD = 0xC0
_END_SONG_CMD = 0xD0
_TMA_RATES = [4096, 262144, 65536, 16384]


def convert_vgm_to_engine_format(vgm: VGM) -> Tuple[List[bytes], Optional[int], Optional[int]]:
    command_iter = vgm.commands()
    result: List[bytes] = []
    current_bank = bytearray()
    loop_addr = None
    loop_bank = None

    while True:
        try:
            command = next(command_iter)
        except StopIteration:
            break

        if len(current_bank) + 4 > _GBS_BANK_SIZE:
            current_bank.append(_NEXT_BANK_CMD)
            result.append(bytes(current_bank))
            current_bank = bytearray()

        # print(command)
        match command:
            case ('write', addr, val):
                current_bank.append(addr & 0xFF)
                current_bank.append(val)
            case ('wait', samples):
                frame_count = round(60 * samples / 44100)

                current_bank.append(_WAIT_CMD)
                current_bank.append(frame_count)
            case 'loop-offset':
                loop_addr = 0x4000 + len(current_bank)
                loop_bank = 1 + len(result)
            case 'data-block', dtype, block:
                print(dtype)
                print(block)
                raise NotImplementedError("Data block conversion not supported")
            case _:
                raise RuntimeError("How did we get here?")

    if loop_bank is not None and loop_addr is not None:
        current_bank.append(_LOOP_CMD)
    else:
        current_bank.append(_END_SONG_CMD)

    result.append(bytes(current_bank))
    return result, loop_bank, loop_addr


def _calculate_tma_modulo(tma_rate: int, engine_rate: int) -> int:
    distance = tma_rate / engine_rate
    return 0xFF - int(round(distance))


def _pad_metadata_string(s: str) -> bytes:
    return (s.encode('ascii') + (b"\x00" * 32))[:32]


def generate_gbs(vgm: VGM, engine_rate: int = 60, tma_offset: int = 0) -> bytes:
    banks, loop_bank, loop_addr = convert_vgm_to_engine_format(vgm)

    with Path(__file__).with_name("patch_rom.bin").open("rb") as patch_rom_file:
        patch_rom = bytearray(patch_rom_file.read())
        patch_rom.extend([0] * ((len(banks) + 1) * 0x4000))

    for i, bank in enumerate(banks):
        bank_offset = 0x4000 * (i + 1)
        patch_rom[bank_offset:bank_offset+len(bank)] = bank[:]

    if engine_rate != 60:
        tma_distance = _calculate_tma_modulo(_TMA_RATES[0], engine_rate)
        patch_rom[0x3FFB] = 4
    else:
        tma_distance = 0
        patch_rom[0x3FFB] = 0

    if loop_bank is not None and loop_addr is not None:
        patch_rom[0x3FFC:0x3FFE] = int.to_bytes(loop_addr, 2, 'little')
        patch_rom[0x3FFE:0x4000] = int.to_bytes(loop_bank, 2, 'little')

    patch_rom[0x3FFA] = tma_offset + tma_distance

    gbs = bytearray(b"GBS")
    gbs.append(1)  # Version
    gbs.append(1)  # Song count
    gbs.append(1)  # First song index
    gbs.extend(int.to_bytes(0x3EF0, 2, 'little'))  # LOAD address
    gbs.extend(int.to_bytes(0x3EF0, 2, 'little'))  # INIT address
    gbs.extend(int.to_bytes(0x3F26, 2, 'little'))  # PLAY address
    gbs.extend(int.to_bytes(0xFFFE, 2, 'little'))  # Stack pointer
    gbs.append(patch_rom[0x3FFA])  # TMA
    gbs.append(patch_rom[0x3FFB])  # TAC

    assert len(gbs) == 0x10

    if vgm.gd3_metadata is not None:
        gbs.extend(_pad_metadata_string(vgm.gd3_metadata.track_name))
        gbs.extend(_pad_metadata_string(vgm.gd3_metadata.author))
        gbs.extend(_pad_metadata_string(vgm.gd3_metadata.game_name))
    else:
        gbs.extend(_pad_metadata_string("<?>") * 3)

    assert len(gbs) == 0x70

    gbs.extend(patch_rom[0x3EF0:])

    return bytes(gbs)
