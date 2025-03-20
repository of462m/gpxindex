#include <stdio.h>
#include <string.h>
#include <dirent.h>
#define _USE_MATH_DEFINES
#include <math.h>
#include <unistd.h>
#include <malloc.h>
#include "libgpxbaikal.h"

void deg2rad(wpt *wpt) {
	wpt->lat = M_PI*wpt->lat/180.0;
	wpt->lon = M_PI*wpt->lon/180.0;
}

double geo_distance_m(wpt wpt1, wpt wpt2) {
	deg2rad(&wpt1);
	deg2rad(&wpt2);
	return 6371000.0 * acos(sin(wpt1.lat)*sin(wpt2.lat) + cos(wpt1.lat)*cos(wpt2.lat)*cos(wpt1.lon-wpt2.lon));
}

double geo2_distance_m(wpt *wpt1) {
	return geo_distance_m(wpt1[0],wpt1[1]);
}

double d_sign(double x) {
        if (x > 0.0) return 1.0;
        if (x < 0.0) return -1.0;
        return 0.0;
}

void get_vec(wpt a, wpt b, vec *res) {
	res->x = b.lon - a.lon;
	res->y = b.lat - a.lat;
	res->r = sqrt(pow(res->x,2.0) + pow(res->y,2.0));
}

double smult(vec a, vec b) {
	return a.x*b.x + a.y*b.y;
}

double get_dir(vec a,vec b) {
        return d_sign(a.x*b.y - a.y*b.x);
}

double get_phi(vec a, vec b) {
	double arg = smult(a,b) / (a.r*b.r);
	if (fabs(arg) > 1.0) arg = d_sign(arg);
	return get_dir(a,b) * acos(arg);
}

void get_sqr_region(wpt pt, double side, sqr_region *sreg) {
	wpt pt_dlat,pt_dlon;
	pt_dlat.lat = pt.lat+.01;	pt_dlat.lon = pt.lon;
	pt_dlon.lat = pt.lat;		pt_dlon.lon = pt.lon+.1;

	double d_lat = geo_distance_m(pt, pt_dlat);
	double d_lon = geo_distance_m(pt, pt_dlon);

	d_lat = .01 * (.5*side)/d_lat;
	d_lon =  .1 * (.5*side)/d_lon;

	sreg->min.lat = pt.lat - d_lat; sreg->max.lat = pt.lat + d_lat;
	sreg->min.lon = pt.lon - d_lon; sreg->max.lon = pt.lon + d_lon;
}

int is_intersect_sqr(sqr_region sqr01, sqr_region sqr02) {	
	if (sqr01.min.lat > sqr02.max.lat ||
	    sqr02.min.lat > sqr01.max.lat ||
    	    sqr01.min.lon > sqr02.max.lon ||
	    sqr02.min.lon > sqr01.max.lon) return 0;
	return 1;
}

int is_wpt_in_sqr_region(wpt pt,sqr_region sreg) {
	if (pt.lat > sreg.min.lat)
		if (pt.lat < sreg.max.lat)
			if (pt.lon > sreg.min.lon)
				if (pt.lon < sreg.max.lon)
					return 1;
	return 0;
}

int is_trk_in_sqr_region(trk tr,sqr_region sreg) {
	if (!is_intersect_sqr(tr.bounds, sreg)) return 0;
	for (int i=0; i<tr.n; i++) 
		if (is_wpt_in_sqr_region(tr.points[i],sreg))
			return 1;
	return 0;
}

int is_wpt_in_region(wpt pt,region reg) {
	if (!is_wpt_in_sqr_region(pt,reg.bounds)) return 0;
	double angle = 0.0;
	vec v0,v,vnext;

	get_vec(pt,reg.points[0],&v0);
	v = v0;

        for(int i=1; i<reg.n; i++) {
                get_vec(pt,reg.points[i],&vnext);
                angle += get_phi(v,vnext);
		v = vnext;
        }

        angle += get_phi(v,v0);
	if (fabs(angle) < 1.0e-5) return 0;
	return 1;
}

int is_trk_in_region(trk tr,region reg) {
	if (!is_intersect_sqr(tr.bounds,reg.bounds)) return 0;
	for (int i=0; i<tr.n; i++)
		if (is_wpt_in_region(tr.points[i],reg))
			return 1;
	return 0;
}

void print_string(char *s) {
	printf("-----\n%s\n-----\n",s);
}

void fillmeup(char *s) {
	sprintf(s,"%s", "один два несколько");
}

int load_track_bounds(char *fname, sqr_region *bounds) {
	FILE *ftrk;
	int n;

	ftrk = fopen(fname, "r");
		fscanf(ftrk,"%i",&n);	
		fscanf(ftrk,"%lf %lf %lf %lf",&bounds->min.lat, &bounds->min.lon, &bounds->max.lat, &bounds->max.lon);
	fclose(ftrk);
}

