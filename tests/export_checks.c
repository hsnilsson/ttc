/* gcc -std=c99 -O2 -DNO_LIBRAW tests/export_checks.c -o build/export-checks -lm */
#define main ttc_cropper_main
#include "../ttc-simple.c"
#undef main
#include <assert.h>
#ifdef _WIN32
#include <process.h>
#define getpid _getpid
#endif

int main(void) {
    unsigned char pixels[9*7*3], original[sizeof pixels];
    for (size_t i=0;i<sizeof pixels;i++) original[i]=(unsigned char)(i%251+1);
    int offsets[]={INT_MIN,-9,-3,0,2,9,INT_MAX};
    for(int a=0;a<7;a++)for(int b=0;b<7;b++) {
        memcpy(pixels,original,sizeof pixels);
        Image im={9,7,pixels,NULL}; int dx=offsets[a],dy=offsets[b];
        translate_image(&im,dx,dy);
        for(int y=0;y<7;y++)for(int x=0;x<9;x++)for(int c=0;c<3;c++) {
            long long sx=(long long)x+dx,sy=(long long)y+dy;
            int expected=(sx>=0 && sx<9 && sy>=0 && sy<7)?original[(sy*9+sx)*3+c]:0;
            assert(pixels[(y*9+x)*3+c]==expected);
        }
    }
    Image im={9,7,original,NULL};
    char path[128]; snprintf(path,sizeof path,"build/export-check-%lu.png",(unsigned long)getpid());
    assert(write_new_png(path,&im)); assert(!write_new_png(path,&im));
    Image *loaded=load_image(path); assert(loaded && loaded->width==9 && loaded->height==7);
    assert(!memcmp(loaded->data,original,sizeof original)); free_image(loaded); remove(path);
    unsigned char *large=malloc(500*420*3);assert(large);memset(large,123,500*420*3);
    Image big={500,420,large,NULL};Roi r={0};r.x=30;r.y=20;r.w=450;r.h=390;
    assert(roi_preview(&big,&r,0,0,path));loaded=load_image(path);
    assert(loaded && loaded->width==450 && loaded->height==390);
    free_image(loaded);free(large);remove(path);
    puts("Export checks passed: all translation directions/extremes, black edges, exact pixels, no overwrite, full-detail crops.");
    return 0;
}
