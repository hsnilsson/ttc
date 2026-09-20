#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <ctype.h>
#include <stdint.h>
#include <limits.h>

#ifdef _WIN32
    #include <direct.h>
    #include <windows.h>
    #include <io.h>
    #define mkdir(path, mode) _mkdir(path)
    #define PATH_SEPARATOR '\\'
    #ifndef S_ISREG
    #define S_ISREG(mode) (((mode) & _S_IFMT) == _S_IFREG)
    #endif
#else
    #include <unistd.h>
    #include <dirent.h>
    #define PATH_SEPARATOR '/'
#endif

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#ifdef TTC_LIBDEFLATE
#include <libdeflate.h>
// stb accepts a malloc-owned zlib stream. Keep filtering and pixels unchanged.
static unsigned char *ttc_zlib_compress(unsigned char *data, int length,
                                      int *out_length, int quality) {
    (void)quality;
    if (length < 0) return NULL;
    struct libdeflate_compressor *compressor = libdeflate_alloc_compressor(6);
    if (!compressor) return NULL;
    size_t capacity = libdeflate_zlib_compress_bound(compressor, (size_t)length);
    unsigned char *output = capacity <= INT_MAX ? malloc(capacity) : NULL;
    size_t written = output ? libdeflate_zlib_compress(compressor, data,
                                   (size_t)length, output, capacity) : 0;
    libdeflate_free_compressor(compressor);
    if (!written) { free(output); return NULL; }
    *out_length = (int)written;
    return output;
}
#define STBIW_ZLIB_COMPRESS ttc_zlib_compress
#endif
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

// Include libraw for DNG support
#ifndef NO_LIBRAW
#include <libraw/libraw.h>
#endif

#define VERSION "1.2.0"

typedef struct {
    int width;
    int height;
    unsigned char *data;
    void *allocation; // Optional owning block when data is an interior pointer.
} Image;

// Create output directory
int create_output_dir(const char *path) {
    struct stat st = {0};
    if (stat(path, &st) == -1) {
        return mkdir(path, 0755);
    }
    return 0;
}

// Check if file is DNG format
int is_dng_file(const char *filename) {
    if (!filename) return 0;
    
    const char *ext = strrchr(filename, '.');
    if (!ext) return 0;
    
    // Convert to lowercase for comparison
    char ext_lower[5] = {0};
    for (int i = 0; i < 4 && ext[i+1]; i++) {
        ext_lower[i] = tolower((unsigned char)ext[i+1]);
        ext_lower[i+1] = '\0';
    }
    
    return strcmp(ext_lower, "dng") == 0;
}

// Load image using libraw for DNG, stb_image for other formats
Image* load_image(const char *filename) {
    Image *img = calloc(1, sizeof(Image));
    if (!img) return NULL;
    
#ifndef NO_LIBRAW
    if (is_dng_file(filename)) {
        // Use libraw for DNG files
        libraw_data_t *raw = libraw_init(0);
        if (!raw) {
            free(img);
            return NULL;
        }
        
        if (libraw_open_file(raw, filename) != LIBRAW_SUCCESS) {
            printf("Warning: Could not open DNG file %s with libraw\n", filename);
            libraw_close(raw);
            free(img);
            return NULL;
        }
        
        // Full resolution, daylight WB, sRGB primaries and LibRaw default gamma.
        // raw2image alone is NOT a rendered RGB image (nor an 8-bit buffer).
        raw->params.half_size = 0;
        raw->params.output_bps = 8;
        raw->params.output_color = 1;
        raw->params.use_camera_wb = 0;
        raw->params.use_auto_wb = 0;
        raw->params.no_auto_bright = 1;
        raw->params.adjust_maximum_thr = 0.0f;
        raw->params.bright = 1.0f;
        int error = libraw_unpack(raw);
        if (error == LIBRAW_SUCCESS) error = libraw_dcraw_process(raw);
        libraw_processed_image_t *rendered = NULL;
        if (error == LIBRAW_SUCCESS)
            rendered = libraw_dcraw_make_mem_image(raw, &error);
        if (!rendered || error != LIBRAW_SUCCESS ||
            rendered->type != LIBRAW_IMAGE_BITMAP || rendered->bits != 8 ||
            rendered->colors != 3 || !rendered->width || !rendered->height ||
            (size_t)rendered->width * rendered->height * 3 != rendered->data_size) {
            fprintf(stderr, "DNG rendering failed for %s: %s\n", filename,
                    libraw_strerror(error));
            libraw_dcraw_clear_mem(rendered);
            libraw_close(raw);
            free(img);
            return NULL;
        }
        img->width = rendered->width;
        img->height = rendered->height;
        // The processed bitmap has independent ownership; no full-image copy.
        img->data = rendered->data;
        img->allocation = rendered;
        libraw_close(raw);
        printf("Loaded DNG: %dx%d (daylight WB, sRGB primaries, LibRaw gamma, fixed brightness)\n", img->width, img->height);
        return img;
        
    } else {
#endif // NO_LIBRAW
        // Use stb_image for other formats (PNG, JPG, BMP, etc.)
        int channels;
        img->data = stbi_load(filename, &img->width, &img->height, &channels, 3);
        
        if (!img->data) {
            free(img);
            return NULL;
        }
        
        return img;
#ifndef NO_LIBRAW
    }
#endif
}

