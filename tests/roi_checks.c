/* Run: gcc -O2 -DNO_LIBRAW tests/roi_checks.c -o build/roi-checks -lm */
#define main ttc_cropper_main
#include "../ttc-simple.c"
#undef main
#include <assert.h>

static Image fixture(int w,int h) {
    Image im={w,h,NULL,NULL};
    im.data=malloc((size_t)w*h*3); assert(im.data); return im;
}
static void gray(Image *im,int x,int y,int v) {
    unsigned char *p=im->data+((size_t)y*im->width+x)*3;
    p[0]=p[1]=p[2]=(unsigned char)v;
}
static Image box_blur(const Image *im,int radius) {
    Image out=fixture(im->width,im->height);
    for(int y=0;y<im->height;++y) for(int x=0;x<im->width;++x) {
        int sum=0,count=0;
        for(int j=-radius;j<=radius;++j) for(int i=-radius;i<=radius;++i) {
            int xx=x+i,yy=y+j;
            if(xx>=0 && xx<im->width && yy>=0 && yy<im->height) {
                sum+=im->data[((size_t)yy*im->width+xx)*3]; ++count;
            }
        }
        gray(&out,x,y,(sum+count/2)/count);
    }
    return out;
}
static void fresh_output(char *path,size_t size) {
    static int serial=0;
    struct stat info;
    do { snprintf(path,size,"build/roi-cli-%d",++serial); } while(stat(path,&info)==0);
}
static void check_csv(const char *dir,int rows) {
    char path[256],line[2048];snprintf(path,sizeof path,"%s/report.csv",dir);
    FILE *f=fopen(path,"r");assert(f);int count=0;
    while(fgets(line,sizeof line,f)) {
        int commas=0;for(char *p=line;*p;++p) if(*p==',')++commas;
        assert(commas==16);++count;
    }
    assert(count==rows+1);fclose(f);
}
int main(void) {
    Image im=fixture(160,144),scaled=fixture(160,144),shifted=fixture(160,144);
    Roi r={0}; strcpy(r.name,"center"); r.x=40;r.y=40;r.w=64;r.h=64;
    for(int y=0;y<im.height;++y) for(int x=0;x<im.width;++x) {
        int v=64+(int)(24*sin(x*0.43)+20*cos(y*0.37));
        gray(&im,x,y,v); gray(&scaled,x,y,2*v);
    }
    RoiMetrics a=roi_measure(&im,&r,0,0),b=roi_measure(&scaled,&r,0,0);
    assert(fabs(a.sharpness-b.sharpness)<1e-10);
    assert(fabs(a.contrast-b.contrast)<1e-10);
    Image blur=box_blur(&im,2),blur2=box_blur(&im,4);
    RoiMetrics c=roi_measure(&blur,&r,0,0),d=roi_measure(&blur2,&r,0,0);
    assert(c.sharpness<a.sharpness && d.sharpness<c.sharpness);
    assert(c.contrast<a.contrast && d.contrast<c.contrast);
    /* Noise can raise the proxy; this is a documented limitation, not detail. */
    Image noisy=fixture(160,144);
    for(int y=0;y<im.height;++y) for(int x=0;x<im.width;++x) {
        int v=im.data[((size_t)y*im.width+x)*3]+(((x+y)%2)?8:-8);
        gray(&noisy,x,y,v);
    }
    assert(roi_measure(&noisy,&r,0,0).sharpness>a.sharpness);
    /* Nonperiodic texture for unique alignment. */
    unsigned state=129;
    for(int y=0;y<im.height;++y) for(int x=0;x<im.width;++x) {
        state=1664525u*state+1013904223u;
        gray(&im,x,y,40+(int)((state>>24)%150));
    }
    roi_reference(&r,&im,8);
    RoiMatch m=roi_track(&im,&r,8);
    assert(!strcmp(m.status,"tracked") && m.dx==0 && m.dy==0);
    memset(shifted.data,80,(size_t)shifted.width*shifted.height*3);
    for(int y=0;y<im.height-3;++y) for(int x=5;x<im.width;++x)
        memcpy(shifted.data+((size_t)(y+3)*im.width+x-5)*3,im.data+((size_t)y*im.width+x)*3,3);
    m=roi_track(&shifted,&r,8);
    assert(!strcmp(m.status,"tracked") && m.dx==-5 && m.dy==3);
    m=roi_track(&shifted,&r,5);
    assert(!strcmp(m.status,"tracking-boundary"));
    Roi edge=r;edge.x=0;
    roi_reference(&edge,&im,8);m=roi_track(&shifted,&edge,8);
    assert(!strcmp(m.status,"tracking-out-of-bounds") && m.dx==-5 && m.dy==3);
    for(int y=0;y<im.height;++y) for(int x=0;x<im.width;++x) gray(&im,x,y,(x%4<2)?70:150);
    roi_reference(&r,&im,8); m=roi_track(&im,&r,8);
    assert(strcmp(m.status,"tracked"));
    memset(im.data,128,(size_t)im.width*im.height*3);
    roi_reference(&r,&im,8); m=roi_track(&im,&r,8);
    assert(!strcmp(m.status,"tracking-flat"));
    a=roi_measure(&im,&r,0,0); assert(a.sharpness==0 && a.contrast==0 && a.clipped==0);
    memset(im.data,255,(size_t)im.width*im.height*3);
    a=roi_measure(&im,&r,0,0); assert(a.clipped==1);
    assert(roi_inside(&im,&r,0,0)); assert(!roi_inside(&im,&r,-100,0));
    assert(stbi_write_png("build/roi-fixture.png",blur.width,blur.height,3,blur.data,blur.width*3));
    FILE *f=fopen("build/roi-fixture.conf","w");assert(f);
    fputs("\xef\xbb\xbf# synthetic coordinates\nimage 160 144\ncenter 40 40 64 64\n",f);fclose(f);
    Roi parsed[ROI_MAX];int w=0,h=0;
    assert(roi_config("build/roi-fixture.conf",parsed,&w,&h)==1 && w==160 && h==144);
    f=fopen("build/roi-invalid.conf","w");assert(f);
    fputs("image 160 144\ncenter 100 40 64 64\n",f);fclose(f);
    assert(roi_config("build/roi-invalid.conf",parsed,&w,&h)==-1);
    f=fopen("build/roi-duplicate.conf","w");assert(f);
    fputs("image 160 144\ncenter 40 40 64 64\ncenter 40 40 64 64\n",f);fclose(f);
    assert(roi_config("build/roi-duplicate.conf",parsed,&w,&h)==-1);
    f=fopen("build/roi-overflow.conf","w");assert(f);
    fputs("image 160 144\ncenter 99999999999999999999999999999999 40 64 64\n",f);fclose(f);
    assert(roi_config("build/roi-overflow.conf",parsed,&w,&h)==-1);
    char out[128];fresh_output(out,sizeof out);
    char *valid[]={"ttc","--analyze","build/roi-fixture.conf",out,"build/roi-fixture.png"};
    assert(roi_cli(5,valid)==0);check_csv(out,1);
    assert(roi_cli(5,valid)==1); /* Never overwrite an existing report. */
    fresh_output(out,sizeof out);
    char *missing[]={"ttc","--analyze","build/roi-fixture.conf",out,"build/no-such-input.png","build/roi-fixture.png"};
    assert(roi_cli(6,missing)==2);check_csv(out,2);
    Image small=fixture(8,8);memset(small.data,80,8*8*3);
    assert(stbi_write_png("build/roi-small.png",8,8,3,small.data,24));free(small.data);
    fresh_output(out,sizeof out);
    char *dimensions[]={"ttc","--analyze","build/roi-fixture.conf",out,"build/roi-fixture.png","build/roi-small.png"};
    assert(roi_cli(6,dimensions)==2);check_csv(out,2);
    fresh_output(out,sizeof out);
    char *badtrack[]={"ttc","--analyze","build/roi-fixture.conf",out,"--track","9000000000000000000000000","build/roi-fixture.png"};
    assert(roi_cli(7,badtrack)==1);
    /* Flat row produces no invented reference score. */
    assert(stbi_write_png("build/roi-flat.png",im.width,im.height,3,im.data,im.width*3));
    fresh_output(out,sizeof out);
    char *flat[]={"ttc","--analyze","build/roi-fixture.conf",out,"build/roi-flat.png","build/roi-fixture.png"};
    assert(roi_cli(6,flat)==2);check_csv(out,2);
    free(im.data);free(scaled.data);free(shifted.data);free(blur.data);free(blur2.data);free(noisy.data);
    puts("ROI checks passed: exposure, progressive blur, translation, ambiguity, flatness, clipping, bounds, config.");
    return 0;
}
