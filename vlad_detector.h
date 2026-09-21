/* Native content detector for the locally validated Vlad target variant.
 * Include after Image/load_image/free_image. No decoder changes. */
#ifndef TTC_VLAD_DETECTOR_H
#define TTC_VLAD_DETECTOR_H
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "vlad_templates.h"
#define VLAD_COUNT 5
typedef struct {
    const char *id, *status;
    int x,y,width,height;
    double confidence,margin,scale,angle;
} VladRegion;
typedef struct {
    VladRegion regions[VLAD_COUNT];
    int accepted;
    double confidence;
    const char *status;
} VladDetection;
typedef struct { int w,h; float *p; } VladGray;
typedef struct { double x,y,scale,angle,score; } VladPeak;
static const double vlad_boxes[5][4]={{9260,4840,650,650},{2040,1740,880,880},{16380,1930,880,880},{1690,9890,880,880},{16180,10300,880,880}};
static const char *vlad_ids[5]={"center","tl","tr","bl","br"};

static double vlad_pixel(const VladGray *g,double x,double y) {
    int ix=(int)x,iy=(int)y;
    double fx=x-ix,fy=y-iy;
    return (1-fy)*((1-fx)*g->p[iy*g->w+ix]+fx*g->p[iy*g->w+ix+1])+
        fy*((1-fx)*g->p[(iy+1)*g->w+ix]+fx*g->p[(iy+1)*g->w+ix+1]);
}
/* Fixed small processing raster, with area averaging (never used for metrics). */
static int vlad_gray(const Image *im,VladGray *g) {
    g->w=im->width<800?im->width:800;
    g->h=(int)((double)im->height*g->w/im->width);
    if(g->w<320 || g->h<200 || g->h>1600) return 0;
    g->p=malloc((size_t)g->w*g->h*sizeof(float)); if(!g->p)return 0;
    for(int y=0;y<g->h;y++) for(int x=0;x<g->w;x++) {
        int x0=x*im->width/g->w,x1=(x+1)*im->width/g->w;
        int y0=y*im->height/g->h,y1=(y+1)*im->height/g->h;
        double sum=0;int n=0;
        for(int j=y0;j<y1;j++) for(int i=x0;i<x1;i++) {
            const unsigned char *p=im->data+((size_t)j*im->width+i)*3;
            sum+=.2126*p[0]+.7152*p[1]+.0722*p[2];++n;
        }
        g->p[y*g->w+x]=(float)(sum/n);
    }
    return 1;
}
static double vlad_score(const VladGray *g,int k,VladPeak p,int stride) {
    double span=(k?210.:200.)*g->w/1600.*p.scale;
    double a=p.angle*.017453292519943295,c=cos(a)*span/32,s=sin(a)*span/32;
    double bound=(fabs(c)+fabs(s))*15.5;
    if(p.x-bound<0 || p.y-bound<0 || p.x+bound>=g->w-1 || p.y+bound>=g->h-1) return -1;
    double st=0,sv=0,tt=0,vv=0,tv=0;int n=0;
    for(int y=0;y<32;y+=stride) for(int x=0;x<32;x+=stride) {
        double t=vlad_templates[k][y*32+x];
        double v=vlad_pixel(g,p.x+(x-15.5)*c-(y-15.5)*s,p.y+(x-15.5)*s+(y-15.5)*c);
        st+=t;sv+=v;tt+=t*t;vv+=v*v;tv+=t*v;++n;
    }
    tt-=st*st/n;vv-=sv*sv/n;tv-=st*sv/n;
    if(vv/n<4 || tt<=0) return -1;
    return tv/sqrt(tt*vv);
}
static VladPeak vlad_refine(const VladGray *g,int k,VladPeak best) {
    for(int level=0;level<4;level++) {
        double step=1.0/(1<<level),ds=.02/(1<<level),da=1.0/(1<<level);
        for(int repeat=0;repeat<3;repeat++) {
            VladPeak origin=best;
            for(int axis=0;axis<4;axis++) for(int sign=-1;sign<=1;sign+=2) {
                VladPeak p=origin;
                if(axis==0)p.x+=sign*step;
                if(axis==1)p.y+=sign*step;
                if(axis==2)p.scale+=sign*ds;
                if(axis==3)p.angle+=sign*da;
                p.score=vlad_score(g,k,p,1);
                if(p.score>best.score)best=p;
            }
        }
    }
    return best;
}
static int vlad_detect(const Image *im,int full_width,int full_height,VladDetection *out) {
    VladGray g={0}; memset(out,0,sizeof(*out));
    out->status="manual-required";
    if(!im || !im->data || im->width<=0 || im->height<=0 || full_width<320 || full_height<200 || full_width>1000000 || full_height>1000000 ||
       fabs((double)im->width/im->height-(double)full_width/full_height)>.01 || !vlad_gray(im,&g))return 0;
    out->accepted=1;out->confidence=1;
    for(int k=0;k<5;k++) {
        double cx=(vlad_boxes[k][0]+vlad_boxes[k][2]/2)*g.w/19136.;
        double cy=(vlad_boxes[k][1]+vlad_boxes[k][3]/2)*g.h/12752.;
        VladPeak best={cx,cy,1,0,-1},second=best;
        /* Retain spatially distinct candidates; scale/angle variants of the
         * same physical feature do not count as competing detections. */
        VladPeak peaks[12];for(int j=0;j<12;j++)peaks[j]=best;
        for(int y=(int)(cy-g.h*.12);y<=cy+g.h*.12;y+=3)
        for(int x=(int)(cx-g.w*.12);x<=cx+g.w*.12;x+=3)
        for(int si=-1;si<=1;si++) for(int ai=-1;ai<=1;ai++) {
            VladPeak p={(double)x,(double)y,1+si*.08,ai*3.,0};p.score=vlad_score(&g,k,p,2);
            if(p.score>peaks[11].score) {
                int at=11;while(at>0 && p.score>peaks[at-1].score){peaks[at]=peaks[at-1];--at;}peaks[at]=p;
            }
        }
        for(int j=0;j<12;j++) {
            VladPeak p=peaks[j];p.score=vlad_score(&g,k,p,1);p=vlad_refine(&g,k,p);
            if(p.score>best.score)best=p;
        }
        /* Refine competing peaks too: comparing a subpixel optimum with only
         * coarse samples would incorrectly accept duplicate target patches. */
        for(int j=0;j<12;j++)peaks[j]=second;
        for(int y=(int)(cy-g.h*.12);y<=cy+g.h*.12;y+=3)
        for(int x=(int)(cx-g.w*.12);x<=cx+g.w*.12;x+=3) {
            if(hypot(x-best.x,y-best.y)<10)continue;
            VladPeak p={(double)x,(double)y,best.scale,best.angle,0};p.score=vlad_score(&g,k,p,2);
            if(p.score>peaks[11].score) {
                int at=11;while(at>0 && p.score>peaks[at-1].score){peaks[at]=peaks[at-1];--at;}peaks[at]=p;
            }
        }
        for(int j=0;j<12;j++) {
            VladPeak p=peaks[j];p.score=vlad_score(&g,k,p,1);p=vlad_refine(&g,k,p);
            if(hypot(p.x-best.x,p.y-best.y)>=10 && p.score>second.score)second=p;
        }
        VladRegion *r=&out->regions[k];r->id=vlad_ids[k];r->confidence=fmax(0,best.score);r->margin=best.score-second.score;r->scale=best.scale;r->angle=best.angle;
        r->width=(int)floor(vlad_boxes[k][2]*full_width/19136.*best.scale+.5);
        r->height=(int)floor(vlad_boxes[k][3]*full_height/12752.*best.scale+.5);
        r->x=(int)floor(best.x*full_width/g.w-r->width/2.+.5);
        r->y=(int)floor(best.y*full_height/g.h-r->height/2.+.5);
        r->status="accepted";
        if(best.score<.78)r->status="low-correlation";
        else if(r->margin<.10)r->status="ambiguous";
        else if(best.scale<.88 || best.scale>1.12 || fabs(best.angle)>4.5)r->status="geometry-limit";
        else if(fabs(best.x-cx)>g.w*.115 || fabs(best.y-cy)>g.h*.115)r->status="search-limit";
        else if(r->x<0 || r->y<0 || r->x+r->width>full_width || r->y+r->height>full_height)r->status="out-of-bounds";
        if(strcmp(r->status,"accepted"))out->accepted=0;
        if(r->confidence<out->confidence)out->confidence=r->confidence;
    }
    free(g.p);if(out->accepted)out->status="accepted";return out->accepted;
}
static void vlad_json_regions(const VladDetection *d) {
    for(int k=0;k<5;k++) {
        const VladRegion *r=&d->regions[k];
        printf("%s{\"id\":\"%s\",\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d,\"confidence\":%.6f,\"margin\":%.6f,\"scale\":%.6f,\"angle\":%.4f,\"status\":\"%s\"}",k?",":"",r->id?r->id:vlad_ids[k],r->x,r->y,r->width,r->height,r->confidence,r->margin,r->scale,r->angle,r->status?r->status:"invalid-input");
    }
}
static int vlad_detect_cli(int argc,char **argv) {
    if(argc!=5){fprintf(stderr,"Usage: --detect-preview PREVIEW WIDTH HEIGHT\n");return 1;}
    char *ew,*eh;long w=strtol(argv[3],&ew,10),h=strtol(argv[4],&eh,10);
    if(*ew || *eh || w<1 || h<1 || w>1000000 || h>1000000)return 1;
    Image *im=load_image(argv[2]);if(!im)return 1;
    VladDetection d;vlad_detect(im,(int)w,(int)h,&d);free_image(im);
    printf("{\"status\":\"%s\",\"confidence\":%.6f,\"rois\":[",d.status,d.confidence);
    if(d.accepted)vlad_json_regions(&d);
    printf("],\"candidates\":[");vlad_json_regions(&d);
    printf("],\"warnings\":[\"Template-specific heuristic confidence, not a probability; inspect and edit all five boxes.\"%s]}\n",d.accepted?"":",\"Automatic recognition failed; manual five-region selection is required.\"");
    return 0; /* A valid detection response can report manual-required. */
}
#endif
