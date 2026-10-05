/* Relative rendered-RGB edge chroma, version 1. See docs/color-fringe.md. */
#ifndef TTC_ROI_FRINGE_H
#define TTC_ROI_FRINGE_H

typedef struct {
    const char *status;
    double score, noise, cast, span;
    size_t pixels, baseline;
} RoiFringe;

static int fringe_usable(const Image *im, int x, int y) {
    const unsigned char *p=im->data+((size_t)y*im->width+x)*3;
    return p[0]>4 && p[1]>4 && p[2]>4 && p[0]<251 && p[1]<251 && p[2]<251 && roi_gray(im,x,y)>=0.05;
}
/* Mask is at native ROI size: green=score samples, blue=cast/noise fit samples.
 * It is returned only for accepted measurements. No crop is resampled. */
static RoiFringe roi_fringe(const Image *im,const Roi *r,int dx,int dy,unsigned char **overlay) {
    RoiFringe f={"invalid-region",0,0,0,0,0,0};
    *overlay=NULL;
    if(r->w<8 || r->h<8 || !roi_inside(im,r,dx,dy)) return f;
    size_t n=(size_t)r->w*r->h, hist[256]={0}, clipped=0;
    double mean=0;
    for(int y=0;y<r->h;++y) for(int x=0;x<r->w;++x) {
        int ix=r->x+dx+x,iy=r->y+dy+y;
        double v=roi_gray(im,ix,iy); mean+=v;
        ++hist[(int)(v*255+0.5)];
        const unsigned char *p=im->data+((size_t)iy*im->width+ix)*3;
        if(p[0]<=4 || p[1]<=4 || p[2]<=4 || p[0]>=251 || p[1]>=251 || p[2]>=251) ++clipped;
    }
    if(mean/n<0.05) { f.status="too-dark"; return f; }
    if((double)clipped/n>0.01) { f.status="clipped"; return f; }
    size_t count=0; int lo=-1,hi=255;
    for(int i=0;i<256;++i) {
        count+=hist[i];
        if(lo<0 && count>=(n+19)/20) lo=i;
        if(count>=n-n/20) { hi=i; break; }
    }
    f.span=(hi-lo)/255.0;
    if(f.span<0.15) { f.status="low-contrast"; return f; }
    unsigned char *band=calloc(n,1);
    if(!band) { f.status="allocation-failed"; return f; }
    double threshold=fmax(0.03,0.08*f.span);
    /* Normalized Sobel seeds; a two-pixel Chebyshev dilation covers both sides.
     * Only selection uses a neighborhood. The residual uses original RGB. */
    for(int y=1;y<r->h-1;++y) for(int x=1;x<r->w-1;++x) {
        int ix=r->x+dx+x,iy=r->y+dy+y;
        double gx=0,gy=0;
        for(int j=-1;j<=1;++j) for(int i=-1;i<=1;++i) {
            double v=roi_gray(im,ix+i,iy+j);
            gx+=i*(j==0?2:1)*v/8; gy+=j*(i==0?2:1)*v/8;
        }
        if(hypot(gx,gy)<threshold) continue;
        for(int j=-2;j<=2;++j) for(int i=-2;i<=2;++i)
            if(x+i>=0 && x+i<r->w && y+j>=0 && y+j<r->h) band[(size_t)(y+j)*r->w+x+i]=1;
    }
    double sy=0,syy=0,sc[3]={0},syc[3]={0},a[3],b[3];
    /* Exclude three pixels at the boundary, never sampling outside this ROI. */
    for(int y=3;y<r->h-3;++y) for(int x=3;x<r->w-3;++x) {
        size_t k=(size_t)y*r->w+x;
        int ix=r->x+dx+x,iy=r->y+dy+y;
        if(!fringe_usable(im,ix,iy)) { band[k]=0; continue; }
        if(band[k]) { ++f.pixels; continue; }
        band[k]=2; ++f.baseline;
        double v=roi_gray(im,ix,iy);
        const unsigned char *p=im->data+((size_t)iy*im->width+ix)*3;
        sy+=v; syy+=v*v;
        for(int c=0;c<3;++c) { double z=p[c]/255.0; sc[c]+=z; syc[c]+=v*z; }
    }
    if(f.pixels<32 || (double)f.pixels/n<0.002) f.status="insufficient-edges";
    else if(f.baseline<32 || (double)f.baseline/n<0.1 || syy-sy*sy/f.baseline<0.0025*f.baseline) f.status="insufficient-baseline";
    else {
        double cast2=0;
        for(int c=0;c<3;++c) {
            b[c]=(syc[c]-sy*sc[c]/f.baseline)/(syy-sy*sy/f.baseline);
            a[c]=(sc[c]-b[c]*sy)/f.baseline;
            double d=a[c]+b[c]*0.5-0.5; cast2+=d*d/3;
        }
        f.cast=100*sqrt(cast2);
        double edge2=0,base2=0,lnoise2=0;
        for(int y=3;y<r->h-3;++y) for(int x=3;x<r->w-3;++x) {
            size_t k=(size_t)y*r->w+x;
            if(!band[k]) continue;
            int ix=r->x+dx+x,iy=r->y+dy+y;
            double v=roi_gray(im,ix,iy),residual=0;
            const unsigned char *p=im->data+((size_t)iy*im->width+ix)*3;
            for(int c=0;c<3;++c) { double d=p[c]/255.0-a[c]-b[c]*v; residual+=d*d/3; }
            if(band[k]==1) edge2+=residual;
            else {
                base2+=residual;
                double d=v-(roi_gray(im,ix-1,iy)+roi_gray(im,ix+1,iy)+roi_gray(im,ix,iy-1)+roi_gray(im,ix,iy+1))/4;
                lnoise2+=d*d;
            }
        }
        base2/=f.baseline; f.noise=sqrt(base2);
        if(f.noise>0.015 || sqrt(lnoise2/f.baseline)>0.025) f.status="noise-warning";
        else {
            f.status="accepted";
            f.score=100*sqrt(fmax(0,edge2/f.pixels-base2))/f.span;
            *overlay=calloc(n,4);
            if(!*overlay) f.status="allocation-failed";
            else for(int y=3;y<r->h-3;++y) for(int x=3;x<r->w-3;++x) {
                size_t k=(size_t)y*r->w+x;
                if(band[k]) {
                    (*overlay)[k*4+1]=band[k]==1?255:100;
                    (*overlay)[k*4+2]=band[k]==1?80:255;
                    (*overlay)[k*4+3]=band[k]==1?150:65;
                }
            }
        }
    }
    free(band); return f;
}
#endif