void free_image(Image *img) {
    if (img) {
        if (img->allocation) {
#ifndef NO_LIBRAW
            libraw_dcraw_clear_mem((libraw_processed_image_t *)img->allocation);
#else
            free(img->allocation);
#endif
        }
        else if (img->data) free(img->data);
        free(img);
    }
}

// Create composite image
int create_composite(Image *source, const char *output_path) {
    if (!source || !source->data || source->width < 2 || source->height < 2) return -1;
    
    int width = source->width;
    int height = source->height;
    
    // Calculate crop sizes
    int crop_size = (width < height) ? width / 2 : height / 2;
    int corner_size = crop_size / 2;
    
    // Composite dimensions
    int comp_width = crop_size + corner_size * 2;
    int comp_height = crop_size + corner_size * 2;
    
    // Allocate composite image
    unsigned char *composite = malloc((size_t)comp_width * comp_height * 3);
    if (!composite) return -1;
    
    // Initialize to black
    memset(composite, 0, (size_t)comp_width * comp_height * 3);
    
    // Extract and place center crop at top
    int center_x = width / 2;
    int center_y = height / 2;
    int crop_x = center_x - crop_size / 2;
    int crop_y = center_y - crop_size / 2;
    
    // Each crop is in bounds by construction; copy whole RGB rows.
    for (int y = 0; y < crop_size; y++) {
        memcpy(composite + ((size_t)y * comp_width + corner_size) * 3,
               source->data + ((size_t)(crop_y + y) * width + crop_x) * 3,
               (size_t)crop_size * 3);
    }
    for (int y = 0; y < corner_size; y++) {
        size_t top = (size_t)y * width * 3;
        size_t bottom = (size_t)(height - corner_size + y) * width * 3;
        size_t first = (size_t)(crop_size + y) * comp_width * 3;
        size_t second = (size_t)(crop_size + corner_size + y) * comp_width * 3;
        size_t right_src = (size_t)(width - corner_size) * 3;
        size_t right_dst = (size_t)(crop_size + corner_size) * 3;
        size_t bytes = (size_t)corner_size * 3;
        memcpy(composite + first, source->data + top, bytes);
        memcpy(composite + first + right_dst, source->data + top + right_src, bytes);
        memcpy(composite + second, source->data + bottom, bytes);
        memcpy(composite + second + right_dst, source->data + bottom + right_src, bytes);
    }
    // Save composite
    int result = stbi_write_png(output_path, comp_width, comp_height, 3, composite, comp_width * 3);
    
    free(composite);
    return result ? 0 : -1;
}

