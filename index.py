import hashlib
import os
import sys
sys.path.append(".")

import json
import io

import geopy.distance
import gpxpy
from lxml import etree
from gpxpy.gpx import GPX

from gpxindex.tokens import tokenize, get_wtokens, Seasons
from gpxindex.clib import clib_get_ptokens, clib_get_rtokens
from gpxindex.metric import get_score


# from normalize import is_match_xml_schema

class LoadGpxExtention(Exception):
    pass


def md5_checksum(filepath: str, tail: int = 8) -> str:
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()[-tail:]


def load_gpx(gpx_filename: str) -> GPX:
    with open(gpx_filename, "r", encoding='utf-8') as fgpx:
        gpx = gpxpy.parse(fgpx)
    return gpx


def get_max(a: float, b: float) -> float:
    return a if a > b else b


def get_min(a: float, b: float) -> float:
    return a if a < b else b


def get_sqr_region(pt: tuple, side_size: int) -> tuple:
    d_lat = geopy.distance.geodesic(pt, (pt[0] + 0.01, pt[1])).m
    d_lon = geopy.distance.geodesic(pt, (pt[0], pt[1] + 0.1)).m
    # print(f"{d_lat}m {d_lon}m")
    # 0.1 нужно динамически поднастроить исходя из масштаба
    delta_lat = 0.01 * (side_size / 2.0) / d_lat
    delta_lon = 0.1 * (side_size / 2.0) / d_lon
    return round(pt[0] - delta_lat, 6), round(pt[1] - delta_lon, 6), \
           round(pt[0] + delta_lat, 6), round(pt[1] + delta_lon, 6)


class RegBounds:
    __slots__ = ('min_lat', 'min_lon', 'max_lat', 'max_lon',)

    def reset(self) -> None:
        self.min_lat, self.max_lat = 90.0, -90.0
        self.min_lon, self.max_lon = 180.0, -180.0

    def __init__(self):
        self.reset()

    def recalc(self, lat: float, lon: float) -> None:
        self.min_lat = get_min(self.min_lat, lat)
        self.min_lon = get_min(self.min_lon, lon)
        self.max_lat = get_max(self.max_lat, lat)
        self.max_lon = get_max(self.max_lon, lon)

    def __repr__(self):
        return f"{round(self.min_lat, 6)} {round(self.min_lon, 6)} {round(self.max_lat, 6)} {round(self.max_lon, 6)}"


def get_trk_season(gpx: GPX):
    ms = ('', 'зима', 'зима', 'весна',
          'весна', 'весна', 'лето',
          'лето', 'лето', 'осень',
          'осень', 'осень', 'зима',
          )
    if gpx.waypoints:
        if gpx.waypoints[0].time:
            return ms[gpx.waypoints[0].time.month]
    if gpx.tracks:
        if gpx.has_times():
            return ms[gpx.tracks[0].segments[0].points[0].time.month]
    if gpx.routes:
        if gpx.has_times():
            return ms[gpx.routes[0].points[0].time.month]
    if gpx.time:
        return ms[gpx.time.month]
    else:
        return None


class GPXIndex:

    @property
    def root_dir(self):
        return self.__root_dir

    @property
    def points_dir(self):
        return self.__points_dir

    @property
    def regions_dir(self):
        return self.__regions_dir

    def __init__(self, root_dir):
        self.__root_dir = os.path.abspath(root_dir)
        self.__index_dir = f"{self.__root_dir}/index/"
        self.__wtrie_dir = f"{self.__root_dir}/wtrie/"
        self.__gpx_tracks_dir = f"{self.__root_dir}/dat/tracks/"
        self.__points_dir = f"{self.__root_dir}/dat/points/"
        self.__regions_dir = f"{self.__root_dir}/dat/regions/"

        if not os.path.isdir(self.__root_dir):
            os.makedirs(self.__index_dir)
            os.makedirs(self.__wtrie_dir)
            os.makedirs(self.__gpx_tracks_dir)
            os.makedirs(self.__points_dir)
            os.makedirs(self.__regions_dir)

