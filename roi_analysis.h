/* Reusable ROI analysis. Included after Image/load_image/free_image and stb.
 * No decoder or global cropper state is changed. MIT license, like TTC. */
#ifndef TTC_ROI_ANALYSIS_H
#define TTC_ROI_ANALYSIS_H
#include <math.h>
#include <limits.h>
#include <errno.h>

#define ROI_MAX 32
#define ROI_SAMPLES 1024
#define ROI_PATH 2048
typedef struct {
    char name[64];
    int x, y, w, h;
    int sx[ROI_SAMPLES], sy[ROI_SAMPLES], n;
    double ref[ROI_SAMPLES], ref_mean, ref_energy;
} Roi;
typedef struct {
    double mean, contrast, sharpness, clipped, pcontrast;
} RoiMetrics;
typedef struct { int dx, dy; double score, margin; const char *status; } RoiMatch;

static double roi_gray(const Image *im, int x, int y) {
    const unsigned char *p = im->data + ((size_t)y * im->width + x) * 3;
    return (0.2126*p[0] + 0.7152*p[1] + 0.0722*p[2]) / 255.0;
}
static int roi_inside(const Image *im, const Roi *r, int dx, int dy) {
    return r->x + dx >= 0 && r->y + dy >= 0 &&
        (long long)r->x + dx + r->w <= im->width &&
        (long long)r->y + dy + r->h <= im->height;
}
/* Online variance avoids cancellation on flat, bright patches. Gradient energy
 * uses all horizontal/vertical adjacent pairs, with separate pair counts. */
static RoiMetrics roi_measure(const Image *im, const Roi *r, int dx, int dy) {
    RoiMetrics m = {0};
    double variance = 0, gx = 0, gy = 0;
    size_t n = 0, clipped = 0, hist[256] = {0};
    for (int y = 0; y < r->h; ++y) for (int x = 0; x < r->w; ++x) {
        int ix = r->x + dx + x, iy = r->y + dy + y;
        double v = roi_gray(im, ix, iy), d = v - m.mean;
        m.mean += d / (double)++n;
        variance += d * (v - m.mean);
        ++hist[(int)(v * 255.0 + 0.5)];
        const unsigned char *p = im->data + ((size_t)iy * im->width + ix) * 3;
        if (p[0] == 0 || p[1] == 0 || p[2] == 0 ||
            p[0] == 255 || p[1] == 255 || p[2] == 255) ++clipped;
        if (x + 1 < r->w) { d = roi_gray(im, ix+1, iy) - v; gx += d*d; }
        if (y + 1 < r->h) { d = roi_gray(im, ix, iy+1) - v; gy += d*d; }
    }
    m.clipped = (double)clipped / n;
    if (m.mean > 0) {
        m.contrast = sqrt(variance / n) / m.mean;
        m.sharpness = sqrt(gx / ((double)(r->w-1)*r->h) +
                           gy / ((double)(r->h-1)*r->w)) / m.mean;
    }
    size_t count = 0;
    int lo = -1, hi = 255;
    for (int i = 0; i < 256; ++i) {
        count += hist[i];
        if (lo < 0 && count >= (n+19)/20) lo = i;
        if (count >= n - n/20) { hi = i; break; }
    }
    m.pcontrast = hi + lo > 0 ? (double)(hi-lo)/(hi+lo) : 0;
    return m;
}

/* Tracking uses context around the ROI, with a fixed, deterministic sample
 * grid and 3x3 averaging. Metrics always use unresampled original pixels. */
