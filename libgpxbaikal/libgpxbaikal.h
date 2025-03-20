#ifndef _LIBGPXBAIKAL_H_
#define _LIBGPXBAIKAL_H_

typedef struct {
	double x;
	double y;
	double r;
} vec;

typedef struct {
	double lat;
	double lon;
//	double ele;
//	int time;
} wpt;

typedef struct {
	wpt min; // (min.lat,min.lon)
	wpt max; // (max.lat,max.lon)
} sqr_region;

typedef struct {
	int n;
	sqr_region bounds;
	wpt *points;
} trk;

typedef struct {
	int n;
	sqr_region bounds;
	wpt *points;
	char tokens[512];
} region;
/*
REGION FILE FORMAT:
n - size of region array
0 token1 token2 token3 - tokens
min.lat min.lon max.lat max.lon - bounds
lat lon
lat lon
...
lat lon
*/

double geo_distance_m(wpt wpt1, wpt wpt2);
double geo2_distance_m(wpt *wpt1);

double d_sign(double x);
void deg2rad(wpt *wpt);

void get_vec(wpt a, wpt b, vec *res);
double smult(vec a, vec b);
double get_dir(vec a,vec b);
double get_phi(vec a, vec b);

void get_sqr_region(wpt pt, double side, sqr_region *sreg);

int is_intersect_sqr(sqr_region sqr01, sqr_region sqr02);
int is_wpt_in_sqr_region(wpt pt, sqr_region sreg);
int is_wpt_in_region(wpt pt, region reg);

int is_trk_in_sqr_region(trk tr, sqr_region sreg);
int is_trk_in_region(trk tr, region reg);

void print_string(char *s);
void fillmeup(char *s);

int load_track(char *gpxdatafile, trk *track);
int load_region(char *regdatafile, region *reg);

int get_ptokens(char *pdir, char *gpxdatafile, char *ptokens);
int get_rtokens(char *rdir, char *gpxdatafile, char *rtokens);

int get_tracks_by_point(wpt pt, double nbhood_r, char *tdir, char *fids);

#endif /* !_LIBGPXBAIKAL_H_ */
