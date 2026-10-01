/* Research-only LibRaw 0.21.2 decoder hook, single-threaded, fixture-specific.
 * Build with scripts/codex-selective-dng-probe.ps1. Never use for production.
 * Keeps LibRaw's original decoder identity/allocation/curve/predictor logic.
 */
#include <libraw/libraw.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <algorithm>
#include <chrono>
#include <vector>

static_assert(LIBRAW_MAJOR_VERSION==0 && LIBRAW_MINOR_VERSION==21 &&
              LIBRAW_PATCH_VERSION==2, "Probe requires LibRaw 0.21.2 headers");

struct Window {
    int x,y,w,h,rx,ry;
    std::vector<unsigned short> samples;
    std::vector<unsigned char> rgb;
};
static std::vector<Window> windows;
static bool selective=false;
static size_t visited=0, decoded=0;
bool ttc_probe_tile_needed(unsigned x,unsigned y,unsigned w,unsigned h) {
    ++visited;
    bool needed=!selective;
    for(const auto &r:windows)
        if(x<unsigned(r.rx+r.w) && y<unsigned(r.ry+r.h) &&
           x+w>unsigned(r.rx) && y+h>unsigned(r.ry)) needed=true;
    decoded+=needed;
    return needed;
}
static double now() {
    return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
static void check(int e) {
    if(e) { std::fprintf(stderr,"LibRaw: %s\n",libraw_strerror(e)); std::exit(1); }
}
static void settings(LibRaw &raw) {
    auto &p=raw.imgdata.params;
    p.half_size=0; p.output_bps=8; p.output_color=1;
    p.use_camera_wb=1; p.use_auto_wb=0; p.no_auto_bright=1;
    p.adjust_maximum_thr=0; p.bright=1;
}
static void validate(LibRaw &raw) {
    auto &s=raw.imgdata.sizes;
    auto &id=raw.imgdata.idata;
    std::printf("decoder=%s storage=%ux%u active=%ux%u margin=%u,%u flip=%d filters=%u colors=%d black=%u max=%u cam_mul=%.6f,%.6f,%.6f\n",
        raw.unpack_function_name(),s.raw_width,s.raw_height,s.width,s.height,
        s.left_margin,s.top_margin,s.flip,id.filters,id.colors,
        raw.imgdata.color.black,raw.imgdata.color.maximum,
        raw.imgdata.color.cam_mul[0],raw.imgdata.color.cam_mul[1],raw.imgdata.color.cam_mul[2]);
    if(std::strcmp(raw.unpack_function_name(),"lossless_dng_load_raw()") ||
       s.raw_width!=19200 || s.raw_height!=12752 || s.width!=19136 ||
       s.height!=12752 || s.flip!=3 || id.filters || id.colors!=3)
        { std::fprintf(stderr,"Unsupported fixture profile\n"); std::exit(1); }
    for(auto &r:windows) { r.rx=s.left_margin+s.width-r.x-r.w; r.ry=s.top_margin+s.height-r.y-r.h; }
}
int main(int argc,char **argv) {
    if(argc<2 || argc>3 || (argc==3 && std::strcmp(argv[2],"--selective-only"))) {
        std::fprintf(stderr,"usage: selective-dng-probe FILE.dng [--selective-only]\n"); return 1;
    }
    // Five source ROIs padded by 32 context + 32 search + 1 smoothing pixel.
    const int pad=65;
    const int boxes[][4]={{9260,4840,650,650},{2040,1740,880,880},
        {16380,1930,880,880},{1690,9890,880,880},{16180,10300,880,880}};
    for(auto &b:boxes) { Window r={}; r.x=b[0]-pad; r.y=b[1]-pad;
        r.w=b[2]+2*pad; r.h=b[3]+2*pad; windows.push_back(r); }
    size_t sampleBad=0,rgbBad=0,sampleCount=0,rgbCount=0;
    bool only=argc==3;
    for(int pass=only?1:0;pass<2;++pass) {
        selective=pass==1; visited=decoded=0;
        LibRaw raw; settings(raw); double t=now(); check(raw.open_file(argv[1]));
        validate(raw); double opened=now()-t;
        t=now(); check(raw.unpack()); double unpacked=now()-t;
        if(!raw.imgdata.rawdata.color4_image) return 1;
        std::printf("selective=%d open_s=%.6f unpack_s=%.6f visited=%zu decoded=%zu\n",selective,opened,unpacked,visited,decoded);
        for(auto &r:windows) {
            const auto *src=raw.imgdata.rawdata.color4_image;
            if(!selective) r.samples.resize(size_t(r.w)*r.h*4);
            for(int y=0;y<r.h;++y) for(int x=0;x<r.w;++x) for(int c=0;c<4;++c) {
                size_t k=(size_t(y)*r.w+x)*4+c;
                auto v=src[size_t(r.ry+y)*raw.imgdata.sizes.raw_width+r.rx+x][c];
                if(!selective) r.samples[k]=v;
                else if(!only) { sampleBad+=r.samples[k]!=v; ++sampleCount; }
            }
        }
        // Full decode reference renders the complete frame; selective pass only
        // renders initialized windows. Rendering skipped pixels is forbidden.
        double render=0;
        if(!selective) {
            t=now(); check(raw.dcraw_process()); int e=0;
            auto *im=raw.dcraw_make_mem_image(&e); check(e);
            if(!im || im->width!=19136 || im->height!=12752 || im->colors!=3 || im->bits!=8) return 1;
            render=now()-t;
            for(auto &r:windows) {
                r.rgb.resize(size_t(r.w)*r.h*3);
                for(int y=0;y<r.h;++y) std::copy_n(im->data+3*(size_t(r.y+y)*im->width+r.x),3*r.w,r.rgb.data()+size_t(y)*r.w*3);
            }
            LibRaw::dcraw_clear_mem(im);
        } else for(auto &r:windows) {
            auto &p=raw.imgdata.params;
            p.cropbox[0]=r.rx-raw.imgdata.rawdata.sizes.left_margin;
            p.cropbox[1]=r.ry-raw.imgdata.rawdata.sizes.top_margin;
            p.cropbox[2]=r.w; p.cropbox[3]=r.h;
            t=now(); check(raw.dcraw_process()); int e=0;
            auto *im=raw.dcraw_make_mem_image(&e); check(e);
            render+=now()-t;
            if(!im || im->width!=r.w || im->height!=r.h || im->colors!=3 || im->bits!=8) return 1;
            if(!only) for(size_t k=0;k<r.rgb.size();++k) { rgbBad+=r.rgb[k]!=im->data[k]; ++rgbCount; }
            LibRaw::dcraw_clear_mem(im);
        }
        std::printf("selective=%d render_s=%.6f total_s=%.6f\n",selective,render,opened+unpacked+render);
    }
    std::printf("sample_mismatches=%zu rgb_mismatches=%zu samples_compared=%zu rgb_bytes_compared=%zu compared=%d\n",sampleBad,rgbBad,sampleCount,rgbCount,!only);
    return sampleBad || rgbBad ? 2 : 0;
}