static double roi_smooth(const Image *im, int x, int y) {
    double s = 0;
    for (int j=-1; j<=1; ++j) for (int i=-1; i<=1; ++i)
        s += roi_gray(im,x+i,y+j);
    return s/9;
}
static void roi_reference(Roi *r, const Image *im, int radius) {
    int x0 = r->x-32, y0 = r->y-32;
    int x1 = r->x+r->w+31, y1 = r->y+r->h+31;
    if (x0 < radius+1) x0=radius+1;
    if (y0 < radius+1) y0=radius+1;
    if (x1 > im->width-radius-2) x1=im->width-radius-2;
    if (y1 > im->height-radius-2) y1=im->height-radius-2;
    r->n=0; r->ref_mean=0; r->ref_energy=0;
    if (x1-x0 < 8 || y1-y0 < 8) return;
    int nx = x1-x0+1 < 32 ? x1-x0+1 : 32;
    int ny = y1-y0+1 < 32 ? y1-y0+1 : 32;
    for (int y=0;y<ny;++y) for (int x=0;x<nx;++x) {
        int k=r->n++;
        r->sx[k]=x0+(x1-x0)*x/(nx-1);
        r->sy[k]=y0+(y1-y0)*y/(ny-1);
        r->ref[k]=roi_smooth(im,r->sx[k],r->sy[k]);
        r->ref_mean+=r->ref[k];
    }
    r->ref_mean/=r->n;
    for (int k=0;k<r->n;++k) { r->ref[k]-=r->ref_mean; r->ref_energy+=r->ref[k]*r->ref[k]; }
}
static RoiMatch roi_track(const Image *im, const Roi *r, int radius) {
    RoiMatch m={0,0,-2,0,"tracking-flat"};
    double scores[65*65];
    int side=2*radius+1;
    if (!r->n || r->ref_energy/r->n < 0.00001) return m;
    for (int dy=-radius;dy<=radius;++dy) for (int dx=-radius;dx<=radius;++dx) {
        int k=(dy+radius)*side+dx+radius;
        scores[k]=-2;
        double sum=0, sum2=0, cross=0;
        for (int s=0;s<r->n;++s) {
            double v=roi_smooth(im,r->sx[s]+dx,r->sy[s]+dy);
            sum+=v; sum2+=v*v; cross+=v*r->ref[s];
        }
        double energy=sum2-sum*sum/r->n;
        if (energy/r->n < 0.00001) continue;
        scores[k]=cross/sqrt(energy*r->ref_energy);
        if (scores[k]>m.score) { m.score=scores[k]; m.dx=dx; m.dy=dy; }
    }
    if (m.score < -1) return m;
    double next=-1;
    for (int dy=-radius;dy<=radius;++dy) for (int dx=-radius;dx<=radius;++dx)
        if (abs(dx-m.dx)>2 || abs(dy-m.dy)>2) {
            double v=scores[(dy+radius)*side+dx+radius];
            if (v>next) next=v;
        }
    m.margin=m.score-next;
    if (!roi_inside(im,r,m.dx,m.dy)) m.status="tracking-out-of-bounds";
    else if (abs(m.dx)==radius || abs(m.dy)==radius) m.status="tracking-boundary";
    else if (m.score<0.85) m.status="tracking-low-correlation";
    else if (m.margin<0.01) m.status="tracking-ambiguous";
    else m.status="tracked";
    return m;
}

