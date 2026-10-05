/* gcc -std=c99 -O2 -DNO_LIBRAW tests/fringe_checks.c -o build/fringe-checks.exe -lm */
#define main ttc_cropper_main
#include "../ttc-simple.c"
#undef main
#include <assert.h>

static Image make_fixture(void) {
    Image im={160,144,NULL,NULL}; im.data=malloc(160*144*3); assert(im.data); return im;
}
static double step(double x,int blur) {
    if(!blur) return x<80?50:200;
    double t=(x-80)/(double)blur;
    if(t<-1) t=-1; if(t>1) t=1;
    return 125+75*t;
}
static void fill(Image *im,int blur,int offset,int cast,int noise) {
    unsigned rng=41;
    for(int y=0;y<im->height;++y) for(int x=0;x<im->width;++x) for(int c=0;c<3;++c) {
        double v=step(x+(c==0?offset:c==2?-offset:0),blur);
        if(cast) v=c==0?v*.85+10:c==2?v*1.05-5:v;
        rng=1664525u*rng+1013904223u;
        if(noise) v+=(int)((rng>>24)%(2*noise+1))-noise;
        if(v<0)v=0;if(v>255)v=255;
        im->data[((size_t)y*im->width+x)*3+c]=(unsigned char)(v+0.5);
    }
}
static RoiFringe measure(Image *im,Roi *r,int dx,int dy,int accepted) {
    unsigned char *mask=NULL; RoiFringe f=roi_fringe(im,r,dx,dy,&mask);
    printf("%s score=%.5f cast=%.5f noise=%.5f n=%zu baseline=%zu\n",f.status,f.score,f.cast,f.noise,f.pixels,f.baseline);
    assert((mask!=NULL)==accepted);
    if(accepted) {
        size_t edge=0,base=0;
        for(int y=0;y<r->h;++y)for(int x=0;x<r->w;++x) {
            unsigned char *p=mask+((size_t)y*r->w+x)*4;
            if(p[3]==150) { ++edge; assert(p[1]==255 && p[2]==80); }
            else if(p[3]==65) { ++base; assert(p[1]==100 && p[2]==255); }
            else assert(p[3]==0);
            if(x<3||y<3||x>=r->w-3||y>=r->h-3) assert(!p[3]);
        }
        assert(edge==f.pixels && base==f.baseline);
    }
    free(mask); return f;
}
int main(void) {
    Image im=make_fixture();Roi r={0};r.x=16;r.y=8;r.w=128;r.h=128;
    fill(&im,0,0,0,0);assert(measure(&im,&r,0,0,1).score<1e-8);
    fill(&im,4,0,0,0);assert(measure(&im,&r,0,0,1).score<1e-8);
    fill(&im,0,0,1,0);RoiFringe cast=measure(&im,&r,0,0,1);assert(cast.score<1e-6 && cast.cast>1);
    fill(&im,4,0,1,0);assert(measure(&im,&r,0,0,1).score<0.3); /* RGB8 rounding */
    fill(&im,4,1,0,0);double one=measure(&im,&r,0,0,1).score;assert(one>1);
    fill(&im,4,2,0,0);double two=measure(&im,&r,0,0,1).score;assert(two>one*1.5);
    fill(&im,4,2,1,0);assert(measure(&im,&r,0,0,1).score>one);
    fill(&im,0,1,0,0);assert(measure(&im,&r,0,0,1).score>1);
    /* Translation changes coordinates only; source samples and mask match. */
    fill(&im,4,2,0,0);Roi moved=r;moved.x-=3;moved.y+=2;
    RoiFringe shifted=measure(&im,&moved,3,-2,1);assert(fabs(shifted.score-two)<1e-10);
    fill(&im,4,0,0,2);assert(measure(&im,&r,0,0,1).score<0.5);
    fill(&im,4,0,0,18);assert(!strcmp(measure(&im,&r,0,0,0).status,"noise-warning"));
    fill(&im,4,0,0,18);
    for(int y=0;y<144;++y)for(int x=0;x<160;++x) {
        size_t k=((size_t)y*160+x)*3;im.data[k+1]=im.data[k+2]=im.data[k];
    }
    assert(!strcmp(measure(&im,&r,0,0,0).status,"noise-warning"));
    fill(&im,4,2,0,0);
    unsigned char *mask=NULL;
    im.data[((size_t)60*160+80)*3]=255; /* Sparse clipping excluded pixel by pixel. */
    RoiFringe sparse=roi_fringe(&im,&r,0,0,&mask);assert(!strcmp(sparse.status,"accepted"));
    assert(mask[((size_t)(60-r.y)*r.w+80-r.x)*4+3]==0);free(mask);
    /* Horizontal and vertical edges produce the same statistic and counts. */
    fill(&im,4,2,0,0);
    Image transpose={144,160,NULL,NULL};transpose.data=malloc(144*160*3);assert(transpose.data);
    for(int y=0;y<144;++y)for(int x=0;x<160;++x)memcpy(transpose.data+((size_t)x*144+y)*3,im.data+((size_t)y*160+x)*3,3);
    Roi tr=r;tr.x=r.y;tr.y=r.x;
    assert(fabs(measure(&transpose,&tr,0,0,1).score-two)<1e-8);free(transpose.data);
    memset(im.data,128,160*144*3);assert(!strcmp(measure(&im,&r,0,0,0).status,"low-contrast"));
    memset(im.data,5,160*144*3);assert(!strcmp(measure(&im,&r,0,0,0).status,"too-dark"));
    fill(&im,0,0,0,0);for(int y=0;y<144;++y)for(int x=80;x<160;++x)im.data[((size_t)y*160+x)*3]=253;
    assert(!strcmp(measure(&im,&r,0,0,0).status,"clipped"));
    for(int y=0;y<144;++y)for(int x=0;x<160;++x)for(int c=0;c<3;++c)im.data[((size_t)y*160+x)*3+c]=30+x;
    assert(!strcmp(measure(&im,&r,0,0,0).status,"insufficient-edges"));
    for(int y=0;y<144;++y)for(int x=0;x<160;++x)for(int c=0;c<3;++c)im.data[((size_t)y*160+x)*3+c]=x%4<2?50:200;
    assert(!strcmp(measure(&im,&r,0,0,0).status,"insufficient-baseline"));
    moved.x=-1;assert(!strcmp(measure(&im,&moved,0,0,0).status,"invalid-region"));
    /* Fixture for end-to-end service and browser QA: five distinct edge ROIs. */
    Image qa={640,160,NULL,NULL};qa.data=malloc((size_t)640*160*3);assert(qa.data);
    for(int y=0;y<160;++y)for(int x=0;x<640;++x)for(int c=0;c<3;++c) {
        int region=x/128,local=x%128;double v=step(local+16+(c==0?region:c==2?-region:0),4);
        qa.data[((size_t)y*640+x)*3+c]=(unsigned char)(v+0.5);
    }
    assert(stbi_write_png("build/fringe-f4.png",640,160,3,qa.data,640*3));
    for(int y=0;y<160;++y)for(int x=0;x<640;++x)for(int c=0;c<3;++c) {
        int region=x/128,local=x%128;
        int v=region==0?128:region==1?5:region==2?(local<64?40:255):region==3?40+local:(local%4<2?50:200);
        qa.data[((size_t)y*640+x)*3+c]=(unsigned char)v;
    }
    assert(stbi_write_png("build/invalid-f8.png",640,160,3,qa.data,640*3));
    free(qa.data);free(im.data);puts("Fringe checks passed");return 0;
}