#        self.__gpx10_xmlschema_doc = etree.parse('gpx10.xsd')
#        self.__gpx10_xmlschema = etree.XMLSchema(self.__gpx10_xmlschema_doc)
#        self.__gpx11_xmlschema_doc = etree.parse('gpx11.xsd')
#        self.__gpx11_xmlschema = etree.XMLSchema(self.__gpx11_xmlschema_doc)

    def __add_to_wtrie(self, fid: str, tokens: list) -> None:
        for token in tokens:
            wtrie_path = '/'.join(list(token[:3]))
            os.makedirs(f"{self.__wtrie_dir}{wtrie_path}", exist_ok=True)
            open(f"{self.__wtrie_dir}{wtrie_path}/{fid}", 'a').close()

    def __get_from_wtrie(self, tokens: list) -> list:
        token_fids = list()
        for token in tokens:
            wtrie_path = '/'.join(list(token[:3]))
            if os.path.isdir(f"{self.__wtrie_dir}{wtrie_path}"):
                for fname in os.listdir(f"{self.__wtrie_dir}{wtrie_path}"):
                    if os.path.isfile(f"{self.__wtrie_dir}{wtrie_path}/{fname}"):
                        token_fids.append(fname)
        return list(set(token_fids))

    def __get_from_json(self, fid: str) -> dict:
        with open(f"{self.__index_dir}{fid}", "r", encoding='utf-8') as ff:
            return json.load(ff)

    def get_ptokens(self, fid: str) -> list:
        return clib_get_ptokens(f"{self.__gpx_tracks_dir}{fid}", self.__points_dir)

    def get_rtokens(self, fid: str) -> list:
        return clib_get_rtokens(f"{self.__gpx_tracks_dir}{fid}", self.__regions_dir)

    def add_gpx_to_data(self, gpx: GPX, fid: str) -> None:
        bounds = RegBounds()
        linesnum = 0

        with io.StringIO() as sbuf:
            for track in gpx.tracks:
                for trkseg in track.segments:
                    linesnum += len(trkseg.points)
                    for trkpoint in trkseg.points:
                        sbuf.write(f"{trkpoint.latitude} {trkpoint.longitude}\n")
                        bounds.recalc(trkpoint.latitude, trkpoint.longitude)
            for route in gpx.routes:
                linesnum += len(route.points)
                for rtept in route.points:
                    sbuf.write(f"{rtept.latitude} {rtept.longitude}\n")
                    bounds.recalc(rtept.latitude, rtept.longitude)
            linesnum += len(gpx.waypoints)
            for wpt in gpx.waypoints:
                sbuf.write(f"{wpt.latitude} {wpt.longitude}\n")
                bounds.recalc(wpt.latitude, wpt.longitude)

            sbuf.seek(0)
            with open(f"{self.__gpx_tracks_dir}{fid}", "w", encoding='utf-8') as fdat:
                fdat.write(f"{linesnum}\n")
                fdat.write(f"{bounds}\n")
                for line in sbuf.readlines():
                    fdat.write(line)

    def add_track(self, gpx_filename: str, gpx_href: str = "https://gpxbaikal.ru/db/my.gpx"):
        # если gpx_href = None - размещаем у себя
        fid = md5_checksum(gpx_filename)
        if os.path.isfile(f"{self.__index_dir}/{fid}"):
            print(f"File {gpx_filename} md5-hash: {fid} exists.")
            return None
        fjson = {"id": fid, "filename": os.path.split(gpx_filename)[1], "url": gpx_href, }

        # fjson.update({"author-tg-id": author_tg_id, "author-tg-name": author_tg_name})
        # fjson.update({"upload-time": upload_time})
        # проверить схему, если не норм - fjson.update({"match-gpx-xml-schema": "False"})
        # else fjson.update({"match-gpx-xml-schema": "True"})
        # is_match_xml_schema
        # fjson.update({"match-gpx-xml-schema": is_match_gpx_xml_schema(?)})

        gpx = load_gpx(gpx_filename)
        fjson.update({"gpx-season": get_trk_season(gpx)})
        self.add_gpx_to_data(gpx, fid)
        fjson.update({"gpx-version": gpx.version})
        if gpx.name:
            fjson.update({"gpx-name": gpx.name})
        if gpx.description:
            fjson.update({"gpx-desc": gpx.description})
        wtokens, wseason = get_wtokens(gpx)
        if len(wtokens):
            self.__add_to_wtrie(fid, wtokens)
            fjson.update({"w-tokens": wtokens})
        ptokens = self.get_ptokens(fid)
        if len(ptokens):
            self.__add_to_wtrie(fid, ptokens)
            fjson.update({"p-tokens": ptokens})
        rtokens = self.get_rtokens(fid)
        if len(rtokens):
            self.__add_to_wtrie(fid, rtokens)
            fjson.update({"r-tokens": rtokens})

        with open(f"{self.__index_dir}/{fid}", "w") as ff:
            json.dump(fjson, ff, sort_keys=False, ensure_ascii=False, indent=3)

        return 1

    def add_gpx_from_buf(self):
        pass

    def add_points(self, points_filepath: str, reindex: bool = False):
        # в сервисе вывод заменить на заполнение json
        try:
            print(f"Adding points {os.path.split(points_filepath)[1]}  ...", end="")
            gpx_points = load_gpx(points_filepath)
            filename = f"{md5_checksum(points_filepath)}"
            with open(f"{self.__points_dir}{filename}", "w", encoding='utf-8') as fdat:
                fdat.write(f"{len(gpx_points.waypoints)}\n")
                for point in gpx_points.waypoints:
                    name_tokens = point.name.split()
                    size = int(name_tokens[0])
                    p_tokens = ' '.join(name_tokens[1:])
                    sqr_region = get_sqr_region((point.latitude, point.longitude), size)
                    fdat.write(f"{sqr_region[0]} {sqr_region[1]} {sqr_region[2]} {sqr_region[3]} {p_tokens}\n")
                print("OK")
        except:
            print("ERROR")

    def add_region(self, region_filepath: str, reindex: bool = False):
        # в сервисе вывод заменить на заполнение json
        try:
            print(f"Adding region {os.path.split(region_filepath)[1]}  ...", end="")
            gpx_region = load_gpx(region_filepath)
            bounds = RegBounds()
            filename = f"{md5_checksum(region_filepath)}"
            with io.StringIO() as sbuf:
                for point in gpx_region.tracks[0].segments[0].points:
                    sbuf.write(f"{point.latitude} {point.longitude}\n")
                    bounds.recalc(point.latitude, point.longitude)
                sbuf.seek(0)
                with open(f"{self.__regions_dir}{filename}", "w", encoding='utf-8') as fdat:
                    fdat.write(f"{len(gpx_region.tracks[0].segments[0].points)}\n")
                    fdat.write(f"0 {gpx_region.tracks[0].name}\n")
                    fdat.write(f"{bounds}\n")
                    for line in sbuf.readlines():
                        fdat.write(line)
            print("OK")
        # except LoadGpxExtention as e:
        except Exception as e:
            print(f"ERROR: {str(e)}")

    def search(self, tokens_str: str):
        search_tokens, season = tokenize(tokens_str)
        # для чистки хвостов из places-токенов
        #
        max_metric = len(search_tokens)
        res_fids = list()
        search_tokens_fids = self.__get_from_wtrie(search_tokens)
        for search_tokens_fid in search_tokens_fids:
            search_fid_data = self.__get_from_json(search_tokens_fid)
            w_score, p_score, r_score = get_score(search_fid_data, search_tokens)
            score = w_score + 3.0 * p_score + 2.0 * r_score
            search_fid_data.update({"score": round(score, 4)})
            # fid_data.pop("w-tokens")
            if score:
                res_fids.append(search_fid_data)
        res_fids = sorted(res_fids, key=lambda d: d['score'], reverse=True)
        if season:
            res_fids = list(filter(lambda p: p["gpx-season"] == season, res_fids))
        res = {"search-str": tokens_str, "search-tokens": search_tokens, "results-number": len(res_fids),
               "search-results": res_fids}
#        print(json.dumps(res, ensure_ascii=False))
        return res

    def geosearch_point(self, lat: float, lon: float):
        pass

    def geosearch_region(self):
        pass


if __name__ == '__main__':
    index = GPXIndex("/var/db/mindex")
    print(index.search("мунку зимой"))
    exit(0)
    for fname in os.listdir("gpxindex/angara-w"):
      gpx_fname = f"gpxindex/angara-w/{fname}"
      gpx_href_fname = f"gpxindex/angara-l/{fname.split('.')[0]}.href"
      with open(gpx_href_fname, "r") as fhref:
          url = fhref.readline().strip('\n')
      print(f"Adding {gpx_fname} ...", end='')
      index.add_track(gpx_fname, url)
      print("OK")
