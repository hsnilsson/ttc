/* Benchmark the production loader/compositor; hash outside timed sections. */
#ifndef TTC_SOURCE
#define TTC_SOURCE "../ttc-simple.c"
#endif
#define main ttc_program_main
#include TTC_SOURCE
#undef main
#include <inttypes.h>
#include <psapi.h>

static uint64_t image_hash(const Image *im) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < (size_t)im->width * im->height * 3; i++)
        hash = (hash ^ im->data[i]) * UINT64_C(1099511628211);
    return hash;
}
int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "Usage: benchmark INPUT_IMAGE OUTPUT_PNG\n"); return 2;
    }
    LARGE_INTEGER frequency, start, loaded, before_write, written;
    QueryPerformanceFrequency(&frequency); QueryPerformanceCounter(&start);
    Image *im = load_image(argv[1]); QueryPerformanceCounter(&loaded);
    if (!im) return 1;
    int width = im->width, height = im->height;
    uint64_t source_hash = image_hash(im);
    QueryPerformanceCounter(&before_write);
    int result = create_composite(im, argv[2]); QueryPerformanceCounter(&written);
    PROCESS_MEMORY_COUNTERS memory = {0}; memory.cb = sizeof(memory);
    GetProcessMemoryInfo(GetCurrentProcess(), &memory, sizeof(memory));
    free_image(im);
    if (result) return 1;
    Image *composite = load_image(argv[2]);
    if (!composite) return 1;
    printf("BENCH %dx%d source=%016" PRIx64 " composite=%dx%d:%016" PRIx64
           " load_s=%.6f composite_s=%.6f peak_mib=%.2f\n",
           width, height, source_hash, composite->width, composite->height,
           image_hash(composite),
           (double)(loaded.QuadPart-start.QuadPart)/frequency.QuadPart,
           (double)(written.QuadPart-before_write.QuadPart)/frequency.QuadPart,
           (double)memory.PeakWorkingSetSize / (1024 * 1024));
    free_image(composite);
    return 0;
}
