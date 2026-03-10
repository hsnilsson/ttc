#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>
#include <ctype.h>

#ifdef _WIN32
    #include <direct.h>
    #include <windows.h>
    #define mkdir(path, mode) _mkdir(path)
    #define PATH_SEPARATOR '\\'
#else
    #include <unistd.h>
    #define PATH_SEPARATOR '/'
#endif

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

// Include libraw for DNG support
#ifndef NO_LIBRAW
#ifdef _WIN32
    #include "C:\libraw\include\libraw\libraw.h"
#else
    #include <libraw/libraw.h>
#endif
#endif

#define VERSION "1.2.0"

typedef struct {
    int width;
    int height;
    unsigned char *data;
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
    char ext_lower[5];
    for (int i = 0; i < 4 && ext[i+1]; i++) {
        ext_lower[i] = tolower(ext[i+1]);
        ext_lower[i+1] = '\0';
    }
    
    return strcmp(ext_lower, "dng") == 0;
}

// Load image using libraw for DNG, stb_image for other formats
Image* load_image(const char *filename) {
    Image *img = malloc(sizeof(Image));
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
        
        // Unpack the raw data
        if (libraw_unpack(raw) != LIBRAW_SUCCESS) {
            printf("Warning: Could not unpack DNG file %s\n", filename);
            libraw_close(raw);
            free(img);
            return NULL;
        }
        
        // Process the raw data to get RGB image
        libraw_dcraw_process_t params = {
            .output_bps = 8,
            .use_auto_wb = 1,
            .no_auto_bright = 1,
            .output_color = 1, // sRGB
            .user_flip = 0,
            .user_black = 0,
            .user_sat = 0,
            .median_filter = 0,
            .highlight = 0,
            .use_camera_matrix = 1,
            .output_tiff = 0,
            .user_qual = 0,
            .user_black = 0,
            .user_sat = 0
        };
        
        if (libraw_dcraw_process(raw, &params) != LIBRAW_SUCCESS) {
            printf("Warning: Could not process DNG file %s\n", filename);
            libraw_close(raw);
            free(img);
            return NULL;
        }
        
        // Get the processed image data
        img->width = raw->sizes.width;
        img->height = raw->sizes.height;
        img->data = malloc(img->width * img->height * 3);
        
        if (!img->data) {
            libraw_close(raw);
            free(img);
            return NULL;
        }
        
        // Copy processed RGB data
        memcpy(img->data, raw->rawdata.color.image, img->width * img->height * 3);
        
        libraw_close(raw);
        printf("Loaded DNG: %dx%d\n", img->width, img->height);
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
        if (img->data) free(img->data);
        free(img);
    }
}

// Create composite image
int create_composite(Image *source, const char *output_path) {
    if (!source || !source->data) return -1;
    
    int width = source->width;
    int height = source->height;
    
    // Calculate crop sizes
    int crop_size = (width < height) ? width / 2 : height / 2;
    int corner_size = crop_size / 2;
    
    // Composite dimensions
    int comp_width = crop_size + corner_size * 2;
    int comp_height = crop_size + corner_size * 2;
    
    // Allocate composite image
    unsigned char *composite = malloc(comp_width * comp_height * 3);
    if (!composite) return -1;
    
    // Initialize to black
    memset(composite, 0, comp_width * comp_height * 3);
    
    // Extract and place center crop at top
    int center_x = width / 2;
    int center_y = height / 2;
    int crop_x = center_x - crop_size / 2;
    int crop_y = center_y - crop_size / 2;
    
    // Copy center crop to top center
    for (int y = 0; y < crop_size; y++) {
        if (crop_y + y >= 0 && crop_y + y < height) {
            for (int x = 0; x < crop_size; x++) {
                if (crop_x + x >= 0 && crop_x + x < width) {
                    int src_idx = ((crop_y + y) * width + (crop_x + x)) * 3;
                    int dst_idx = ((y) * comp_width + (x + corner_size)) * 3;
                    memcpy(&composite[dst_idx], &source->data[src_idx], 3);
                }
            }
        }
    }
    
    // Copy corners to bottom area
    // Top-left corner -> bottom-left
    for (int y = 0; y < corner_size; y++) {
        if (y < height) {
            for (int x = 0; x < corner_size; x++) {
                if (x < width) {
                    int src_idx = (y * width + x) * 3;
                    int dst_idx = ((crop_size + y) * comp_width + x) * 3;
                    memcpy(&composite[dst_idx], &source->data[src_idx], 3);
                }
            }
        }
    }
    
    // Top-right corner -> bottom-right
    for (int y = 0; y < corner_size; y++) {
        if (y < height) {
            for (int x = 0; x < corner_size; x++) {
                if (width - corner_size + x < width) {
                    int src_idx = (y * width + (width - corner_size + x)) * 3;
                    int dst_idx = ((crop_size + y) * comp_width + (crop_size + corner_size + x)) * 3;
                    memcpy(&composite[dst_idx], &source->data[src_idx], 3);
                }
            }
        }
    }
    
    // Bottom-left corner -> bottom-left (second row)
    for (int y = 0; y < corner_size; y++) {
        if (height - corner_size + y < height) {
            for (int x = 0; x < corner_size; x++) {
                if (x < width) {
                    int src_idx = ((height - corner_size + y) * width + x) * 3;
                    int dst_idx = ((crop_size + corner_size + y) * comp_width + x) * 3;
                    memcpy(&composite[dst_idx], &source->data[src_idx], 3);
                }
            }
        }
    }
    
    // Bottom-right corner -> bottom-right (second row)
    for (int y = 0; y < corner_size; y++) {
        if (height - corner_size + y < height) {
            for (int x = 0; x < corner_size; x++) {
                if (width - corner_size + x < width) {
                    int src_idx = ((height - corner_size + y) * width + (width - corner_size + x)) * 3;
                    int dst_idx = ((crop_size + corner_size + y) * comp_width + (crop_size + corner_size + x)) * 3;
                    memcpy(&composite[dst_idx], &source->data[src_idx], 3);
                }
            }
        }
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
}

int main(int argc, char *argv[]) {
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