static int roi_numbers(char *s, long long *values, int count) {
    for(int i=0;i<count;++i) {
        while(isspace((unsigned char)*s)) ++s;
        if(!*s) return 0;
        char *end; errno=0;
        values[i]=strtoll(s,&end,10);
        if(errno || end==s || (*end && !isspace((unsigned char)*end))) return 0;
        s=end;
    }
    while(isspace((unsigned char)*s)) ++s;
    return !*s;
}
static int roi_config(const char *path, Roi *rs, int *width, int *height) {
    FILE *f=fopen(path,"r");
    if (!f) { fprintf(stderr,"Cannot open ROI config: %s\n",path); return -1; }
    char line[512];
    int n=0, lineno=0, header=0, failed=0;
    while (fgets(line,sizeof line,f)) {
        ++lineno;
        if (!strchr(line,'\n') && !feof(f)) { failed=1; break; }
        char *s=line;
        if(lineno==1 && !strncmp(s,"\xef\xbb\xbf",3)) s+=3;
        while (isspace((unsigned char)*s)) ++s;
        if (!*s || *s=='#') continue;
        char *token=s;
        while(*s && !isspace((unsigned char)*s)) ++s;
        if(!*s) { failed=1; break; }
        *s++=0;
        long long values[4];
        if (!header) {
            if (strcmp(token,"image") || !roi_numbers(s,values,2) ||
                values[0]<8 || values[1]<8 || values[0]>100000 || values[1]>100000) { failed=1; break; }
            *width=(int)values[0]; *height=(int)values[1]; header=1; continue;
        }
        if(n==ROI_MAX || strlen(token)>63 || !roi_numbers(s,values,4)) { failed=1; break; }
        strcpy(rs[n].name,token);
        long long a=values[0],b=values[1],c=values[2],d=values[3];
        if (
            a<0 || b<0 || c<8 || d<8 || a>*width || b>*height ||
            c>*width-a || d>*height-b) { failed=1; break; }
        for (char *p=rs[n].name;*p;++p)
            if (!((*p>='a' && *p<='z') || (*p>='A' && *p<='Z') ||
                  (*p>='0' && *p<='9') || *p=='_' || *p=='-')) failed=1;
        for (int j=0;j<n;++j) if (!strcmp(rs[j].name,rs[n].name)) failed=1;
        if (failed) break;
        rs[n].x=(int)a; rs[n].y=(int)b; rs[n].w=(int)c; rs[n].h=(int)d; ++n;
    }
    if (ferror(f)) failed=1;
    fclose(f);
    if (failed || !header || !n) { fprintf(stderr,"Invalid ROI config near line %d: %s\n",lineno,path); return -1; }
    return n;
}
static void roi_html(FILE *f,const char *s) {
    for (;*s;++s) switch (*s) {
        case '&': fputs("&amp;",f); break; case '<': fputs("&lt;",f); break;
        case '>': fputs("&gt;",f); break; case '"': fputs("&quot;",f); break;
        default: fputc((unsigned char)*s,f);
    }
}
static void roi_csv(FILE *f,const char *s) {
    fputc('"',f);
    /* Avoid spreadsheet formula evaluation when opening a report. */
    if (*s=='=' || *s=='+' || *s=='-' || *s=='@' || *s=='\t' || *s=='\r') fputc('\'',f);
    for (;*s;++s) { if (*s=='"') fputc('"',f); fputc((unsigned char)*s,f); }
    fputc('"',f);
}
static int roi_preview(const Image *im,const Roi *r,int dx,int dy,const char *path) {
    int w=r ? r->w : im->width, h=r ? r->h : im->height;
    int max=r ? (w>h?w:h) : 1600;
    double scale=w>h ? (double)max/w : (double)max/h;
    if (scale>1) scale=1;
    int ow=(int)(w*scale), oh=(int)(h*scale);
    if (ow<1) ow=1;
    if (oh<1) oh=1;
    unsigned char *pixels=malloc((size_t)ow*oh*3);
    if (!pixels) return 0;
    for (int y=0;y<oh;++y) for (int x=0;x<ow;++x) {
        int ix=(int)((double)x*w/ow)+(r ? r->x+dx : 0);
        int iy=(int)((double)y*h/oh)+(r ? r->y+dy : 0);
        memcpy(pixels+((size_t)y*ow+x)*3,im->data+((size_t)iy*im->width+ix)*3,3);
    }
    int ok=stbi_write_png(path,ow,oh,3,pixels,ow*3);
    free(pixels); return ok;
}

static int roi_selective_windows(const Roi *rs, int n, int width, int height,
                                 int radius, SelectiveWindow *out, int max) {
    if (!out || n > max) return 0;
    int pad = radius ? 32 + radius + 1 : 0;
    for (int i = 0; i < n; ++i) {
        int x0 = rs[i].x - pad, y0 = rs[i].y - pad;
        int x1 = rs[i].x + rs[i].w + pad, y1 = rs[i].y + rs[i].h + pad;
        if (x0 < 0) x0 = 0;
        if (y0 < 0) y0 = 0;
        if (x1 > width) x1 = width;
        if (y1 > height) y1 = height;
        if (x1 <= x0 || y1 <= y0) return 0;
        out[i].x = x0; out[i].y = y0;
        out[i].w = x1 - x0; out[i].h = y1 - y0;
        out[i].sx = out[i].sy = 0;
    }
    return n;
}

