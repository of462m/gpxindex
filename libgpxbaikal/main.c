#include <stdio.h>
#include <string.h>
#include <dirent.h>
#define _USE_MATH_DEFINES
#include <math.h>
#include <unistd.h>
#include <malloc.h>
#include "libgpxbaikal.h"

int main(int argc, char *argv[]) {

	FILE *ff;
	DIR* dir;
	struct dirent *dir_ent;
	wpt cpoint,dpoint;
	region reg;
	sqr_region sreg00, sreg01;
	int n;
	char tokens[2048];
	
//	cpoint.lat=51.944190;
//	cpoint.lon=102.376980;
//	52.796294 106.474828 53.014763 106.77184
	dpoint.lat=52.796294;
	dpoint.lon=106.474828;
	cpoint.lat=53.014763;
	cpoint.lon=106.77184;

	printf("%lf\n",geo_distance_m(cpoint,dpoint));

	get_tracks_by_point(cpoint, 1500.0, "/home/gpxbaikal/gpxbot/gindex/dat/tracks", tokens);
	printf("[%s]\n", tokens);

	return 1;

	get_rtokens("/home/taras/gpxbaikal/gpxbot/vindex/dat/regions","03b5a1e8",tokens);
	printf("[%s]\n", tokens);
	return 1;

/*
	dir = opendir("/home/taras");
	while ((dir_ent = readdir(dir))) {
		printf("%s\n",dir_ent->d_name);
	}
*/
	cpoint.lat=51.95099;
	cpoint.lon=102.45566;

	dpoint.lat=51.94419;
	dpoint.lon=102.37698;


	get_sqr_region(cpoint,1000.0,&sreg00);
	get_sqr_region(dpoint,100.0,&sreg01);
//	get_sqr_region(sreg00.min,5000.0,&sreg01);

	is_intersect_sqr(sreg01,sreg00) ? printf("YES\n") : printf("NO\n");

	return 0;

//	ff = fopen("unconvex.dat","r");
	ff = fopen("kbzd.dat","r");
		fscanf(ff,"%i",&reg.n);
		reg.points = (wpt *)malloc(reg.n*sizeof(wpt));
		for(int i=0; i<reg.n; i++)
			fscanf(ff,"%lf %lf", &reg.points[i].lat, &reg.points[i].lon);
		is_wpt_in_region(cpoint,reg) ? printf("in\n") : printf("not in\n");
	fclose(ff);
	free(reg.points);

	return 0;
}
