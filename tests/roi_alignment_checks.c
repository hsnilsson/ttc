#define main ttc_cropper_main
#include "../ttc-simple.c"
#undef main
#include "../roi_display_alignment.h"
#define CHECK(x) do {if(!(x)){fprintf(stderr,"Failed %s line %d\n",#x,__LINE__);return 1;}}while(0)
static Image *pattern(double dx,double dy) {
    Image *im=calloc(1,sizeof(*im));im->width=320;im->height=300;im->data=malloc(320*300*3);
    for(int y=0;y<300;y++)for(int x=0;x<320;x++) {
        double xx=x-dx,yy=y-dy;
        int v=(int)(120+23*sin(.12*xx+.04*yy)+20*cos(.075*xx-.14*yy)+23*sin(.21*xx+.19*yy)+15*cos(.033*xx+.027*yy));
        for(int c=0;c<3;c++)im->data[(y*320+x)*3+c]=(unsigned char)v;
    }return im;
}
int main(void) {
    Image *ref=pattern(0,0);Roi r={0};r.x=80;r.y=80;r.w=160;r.h=140;roi_reference(&r,ref,8);
    const double shifts[][2]={{2.3,-1.25},{-.35,.4},{0,0},{3,-2}};
    for(int i=0;i<4;i++) {
        Image *im=pattern(shifts[i][0],shifts[i][1]);RoiMatch m=roi_track(im,&r,8);
        CHECK(!strcmp(m.status,"tracked"));RoiDisplayAlignment a=roi_display_alignment(im,&r,m);
        printf("known %.2f %.2f integer %d %d subpixel %.4f %.4f\n",shifts[i][0],shifts[i][1],m.dx,m.dy,a.dx,a.dy);
        CHECK(a.refined);CHECK(fabs(a.dx-shifts[i][0])<.15);CHECK(fabs(a.dy-shifts[i][1])<.15);
        m.status="tracking-ambiguous";CHECK(!roi_display_alignment(im,&r,m).refined);free_image(im);
    }
    free_image(ref);puts("Display alignment checks passed");return 0;
}
