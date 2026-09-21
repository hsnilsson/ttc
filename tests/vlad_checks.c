/* Native detector checks. Optional argv[1]: independent/local preview PNG.
 * gcc -O2 -DNO_LIBRAW tests/vlad_checks.c -o build/vlad-checks.exe */
#define main ttc_cropper_main
#include "../ttc-simple.c"
#undef main
#include "../vlad_detector.h"
#include <assert.h>
#undef assert
#define assert(x) do { if(!(x)) { fprintf(stderr,"check failed: %s (%d)\n",#x,__LINE__);exit(1); } } while(0)
static Image *blank(int w,int h) {
    Image *im=calloc(1,sizeof(*im));assert(im);
    im->width=w;im->height=h;im->data=malloc((size_t)w*h*3);assert(im->data);
    memset(im->data,100,(size_t)w*h*3);return im;
}
/* A mechanical matcher fixture built from the templates, NOT an independent
 * capture and NOT evidence of recognition generalization. */
static Image *template_fixture(void) {
    Image *im=blank(1600,1066);
    for(int k=0;k<5;k++) {
        double cx=(vlad_boxes[k][0]+vlad_boxes[k][2]/2)*1600/19136.;
        double cy=(vlad_boxes[k][1]+vlad_boxes[k][3]/2)*1066/12752.;
        double span=k?210.:200.;
        for(int y=0;y<1066;y++)for(int x=0;x<1600;x++) {
            double tx=(x-cx)*32/span+15.5,ty=(y-cy)*32/span+15.5;
            if(tx<0||ty<0||tx>=31||ty>=31)continue;
            int ix=(int)tx,iy=(int)ty;double fx=tx-ix,fy=ty-iy;
            const unsigned char *p=vlad_templates[k];
            int v=(int)((1-fy)*((1-fx)*p[iy*32+ix]+fx*p[iy*32+ix+1])+fy*((1-fx)*p[(iy+1)*32+ix]+fx*p[(iy+1)*32+ix+1])+.5);
            for(int c=0;c<3;c++)im->data[((size_t)y*1600+x)*3+c]=(unsigned char)v;
        }
    }return im;
}
static Image *transform(const Image *im,double scale,double angle,double dx,double dy) {
    Image *out=blank(im->width,im->height);double a=angle*.017453292519943295,c=cos(a),s=sin(a);
    for(int y=0;y<out->height;y++)for(int x=0;x<out->width;x++) {
        double xx=x-out->width/2.-dx,yy=y-out->height/2.-dy;
        double sx=(c*xx+s*yy)/scale+im->width/2.,sy=(-s*xx+c*yy)/scale+im->height/2.;
        int ix=(int)floor(sx),iy=(int)floor(sy);double fx=sx-ix,fy=sy-iy;
        if(ix<0||iy<0||ix+1>=im->width||iy+1>=im->height)continue;
        for(int ch=0;ch<3;ch++)out->data[((size_t)y*out->width+x)*3+ch]=(unsigned char)(
            (1-fy)*((1-fx)*im->data[((size_t)iy*im->width+ix)*3+ch]+fx*im->data[((size_t)iy*im->width+ix+1)*3+ch])+
            fy*((1-fx)*im->data[((size_t)(iy+1)*im->width+ix)*3+ch]+fx*im->data[((size_t)(iy+1)*im->width+ix+1)*3+ch])+.5);
    }return out;
}
static void check_transform(const Image *im,double scale,double angle,double dx,double dy) {
    Image *t=transform(im,scale,angle,dx,dy);VladDetection d;
    int accepted=vlad_detect(t,im->width,im->height,&d);
    printf("transform scale %.3f angle %.2f shift %.1f,%.1f: %s NCC %.3f\n",scale,angle,dx,dy,d.status,d.confidence);
    for(int k=0;k<5;k++) {
        double x=(vlad_boxes[k][0]+vlad_boxes[k][2]/2)*im->width/19136.-im->width/2.;
        double y=(vlad_boxes[k][1]+vlad_boxes[k][3]/2)*im->height/12752.-im->height/2.;
        double a=angle*.017453292519943295;
        double ex=scale*(cos(a)*x-sin(a)*y)+im->width/2.+dx;
        double ey=scale*(sin(a)*x+cos(a)*y)+im->height/2.+dy;
        double error=hypot(d.regions[k].x+d.regions[k].width/2.-ex,d.regions[k].y+d.regions[k].height/2.-ey);
        printf(" %s error %.2f status %s NCC %.3f\n",d.regions[k].id,error,d.regions[k].status,d.regions[k].confidence);
        assert(error<im->width*.003);
    }
    assert(accepted);free_image(t);
}
int main(int argc,char **argv) {
    (void)vlad_detect_cli;
    Image *im=blank(1600,1066);VladDetection d;
    assert(!vlad_detect(im,19136,12752,&d));puts("blank rejected");
    unsigned int rng=123;
    for(int mode=0;mode<3;mode++) {
        for(int y=0;y<im->height;y++)for(int x=0;x<im->width;x++) {
            rng=1664525*rng+1013904223;
            int v=mode==0?(int)(rng>>24):mode==1?(((x/4+y/4)%2)*180+30):((x%13<4)?220:30);
            for(int c=0;c<3;c++)im->data[((size_t)y*im->width+x)*3+c]=(unsigned char)v;
        }
        assert(!vlad_detect(im,19136,12752,&d));printf("negative %d rejected NCC %.3f\n",mode,d.confidence);
    }
    assert(!vlad_detect(im,100,100,&d));free_image(im);
    {
        im=argc>1?load_image(argv[1]):template_fixture();assert(im);
        check_transform(im,1,0,0,0);
        check_transform(im,1,0,47,-25);
        check_transform(im,.96,0,8,3);
        check_transform(im,1,2,0,0);
        check_transform(im,.97,-1.5,16,-7);
        if(im->width==1600 && im->height==1066) {
            Image *duplicate=transform(im,1,0,0,0);
            for(int y=332;y<532;y++)for(int x=701;x<901;x++) {
                memcpy(duplicate->data+((size_t)y*1600+x-100)*3,im->data+((size_t)y*1600+x)*3,3);
                memcpy(duplicate->data+((size_t)y*1600+x+100)*3,im->data+((size_t)y*1600+x)*3,3);
            }
            assert(!vlad_detect(duplicate,1600,1066,&d));
            assert(!strcmp(d.regions[0].status,"ambiguous"));
            puts("duplicate center contexts rejected as ambiguous");free_image(duplicate);
        }
        /* Removal of one region must invalidate automatic five-box result. */
        for(int y=350;y<500 && y<im->height;y++)for(int x=680;x<920 && x<im->width;x++)
            memset(im->data+((size_t)y*im->width+x)*3,100,3);
        assert(!vlad_detect(im,im->width,im->height,&d));puts("missing center rejected");free_image(im);
    }
    puts("Vlad detector checks passed");return 0;
}
