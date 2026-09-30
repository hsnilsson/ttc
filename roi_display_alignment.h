/* Optional display-only subpixel estimate. Include after roi_analysis.h.
 * Original integer RoiMatch and all metric pixels remain unchanged. */
#ifndef TTC_ROI_DISPLAY_ALIGNMENT_H
#define TTC_ROI_DISPLAY_ALIGNMENT_H
typedef struct { double dx,dy; int refined; const char *status; } RoiDisplayAlignment;
static double roi_alignment_score(const Image *im,const Roi *r,int dx,int dy) {
    double sum=0,squares=0,cross=0;
    for(int i=0;i<r->n;i++) {
        int x=r->sx[i]+dx,y=r->sy[i]+dy;
        if(x<1||y<1||x>=im->width-1||y>=im->height-1)return -2;
        double v=roi_smooth(im,x,y);sum+=v;squares+=v*v;cross+=v*r->ref[i];
    }
    double energy=squares-sum*sum/r->n;
    return energy>0 && r->ref_energy>0?cross/sqrt(energy*r->ref_energy):-2;
}
static RoiDisplayAlignment roi_display_alignment(const Image *im,const Roi *r,RoiMatch match) {
    RoiDisplayAlignment a={(double)match.dx,(double)match.dy,0,"integer-only"};
    if(strcmp(match.status,"tracked") || r->n<1)return a;
    double c=roi_alignment_score(im,r,match.dx,match.dy);
    double left=roi_alignment_score(im,r,match.dx-1,match.dy),right=roi_alignment_score(im,r,match.dx+1,match.dy);
    double up=roi_alignment_score(im,r,match.dx,match.dy-1),down=roi_alignment_score(im,r,match.dx,match.dy+1);
    if(left<-1||right<-1||up<-1||down<-1)return a;
    double hx=left-2*c+right,hy=up-2*c+down;
    if(hx>=-1e-6||hy>=-1e-6)return a;
    double ul=roi_alignment_score(im,r,match.dx-1,match.dy-1),ur=roi_alignment_score(im,r,match.dx+1,match.dy-1);
    double dl=roi_alignment_score(im,r,match.dx-1,match.dy+1),dr=roi_alignment_score(im,r,match.dx+1,match.dy+1);
    if(ul<-1||ur<-1||dl<-1||dr<-1)return a;
    double hxy=(dr-dl-ur+ul)/4,det=hx*hy-hxy*hxy;
    if(det<1e-10)return a;
    double gx=(right-left)/2,gy=(down-up)/2;
    double fx=(-hy*gx+hxy*gy)/det,fy=(hxy*gx-hx*gy)/det;
    if(fabs(fx)>.5 || fabs(fy)>.5)return a;
    a.dx+=fx;a.dy+=fy;a.refined=1;a.status="subpixel-estimate";return a;
}
#endif
