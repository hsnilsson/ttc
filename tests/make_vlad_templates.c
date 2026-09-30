/* Reproduce minimal reference derivatives. See docs/vlad-detector.md. */
#define STB_IMAGE_IMPLEMENTATION
#include "../stb_image.h"
#include <stdio.h>
#include <math.h>
int main(int argc,char **argv) {
    int w,h,n; unsigned char *p;
    const double boxes[5][4]={{9260,4840,650,650},{2040,1740,880,880},{16380,1930,880,880},{1690,9890,880,880},{16180,10300,880,880}};
    if(argc!=2 || !(p=stbi_load(argv[1],&w,&h,&n,3))) return 1;
    if(w!=1600 || h!=1066){fprintf(stderr,"Expected the documented 1600x1066 reference\n");stbi_image_free(p);return 1;}
    puts("/* Small grayscale derivatives of local Vlad reference; see docs/vlad-detector.md. */\nstatic const unsigned char vlad_templates[5][1024] = {");
    for(int k=0;k<5;k++) {
        double cx=(boxes[k][0]+boxes[k][2]/2)*w/19136.,cy=(boxes[k][1]+boxes[k][3]/2)*h/12752.;
        double span=(k?210.:200.)*w/1600.;
        puts("{");
        for(int j=0;j<32;j++) { for(int i=0;i<32;i++) {
            int x=(int)floor(cx+(i-15.5)*span/32+.5),y=(int)floor(cy+(j-15.5)*span/32+.5);
            double sum=0;
            for(int dy=-2;dy<=2;dy++) for(int dx=-2;dx<=2;dx++) {
                unsigned char *q=p+((y+dy)*w+x+dx)*3;
                sum+=.2126*q[0]+.7152*q[1]+.0722*q[2];
            }
            printf("%d%s",(int)(sum/25+.5),(i==31 && j==31)?"":",");
        } puts(""); } puts("},");
    } puts("};"); stbi_image_free(p);return 0;
}