// Process a single image file
void process_file(const char *filename, const char *output_dir) {
    printf("Processing %s\n", filename);
    
    Image *img = load_image(filename);
    if (!img) {
        printf("Error: Could not load %s\n", filename);
        return;
    }
    
    printf("Loaded image: %dx%d\n", img->width, img->height);
    
    // Create output filename
    const char *base = strrchr(filename, PATH_SEPARATOR);
    base = base ? base + 1 : filename;
    
    char *base_copy = strdup(base);
    char *ext = strrchr(base_copy, '.');
    if (ext) *ext = '\0';
    
    char output_path[512];
    snprintf(output_path, sizeof(output_path), "%s\\%s_composite.png", output_dir, base_copy);
    
    if (create_composite(img, output_path) == 0) {
        printf("Created composite: %s\n", output_path);
    } else {
        printf("Error: Could not create composite\n");
    }
    
    free(base_copy);
    free_image(img);
}

// Scan directory for image files
void scan_directory(const char *dir_path, const char *output_dir, int pngs_only) {
#ifdef _WIN32
    // Windows implementation
    WIN32_FIND_DATAA findData;
    char searchPattern[MAX_PATH];
    snprintf(searchPattern, sizeof(searchPattern), "%s\\*", dir_path);
    
    HANDLE hFind = FindFirstFileA(searchPattern, &findData);
    if (hFind == INVALID_HANDLE_VALUE) {
        printf("Error: Could not open directory %s\n", dir_path);
        return;
    }
    
    int found_files = 0;
    
    printf("Searching for files in '%s'\n", dir_path);
    
    // First pass: count files
    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            const char *name = findData.cFileName;
            size_t len = strlen(name);
            
            if (len > 4) {
                const char *ext = name + len - 4;
                
                int is_dng = (strcasecmp(ext, ".dng") == 0);
                int is_png = (strcasecmp(ext, ".png") == 0);
                int is_jpg = (strcasecmp(ext, ".jpg") == 0) || (strcasecmp(ext, ".jpeg") == 0);
                
                if ((is_dng && !pngs_only) || is_png || is_jpg) {
                    found_files++;
                    printf("Found: %s\n", name);
                }
            }
        }
    } while (FindNextFileA(hFind, &findData));
    
    if (found_files == 0) {
        printf("No image files found\n");
        FindClose(hFind);
        return;
    }
    
    printf("Found %d image files to process\n", found_files);
    
    // Reset and process files
    FindClose(hFind);
    hFind = FindFirstFileA(searchPattern, &findData);
    
    do {
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            const char *name = findData.cFileName;
            size_t len = strlen(name);
            
            if (len > 4) {
                const char *ext = name + len - 4;
                
                int is_dng = (strcasecmp(ext, ".dng") == 0);
                int is_png = (strcasecmp(ext, ".png") == 0);
                int is_jpg = (strcasecmp(ext, ".jpg") == 0) || (strcasecmp(ext, ".jpeg") == 0);
                
                if ((is_dng && !pngs_only) || is_png || is_jpg) {
                    char full_path[MAX_PATH];
                    snprintf(full_path, sizeof(full_path), "%s\\%s", dir_path, name);
                    
                    process_file(full_path, output_dir);
                }
            }
        }
    } while (FindNextFileA(hFind, &findData));
    
    FindClose(hFind);
