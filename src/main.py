import argparse
from pathlib import Path
from vgm import VGM
from converter import generate_gbs


parser = argparse.ArgumentParser(prog='vgm2gbs', description='Game Boy VGM to GBS converter')
parser.add_argument('infile', type=str)
parser.add_argument('outfile', type=str, nargs='?')


if __name__ == "__main__":
    args = parser.parse_args()

    in_file = Path(args.infile)

    if args.outfile is None:
        out_file = in_file.with_suffix(".gbs")
    else:
        out_file = Path(args.outfile)

    with in_file.open('rb') as vgm_file:
        vgm = VGM(vgm_file.read())

    print(f'Converting {in_file.name} to {out_file.name}...')
    print('VGM version:', vgm.version_string)
    if vgm.gd3_metadata is not None:
        print('Track info:', vgm.gd3_metadata.track_info)
    else:
        print('Track info: <none>')
    gbs = generate_gbs(vgm)

    with out_file.open('wb') as gbs_file:
        gbs_file.write(gbs)

    print('Done!')
