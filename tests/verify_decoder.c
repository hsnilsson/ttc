/* Windows integration harness; includes the production loader unchanged. */
#define main ttc_program_main
#include "../ttc-simple.c"
#undef main
#include <inttypes.h>

static uint64_t hash_bytes(uint64_t h, const unsigned char *p, size_t n) {
    while (n--) { h ^= *p++; h *= UINT64_C(1099511628211); }
    return h;
}

static int temporary_path(char *path, const char *extension) {
    char directory[MAX_PATH], base[MAX_PATH];
    DWORD length = GetTempPathA(MAX_PATH, directory);
    if (!length || length >= MAX_PATH ||
        !GetTempFileNameA(directory, "ttc", 0, base)) return 0;
    if (strlen(base) + strlen(extension) >= MAX_PATH) {
        DeleteFileA(base); return 0;
    }
    strcpy(path, base); strcat(path, extension);
    if (!MoveFileA(base, path)) { DeleteFileA(base); return 0; }
    return 1;
}

static int smoke_tests(void) {
    const unsigned char pixels[] = {255,0,0, 0,255,0, 0,0,255,
                                   1,2,3, 254,127,63, 0,0,0};
    char path[MAX_PATH];
    if (!temporary_path(path, ".png")) return 0;
    int written = stbi_write_png(path, 3, 2, 3, pixels, 9);
    Image *im = written ? load_image(path) : NULL;
    int ok = im && im->width == 3 && im->height == 2 &&
             !memcmp(im->data, pixels, sizeof(pixels));
    free_image(im); DeleteFileA(path);
    if (!ok || !temporary_path(path, ".dng")) return 0;
    FILE *f = fopen(path, "wb");
    if (!f) { DeleteFileA(path); return 0; }
    fputs("not a DNG", f); fclose(f);
    im = load_image(path);
    ok = im == NULL;
    free_image(im); DeleteFileA(path);
    if (ok) puts("PASS synthetic RGB PNG and malformed DNG");
    return ok;
}

/* PPM header reader: consume exactly its final delimiter, never pixel bytes. */
static int ppm_token(FILE *f, char *token, size_t capacity) {
    int c;
    do {
        c = fgetc(f);
        if (c == '#') while (c != '\n' && c != EOF) c = fgetc(f);
    } while (c != EOF && isspace((unsigned char)c));
    size_t n = 0;
    while (c != EOF && !isspace((unsigned char)c)) {
        if (n + 1 >= capacity) return 0;
        token[n++] = (char)c; c = fgetc(f);
    }
    token[n] = 0;
    if (c == '\r') { c = fgetc(f); if (c != '\n' && c != EOF) ungetc(c, f); }
    return n != 0;
}

#ifndef NO_LIBRAW
static int reference_hash(const char *input, int *width, int *height,
                          uint64_t *hash) {
    char path[MAX_PATH];
    if (!temporary_path(path, ".ppm")) return 0;
    libraw_data_t *raw = libraw_init(0);
    int rc = raw ? libraw_open_file(raw, input) : -1;
    if (!rc) {
        /* Explicit independent reference configuration; preserve camera flip. */
        raw->params.half_size = 0;
        raw->params.output_bps = 8;
        raw->params.output_color = 1;
        raw->params.use_camera_wb = raw->params.use_auto_wb = 0;
        raw->params.no_auto_bright = 1;
        raw->params.adjust_maximum_thr = 0;
        raw->params.bright = 1;
        raw->params.output_tiff = 0;
        rc = libraw_unpack(raw);
        if (!rc) rc = libraw_dcraw_process(raw);
        if (!rc) rc = libraw_dcraw_ppm_tiff_writer(raw, path);
    }
    if (raw) libraw_close(raw);
    FILE *f = rc ? NULL : fopen(path, "rb");
    int ok = f != NULL;
    char token[64];
    if (ok) ok = ppm_token(f, token, sizeof(token)) && !strcmp(token, "P6");
    if (ok) { ok = ppm_token(f, token, sizeof(token)); *width = atoi(token); }
    if (ok) { ok = ppm_token(f, token, sizeof(token)); *height = atoi(token); }
    if (ok) ok = ppm_token(f, token, sizeof(token)) && !strcmp(token, "255") &&
                 *width > 0 && *height > 0;
    size_t expected = ok ? (size_t)*width * *height * 3 : 0, total = 0;
    unsigned char buffer[65536];
    *hash = UINT64_C(14695981039346656037);
    if (ok) {
        size_t n;
        while ((n = fread(buffer, 1, sizeof(buffer), f)) != 0) {
            *hash = hash_bytes(*hash, buffer, n); total += n;
        }
        ok = !ferror(f) && total == expected;
    }
    if (f) fclose(f);
    DeleteFileA(path);
    if (!ok) fprintf(stderr, "Reference PPM failed (LibRaw status %d)\n", rc);
    return ok;
}
#endif

int main(int argc, char **argv) {
    if (argc > 3 || (argc == 3 && strcmp(argv[2], "--reference"))) {
        fprintf(stderr, "Usage: %s [input.dng [--reference]]\n", argv[0]); return 2;
    }
    if (!smoke_tests()) { fputs("FAIL smoke tests\n", stderr); return 1; }
    if (argc == 1) return 0;
    Image *im = load_image(argv[1]);
    if (!im) return 1;
    int width = im->width, height = im->height;
    uint64_t hash = hash_bytes(UINT64_C(14695981039346656037), im->data,
                               (size_t)width * height * 3);
    free_image(im); /* Never retain the app image during reference decoding. */
    printf("APP %dx%d RGB8 FNV1a64=%016" PRIx64 "\n", width, height, hash);
    if (argc == 3) {
#ifndef NO_LIBRAW
        int rw = 0, rh = 0; uint64_t reference = 0;
        if (!reference_hash(argv[1], &rw, &rh, &reference)) return 1;
        printf("REF %dx%d RGB8 FNV1a64=%016" PRIx64 "\n", rw, rh, reference);
        if (width != rw || height != rh || hash != reference) {
            fputs("FAIL reference dimensions or pixels differ\n", stderr); return 1;
        }
        puts("PASS full-resolution oriented RGB8 matches LibRaw PPM writer");
#else
        fputs("Reference requires LibRaw\n", stderr); return 2;
#endif
    }
    return 0;
}
