import argparse
from gpxindex.index import GPXIndex, load_gpx
import os

gpx_type = {"trk", "pt", "reg"}


def add_gpx(gpx_fname: str, gtype: str, index_name: str, reindex: bool = False) -> int:
    full_fname = os.path.abspath(gpx_fname)
    full_index_dirname = os.path.abspath(index_name)
    if gtype not in gpx_type:
        return 0
    files_to_add = list()
    if os.path.isdir(full_fname):
        for fname in os.listdir(full_fname):
            files_to_add.append(f"{full_fname}/{fname}")
    else:
        files_to_add = [full_fname]
    # path, filename = os.path.split(full_fname)
    if gtype not in gpx_type:
        return 0
    index = GPXIndex(full_index_dirname)
    if gtype == "trk":
        for fname in files_to_add:
            index.add_track(fname)
    elif gtype == "pt":
        for fname in files_to_add:
            index.add_points(fname, reindex)
    elif gtype == "reg":
        for fname in files_to_add:
            index.add_region(fname, reindex)
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', help='File/directory name to add to index', required=True)
    parser.add_argument('-i', '--index', help='Index direcrory', required=True)
    parser.add_argument('-t', '--type', choices=("trk", "pt", "reg"), help='Type of file to add to index', required=True)
    parser.add_argument('--reindex', action="store_true", help="Recalc index considering new added files")

    args = parser.parse_args()
    add_gpx(args.filename, args.type, args.index)

    # add_gpx("points/points.gpx", "points", "index00")
    # add_gpx("angara-w", "points", "index00")