int load_track(char *gpxdatafile, trk *track) {
	FILE *fgpx;
	fgpx = fopen(gpxdatafile, "r");
		fscanf(fgpx,"%i",&track->n);
		fscanf(fgpx,"%lf %lf %lf %lf",&track->bounds.min.lat, &track->bounds.min.lon, &track->bounds.max.lat, &track->bounds.max.lon);
		track->points = (wpt *)malloc(track->n*sizeof(wpt));
		for(int i=0; i < track->n; i++) 
			fscanf(fgpx,"%lf %lf", &track->points[i].lat, &track->points[i].lon);
	fclose(fgpx);
	return 1;
}

int load_region(char *regdatafile, region *reg) {
	FILE *freg;
	int chop;
	freg = fopen(regdatafile, "r");
		strcpy(reg->tokens,"");
		fscanf(freg,"%i",&reg->n);
		reg->n -= 1;
		fscanf(freg,"%i %256[^\r\n]",&chop,reg->tokens);
		fscanf(freg,"%lf %lf %lf %lf",&reg->bounds.min.lat, &reg->bounds.min.lon, &reg->bounds.max.lat, &reg->bounds.max.lon);
		reg->points = (wpt *)malloc(reg->n*sizeof(wpt));
		for(int i=0; i < reg->n; i++) 
			fscanf(freg,"%lf %lf", &reg->points[i].lat, &reg->points[i].lon);
	fclose(freg);
	return 1;
}

int get_ptokens(char *pdir, char *gpxdatafile, char *ptokens) {
	DIR *dir;
	FILE *fpoints;
	int i,n;
	struct dirent *dir_ent;
	char fname[2048];
	char tokens[512];
	sqr_region point;
	trk track;

	strcpy(ptokens,"");

	dir = opendir(pdir);		
	if (dir == NULL) return 0;
	load_track(gpxdatafile, &track);
	while ((dir_ent = readdir(dir))) {
		if (strcmp(".",dir_ent->d_name) && strcmp("..",dir_ent->d_name)) {
			sprintf(fname,"%s/%s",pdir,dir_ent->d_name);
			fpoints = fopen(fname, "r");
				fscanf(fpoints,"%i",&n);
				for(i=0; i<n; i++) {
					strcpy(tokens,"");
					fscanf(fpoints,"%lf %lf %lf %lf %255[^\r\n]", &point.min.lat, &point.min.lon, &point.max.lat, &point.max.lon, tokens);
					if (is_trk_in_sqr_region(track,point)) sprintf(ptokens,"%s %s",ptokens,tokens);
				}
			fclose(fpoints);
		}
	}
	free(track.points);
	return 1;
}

int get_rtokens(char *rdir, char *gpxdatafile, char *rtokens) {
        DIR *dir;
        int i,n;
        struct dirent *dir_ent;
        char fname[2048];
        region reg;
        trk track;

        strcpy(rtokens,"");

        dir = opendir(rdir);
        if (dir == NULL) return 0;
        load_track(gpxdatafile, &track);
        while ((dir_ent = readdir(dir))) {
                if (strcmp(".",dir_ent->d_name) && strcmp("..",dir_ent->d_name)) {
                        sprintf(fname,"%s/%s",rdir,dir_ent->d_name);
			load_region(fname, &reg);
			if (is_trk_in_region(track,reg)) sprintf(rtokens,"%s %s",rtokens,reg.tokens);
			free(reg.points);
                }
        }
        free(track.points);
        return 1;
}

int get_tracks_by_point(wpt pt, double nbhood_r, char *tdir, char *fids) {
	DIR *dir;
	struct dirent *dir_ent;
	char fname[2048];
	trk track;
	sqr_region trk_bounds, pt_sqr_nbhood;

	strcpy(fids,"");
	dir = opendir(tdir);
	if (dir == NULL) return 0;
	while ((dir_ent = readdir(dir))) {
		if (strcmp(".",dir_ent->d_name) && strcmp("..",dir_ent->d_name)) {
			sprintf(fname,"%s/%s",tdir,dir_ent->d_name);
			load_track_bounds(fname,&trk_bounds);
			if (is_wpt_in_sqr_region(pt, trk_bounds)) {
				load_track(fname, &track);
				get_sqr_region(pt, nbhood_r, &pt_sqr_nbhood);
				if (is_trk_in_sqr_region(track, pt_sqr_nbhood))
					sprintf(fids,"%s %s",fids,dir_ent->d_name);
			}
		}
	}
}

