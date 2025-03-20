import ctypes

clib = ctypes.CDLL('/usr/lib/libgpxbaikal.so')


class wpt(ctypes.Structure):
    _fields_ = [('lat', ctypes.c_double),
                ('lon', ctypes.c_double),
                ]


def clib_get_ptokens(gpxdatafile: str, pdir: str) -> list:
    clib.get_ptokens.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    arg_pdir = pdir.encode('utf-8')
    arg_gpxdatafile = gpxdatafile.encode('utf-8')
    arg_ptokens = (ctypes.c_char * 256)()
    clib.get_ptokens(arg_pdir, arg_gpxdatafile, arg_ptokens)
    return arg_ptokens.value.decode('utf-8').split()


def clib_get_rtokens(gpxdatafile: str, rdir: str) -> list:
    clib.get_rtokens.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    arg_rdir = rdir.encode('utf-8')
    arg_gpxdatafile = gpxdatafile.encode('utf-8')
    arg_rtokens = (ctypes.c_char * 256)()
    clib.get_rtokens(arg_rdir, arg_gpxdatafile, arg_rtokens)
    return arg_rtokens.value.decode('utf-8').split()


def get_tracks_by_point(tracks_dir: str, lat: float, lon: float, pt_nbhood_r: float = 150.0) -> list:
    # int get_tracks_by_point(wpt pt, double nbhood_r, char *tdir, char *fids);
    clib.get_tracks_by_point.argtypes = [wpt, ctypes.c_double, ctypes.c_char_p, ctypes.c_char_p]
    clib.get_tracks_by_point.restype = ctypes.c_int
    arg_pt = wpt(lat, lon)
    arg_tdir = tracks_dir.encode('utf-8')
    arg_fids = (ctypes.c_char * 256)()
    clib.get_tracks_by_point(arg_pt, pt_nbhood_r, arg_tdir, arg_fids)
    return arg_fids.value.decode('utf-8').split()


if __name__ == '__main__':
    print(get_tracks_by_point("...", 51.944190, 102.376980))
    pass