static int roi_cli(int argc,char **argv) {
    if (argc<5) {
        fprintf(stderr,"Usage: ttc-cli --analyze CONFIG NEW_OUTPUT_DIR [--track 3..32] IMAGE...\n");
        return 1;
    }
    int first=4,radius=0;
    if (!strcmp(argv[first],"--track")) {
        char *end=NULL; errno=0;
        if (argc<7) return 1;
        long value=strtol(argv[first+1],&end,10);
        if (errno || !end || *end || value<3 || value>32) {
            fprintf(stderr,"Tracking radius must be an integer from 3 to 32.\n"); return 1;
        }
        radius=(int)value; first+=2;
    }
    Roi *rs=calloc(ROI_MAX,sizeof *rs);
    if (!rs) return 1;
    int width=0,height=0,n=roi_config(argv[2],rs,&width,&height);
    if (n<0) { free(rs); return 1; }
    /* A fresh directory prevents accidental source/report overwrites. */
    if (strlen(argv[3])>ROI_PATH-80 || mkdir(argv[3],0755)!=0) {
        fprintf(stderr,"Analysis output must be a NEW directory with an existing parent: %s\n",argv[3]); free(rs); return 1;
    }
    char path[ROI_PATH];
    snprintf(path,sizeof path,"%s/report.csv",argv[3]); FILE *csv=fopen(path,"w");
    snprintf(path,sizeof path,"%s/report.html",argv[3]); FILE *html=fopen(path,"w");
    if (!csv || !html) { if(csv)fclose(csv); if(html)fclose(html); free(rs); return 1; }
    snprintf(path,sizeof path,"%s/rois.conf",argv[3]); FILE *saved=fopen(path,"w");
    if(!saved) { fclose(csv); fclose(html); free(rs); return 1; }
    fprintf(saved,"# TTC ROI metrics v1: original reference coordinates\nimage %d %d\n",width,height);
    for(int j=0;j<n;++j) fprintf(saved,"%s %d %d %d %d\n",rs[j].name,rs[j].x,rs[j].y,rs[j].w,rs[j].h);
    int config_error=ferror(saved);
    if(fclose(saved)) config_error=1;
    if(config_error) { fclose(csv); fclose(html); free(rs); return 1; }
    fputs("image,roi,status,x,y,width,height,dx,dy,correlation,peak_margin,mean_luma,rms_contrast,percentile_contrast,gradient_sharpness,sharpness_vs_reference,clipped_fraction\n",csv);
    fputs("<!doctype html><meta charset=utf-8><title>TTC ROI comparison</title><style>body{font:16px system-ui;margin:2em;background:#f5f5f5;color:#20242a}table{border-collapse:collapse;background:white}td,th{border:1px solid #ccc;padding:.6em;text-align:left}img{max-width:320px;max-height:240px}code{white-space:pre-wrap}.overview{max-width:100%;max-height:none}small{display:block}th{position:sticky;top:0;background:#e4e9ed}</style><h1>TTC ROI comparison</h1><p>Relative detail and contrast on decoded RGB8 values. Compare the <b>same ROI</b> across frames. Higher gradient energy can also mean noise or sharpening. These are not MTF or calibrated lp/mm measurements.</p><p>First image is the reference. Coordinates are original decoded pixels; image size must match exactly. Tracking is integer translation only. Rejected tracking rows have no measurements. Inspect crops and clipping before ranking. ROI crops retain full decoded pixel detail; the overview alone uses nearest-neighbor downsampling.</p>",html);
    fprintf(html,"<p>TTC %s / ROI metrics v1. <a href=\"report.csv\">Download CSV</a> &middot; <a href=\"rois.conf\">Reusable ROI configuration</a></p><p>Expected size: %d &times; %d. Tracking radius: %d pixels.</p><pre>",VERSION,width,height,radius);
    for(int j=0;j<n;++j) fprintf(html,"%s: x=%d y=%d w=%d h=%d\n",rs[j].name,rs[j].x,rs[j].y,rs[j].w,rs[j].h);
    fputs("</pre><table><tr><th>Frame / ROI</th><th>Crop</th><th>Status / shift</th><th>Sharpness proxy</th><th>vs reference</th><th>RMS contrast</th><th>Mean / clipping</th></tr>",html);
    RoiMetrics baseline[ROI_MAX]={{0}};
    int errors=0,reference_ok=0;
    SelectiveWindow windows[ROI_MAX];
    int window_count=roi_selective_windows(rs,n,width,height,radius,windows,ROI_MAX);
    for(int i=first;i<argc;++i) {
        printf("Analyzing %s\n",argv[i]); fflush(stdout);
        Image *im=NULL;
#ifndef NO_LIBRAW
        if (i != first && window_count > 0)
            im=load_selective_dng(argv[i],width,height,windows,window_count);
#endif
        if (!im) im=load_image(argv[i]);
        const char *problem=!im ? "decode-failed" :
            im->width!=width || im->height!=height ? "dimension-mismatch" : NULL;
        if (i==first && !problem) reference_ok=1;
        if (!reference_ok && !problem) problem="reference-unavailable";
        if (i==first && !problem) {
            snprintf(path,sizeof path,"%s/reference.png",argv[3]);
            if (!roi_preview(im,NULL,0,0,path)) ++errors;
        }
        for(int j=0;j<n;++j) {
            Roi *r=&rs[j];
            RoiMatch match={0,0,1,0,"fixed"};
            RoiMetrics m={0};
            int valid=!problem;
            if(problem) match.status=problem;
            else if(i==first) { match.status="reference"; if(radius)roi_reference(r,im,radius); }
            else if(radius) { match=roi_track(im,r,radius); valid=!strcmp(match.status,"tracked"); }
            if(valid) {
                m=roi_measure(im,r,match.dx,match.dy);
                if(m.mean<0.01) { match.status="too-dark"; valid=0; }
                else if(m.contrast<0.001) { match.status="flat"; valid=0; }
                else if(m.clipped>0.01) match.status="clipping-warning";
            }
            if(i==first && valid) baseline[j]=m;
            if(!valid) ++errors;
            roi_csv(csv,argv[i]); fputc(',',csv); roi_csv(csv,r->name);
            fprintf(csv,",%s,%d,%d,%d,%d,%d,%d,",match.status,r->x+match.dx,r->y+match.dy,r->w,r->h,match.dx,match.dy);
            if(radius && i!=first && !problem && match.score>=-1)
                fprintf(csv,"%.6f,%.6f,",match.score,match.margin);
            else fputs(",,",csv);
            double relative=baseline[j].sharpness>0 ? m.sharpness/baseline[j].sharpness : 0;
            if(valid) {
                fprintf(csv,"%.8f,%.8f,%.8f,%.8f,",m.mean,m.contrast,m.pcontrast,m.sharpness);
                if(baseline[j].sharpness>0)fprintf(csv,"%.8f",relative);
                fprintf(csv,",%.8f\n",m.clipped);
            } else fputs(",,,,,\n",csv);
            fputs("<tr><td>",html); roi_html(html,argv[i]); fprintf(html,"<small>%s</small></td><td>",r->name);
            if(valid) {
                char name[64]; snprintf(name,sizeof name,"frame-%04d-roi-%02d.png",i-first+1,j+1);
                snprintf(path,sizeof path,"%s/%s",argv[3],name);
                if (!roi_preview(im,r,match.dx,match.dy,path)) ++errors;
                fprintf(html,"<img src=\"%s\" alt=\"%s\">",name,r->name);
            }
            fprintf(html,"</td><td>%s<small>dx=%d dy=%d",match.status,match.dx,match.dy);
            if(radius && i!=first && !problem && match.score>=-1)
                fprintf(html,"; NCC=%.3f; margin=%.3f",match.score,match.margin);
            else fputs("; correlation not estimated",html);
            fputs("</small></td>",html);
            if(valid) {
                fprintf(html,"<td>%.5f</td><td>",m.sharpness);
                if(baseline[j].sharpness>0)fprintf(html,"%.1f%%",100*relative); else fputs("unavailable",html);
                fprintf(html,"</td><td>%.4f</td><td>%.4f / %.2f%%</td></tr>",m.contrast,m.mean,100*m.clipped);
            } else fputs("<td colspan=4>Measurement rejected</td></tr>",html);
        }
        free_image(im);
    }
    fputs("</table><h2>Reference overview</h2>",html);
    if(reference_ok) {
        fprintf(html,"<svg role=img aria-label=\"Reference with ROI locations\" style=\"width:100%%;max-width:1600px\" viewBox=\"0 0 %d %d\"><image href=\"reference.png\" width=\"%d\" height=\"%d\"/>",width,height,width,height);
        int font=width/70; if(font<12)font=12;
        for(int j=0;j<n;++j) {
            Roi *r=&rs[j];
            fprintf(html,"<rect x=\"%d\" y=\"%d\" width=\"%d\" height=\"%d\" fill=\"none\" stroke=\"#ff4020\" stroke-width=\"%d\"/><text x=\"%d\" y=\"%d\" fill=\"#ff4020\" stroke=\"white\" stroke-width=\"1\" paint-order=\"stroke\" font-size=\"%d\">%s</text>",r->x,r->y,r->w,r->h,font/6+1,r->x,r->y+font,font,r->name);
        }
        fputs("</svg>",html);
    }
    fputs("<p>Detailed metric definitions and assumptions: docs/roi-analysis.md. The CSV retains full source paths and shifted measurement coordinates; subtract dx/dy to recover configured x/y.</p>",html);
    if(ferror(csv) || ferror(html)) ++errors;
    if(fclose(csv)) ++errors;
    if(fclose(html)) ++errors;
    free(rs);
    printf("Analysis report: %s/report.html (%d rejected rows or output errors)\n",argv[3],errors);
    return errors ? 2 : 0;
}
#endif
