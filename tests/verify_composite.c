/* Independent coordinate oracle for the original center/corner layout. */
#define main ttc_program_main
#include "../ttc-simple.c"
#undef main
int main(void) {
    const int dimensions[][2]={{2,2},{3,7},{7,3},{8,8},{13,19},{20,14}};
    for(size_t t=0;t<sizeof(dimensions)/sizeof(dimensions[0]);t++) {
        int w=dimensions[t][0],h=dimensions[t][1];
        Image source={w,h,malloc((size_t)w*h*3),NULL};
        if(!source.data)return 1;
        for(int y=0;y<h;y++)for(int x=0;x<w;x++) {
            size_t i=((size_t)y*w+x)*3;
            source.data[i]=(unsigned char)x; source.data[i+1]=(unsigned char)y;
            source.data[i+2]=(unsigned char)(x+y+1);
        }
        char path[MAX_PATH],tmp[MAX_PATH];
        if(!GetTempPathA(MAX_PATH,tmp)||!GetTempFileNameA(tmp,"ttc",0,path))return 1;
        int rc=create_composite(&source,path); free(source.data);
        Image *out=rc?NULL:load_image(path); DeleteFileA(path);
        int c=(w<h?w:h)/2,k=c/2,n=c+2*k;
        if(!out || out->width!=n || out->height!=n)return 1;
        for(int y=0;y<n;y++)for(int x=0;x<n;x++) {
            int sx=-1,sy=-1;
            if(y<c && x>=k && x<k+c) {sx=w/2-c/2+x-k;sy=h/2-c/2+y;}
            else if(y>=c && x<k) {sx=x;sy=y<c+k?y-c:h-k+y-c-k;}
            else if(y>=c && x>=c+k) {sx=w-k+x-c-k;sy=y<c+k?y-c:h-k+y-c-k;}
            unsigned char expected[3]={0,0,0};
            if(sx>=0){expected[0]=(unsigned char)sx;expected[1]=(unsigned char)sy;expected[2]=(unsigned char)(sx+sy+1);}
            if(memcmp(out->data+((size_t)y*n+x)*3,expected,3))return 1;
        }
        free_image(out);
    }
    puts("PASS crop pixels, black padding, odd/even/portrait/landscape/tiny dimensions");
    return 0;
}
