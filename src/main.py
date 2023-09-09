import argparse
from pathlib import Path
from vgm import VGM
from converter import generate_gbs


def positive_int(v: str) -> int:
    i = int(v)
    if i <= 0:
        raise argparse.ArgumentTypeError(f"Value {i} is not a positive integer.")
    return i


parser = argparse.ArgumentParser(prog='vgm2gbs', description='Game Boy VGM to GBS converter')
parser.add_argument('infile', type=str,
                    help='Input VGM file.')
parser.add_argument('outfile', type=str, nargs='?',
                    help='Output GBS file. Defaults to input file path with .gbs extension')
parser.add_argument('-r', '--rate', type=positive_int, nargs=1, required=False,
                    help='Set the engine rate for songs that run at a rate that is not NTSC.')
parser.add_argument('-t', '--tma-offset', type=int, nargs=1, required=False,
                    help='Set the TMA offset for songs using custom timing.')
parser.add_argument('-ti', type=positive_int, nargs=1, required=False,
                    help='Increase the TMA offset. Compatibility option for Pegmode\'s converter.')
parser.add_argument('-td', type=positive_int, nargs=1, required=False,
                    help='Decrease the TMA offset. Compatibility option for Pegmode\'s converter.')


if __name__ == "__main__":
    args = parser.parse_args()

    in_file = Path(args.infile)

    if args.outfile is None:
        out_file = in_file.with_suffix(".gbs")
    else:
        out_file = Path(args.outfile)

    with in_file.open('rb') as vgm_file:
        vgm = VGM(vgm_file.read())

    engine_rate = 60
    tma_offset = 0

    if args.rate is not None:
        engine_rate = args.rate[0]
    if args.tma_offset is not None:
        tma_offset = args.tma_offset[0]
    if args.ti is not None:
        tma_offset += args.ti[0]
    if args.td is not None:
        tma_offset -= args.td[0]

    print(f'Converting {in_file.name} to {out_file.name}...')
    print(f'Engine rate: {engine_rate} Hz, TMA offset: {tma_offset}')
    print('VGM version:', vgm.version_string)
    if vgm.gd3_metadata is not None:
        print('Track info:', vgm.gd3_metadata.track_info)
    else:
        print('Track info: <none>')
    gbs = generate_gbs(vgm, engine_rate, tma_offset)

    with out_file.open('wb') as gbs_file:
        gbs_file.write(gbs)

    print('Done!')