#else
    // POSIX implementation (original code)
    DIR *dir = opendir(dir_path);
    if (!dir) {
        printf("Error: Could not open directory %s\n", dir_path);
        return;
    }
    
    struct dirent *entry;
    int found_files = 0;
    
    printf("Searching for files in '%s'\n", dir_path);
    
    // First pass: count files
    while ((entry = readdir(dir)) != NULL) {
        const char *name = entry->d_name;
        size_t len = strlen(name);
        
        if (len > 4) {
            const char *ext = name + len - 4;
            
            int is_dng = (strcasecmp(ext, ".dng") == 0);
            int is_png = (strcasecmp(ext, ".png") == 0);
            int is_jpg = (strcasecmp(ext, ".jpg") == 0) || (strcasecmp(ext, ".jpeg") == 0);
            
            if ((is_dng && !pngs_only) || is_png || is_jpg) {
                found_files++;
                printf("Found: %s\n", name);
            }
        }
    }
    
    if (found_files == 0) {
        printf("No image files found\n");
        closedir(dir);
        return;
    }
    
    printf("Found %d image files to process\n", found_files);
    
    // Reset and process files
    rewinddir(dir);
    
    while ((entry = readdir(dir)) != NULL) {
        const char *name = entry->d_name;
        size_t len = strlen(name);
        
        if (len > 4) {
            const char *ext = name + len - 4;
            
            int is_dng = (strcasecmp(ext, ".dng") == 0);
            int is_png = (strcasecmp(ext, ".png") == 0);
            int is_jpg = (strcasecmp(ext, ".jpg") == 0) || (strcasecmp(ext, ".jpeg") == 0);
            
            if ((is_dng && !pngs_only) || is_png || is_jpg) {
                char full_path[512];
                snprintf(full_path, sizeof(full_path), "%s%c%s", dir_path, PATH_SEPARATOR, name);
                
                // Check if it's actually a file (not directory)
                struct stat st;
                if (stat(full_path, &st) == 0 && S_ISREG(st.st_mode)) {
                    process_file(full_path, output_dir);
                }
            }
        }
    }
    
    closedir(dir);
#endif
}

#include "roi_analysis.h"

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "--analyze") == 0)
        return roi_cli(argc, argv);
    printf("Test Target Cropper %s (Simple Version)\n", VERSION);
    printf("License: MIT\n");
    printf("Author: hsnilsson\n\n");
    
    const char *input_dir = ".";
    const char *output_dir = NULL;
    int pngs_only = 0;
    
    // Simple argument parsing
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("Usage: ttc-simple [INPUT_DIR] [OPTIONS]\n\n");
            printf("Arguments:\n");
            printf("  INPUT_DIR    Directory containing PNG/JPG/DNG files (default: current directory)\n\n");
            printf("Options:\n");
            printf("  --analyze CONFIG OUT [--track N] IMAGE...  Compare configured ROIs (see docs/roi-analysis.md)\n");
            printf("  -o, --output DIR        Output directory for composite images (default: INPUT_DIR/crops)\n");
            printf("  -p, --use-pngs-only     Only process PNG files; default is to prefer all formats\n");
            printf("  -h, --help              Show this help message\n");
            printf("  -v, --version           Show version information\n\n");
            printf("Examples:\n");
            printf("  ttc-simple               Process current directory\n");
            printf("  ttc-simple ../photos     Process parent directory\n");
            printf("  ttc-simple . -o results  Custom output directory\n");
            printf("  ttc-simple --use-pngs-only Only process PNG files\n\n");
            printf("Note: This version supports PNG, JPG, BMP, GIF, DNG, etc.\n");
            printf("DNG files are processed using libraw for full resolution support.\n");
            return 0;
        }
        else if (strcmp(argv[i], "--version") == 0 || strcmp(argv[i], "-v") == 0) {
            printf("ttc-simple %s\n", VERSION);
            return 0;
        }
        else if (strcmp(argv[i], "--use-pngs-only") == 0 || strcmp(argv[i], "-p") == 0) {
            pngs_only = 1;
        }
        else if ((strcmp(argv[i], "--output") == 0 || strcmp(argv[i], "-o") == 0) && i + 1 < argc) {
            output_dir = argv[++i];
        }
        else if (argv[i][0] != '-') {
            input_dir = argv[i];
        }
    }
    
    // Set default output directory
    char default_output[512];
    if (!output_dir) {
        snprintf(default_output, sizeof(default_output), "%s\\crops", input_dir);
        output_dir = default_output;
    }
    
    // Create output directory
    if (create_output_dir(output_dir) != 0) {
        printf("Error: Could not create output directory %s\n", output_dir);
        return 1;
    }
    
    printf("Output directory: %s\n\n", output_dir);
    
    // Process directory
    scan_directory(input_dir, output_dir, pngs_only);
    
    printf("\nProcessing complete! Check the '%s' directory for results.\n", output_dir);
    
    return 0;
}
