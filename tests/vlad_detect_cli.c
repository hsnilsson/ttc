#define main ttc_cropper_main
#include "../ttc-simple.c"
#undef main
#include "../vlad_detector.h"
int main(int argc,char **argv) { return vlad_detect_cli(argc,argv); }
