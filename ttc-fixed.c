/*
 * Test Target Cropper - C Implementation (Fixed)
 * 
 * Creates composite images from test target photos for pixel peeping analysis.
 * Generates 2x2 grid of corner crops with center overlay.
 * 
 * Author: hsnilsson
 * License: MIT
 * Version: 1.2.0
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vips/vips.h>
#include <getopt.h>
#include <windows.h>

#define VERSION "1.2.0"

void process_file(const char *input_dir, const char *filename, const char *output_dir);
void print_usage(void);
void print_version(void);

int main(int argc, char **argv) {
    // Initialize VIPS
    if (VIPS_INIT(argv[0])) {
        vips_error_exit("unable to start VIPS");
    }

    // Parse arguments
    char *input_dir = ".";
    char *output_dir = NULL;
    int use_pngs_only = 0;
    int show_help = 0;
    int show_version = 0;

    static struct option long_options[] = {
        {"output", required_argument, 0, 'o'},
        {"use-pngs-only", no_argument, 0, 'p'},
        {"use-pngs", no_argument, 0, 'p'},
        {"help", no_argument, 0, 'h'},
        {"version", no_argument, 0, 'v'},
        {0, 0, 0, 0}
    };

    int c;
    while ((c = getopt_long(argc, argv, "o:pvh", long_options, NULL)) != -1) {
        switch (c) {
            case 'o':
                output_dir = optarg;
                break;
            case 'p':
                use_pngs_only = 1;
                break;
            case 'h':
                show_help = 1;
                break;
            case 'v':
                show_version = 1;
                break;
            case '?':
                print_usage();
                return 1;
            default:
                abort();
        }
    }

    if (show_help) {
        print_usage();
        vips_shutdown();
        return 0;
    }

    if (show_version) {
        print_version();
        vips_shutdown();
        return 0;
    }

    // Handle positional argument (input directory)
    if (optind < argc) {
        input_dir = argv[optind];
    }

    // Set default output directory
    if (!output_dir) {
        size_t len = strlen(input_dir) + 7; // "/crops" + null
        output_dir = malloc(len);
        snprintf(output_dir, len, "%s/crops", input_dir);
    }

    // Validate input directory
    struct stat st;
    if (stat(input_dir, &st) == -1 || !S_ISDIR(st.st_mode)) {
        fprintf(stderr, "Error: Directory '%s' does not exist.\n", input_dir);
        if (output_dir != argv[2] && output_dir != NULL) free(output_dir);
        vips_shutdown();
        return 1;
    }

    // Create output directory if it doesn't exist
    if (stat(output_dir, &st) == -1) {
        mkdir(output_dir);
    }

    // Scan directory for image files
    DIR *d = opendir(input_dir);
    if (!d) {
        fprintf(stderr, "Error: Cannot open directory '%s'.\n", input_dir);
        if (output_dir != argv[2] && output_dir != NULL) free(output_dir);
        vips_shutdown();
        return 1;
    }

    struct dirent *dir;
    int file_count = 0;
    printf("Searching for files in '%s'\n", input_dir);
    
    while ((dir = readdir(d)) != NULL) {
        char *name = dir->d_name;
        if (name[0] == '.') continue; // skip hidden files
        
        if (strstr(name, "composite") || strstr(name, "_crops_")) continue;

        int is_png = strstr(name, ".png") != NULL;
        int is_dng = strstr(name, ".dng") != NULL;

        if ((is_dng && !use_pngs_only) || is_png) {
            if (file_count == 0) {
                printf("Found image files to process:\n");
            }
            printf("  - %s\n", name);
            process_file(input_dir, name, output_dir);
            file_count++;
        }
    }
    closedir(d);

    if (file_count == 0) {
        printf("No image files found to process in '%s'.\n", input_dir);
    } else {
        printf("\nProcessing complete! Check the '%s' directory for results.\n", output_dir);
    }

    // Free allocated memory
    if (output_dir != argv[2] && output_dir != NULL) free(output_dir);

    vips_shutdown();
    return 0;
}

void process_file(const char *input_dir, const char *filename, const char *output_dir) {
    char path[1024];
    snprintf(path, sizeof(path), "%s/%s", input_dir, filename);

    printf("Processing %s\n", path);

    // Load image with proper error checking
    VipsImage *img = NULL;
    if (vips_image_new_from_file(path, &img, NULL)) {
        fprintf(stderr, "Error loading %s: %s\n", path, vips_error_buffer());
        return;
    }

    // CRITICAL FIX: Check if img is NULL even if load returned success
    if (!img) {
        fprintf(stderr, "Error: VIPS loaded %s but returned NULL image\n", path);
        fprintf(stderr, "This is a known issue with some DNG files.\n");
        fprintf(stderr, "Try converting the DNG to a different format or use PNG files.\n");
        return;
    }

    // Verify the image object is valid
    if (!VIPS_IS_IMAGE(img)) {
        fprintf(stderr, "Error: Invalid image object for %s\n", path);
        return;
    }

    // Get image size
    int width = vips_image_get_width(img);
    int height = vips_image_get_height(img);
    printf("Original image size: %dx%d\n", width, height);

    // Calculate crop dimensions
    int corner_height = (int)(height * 0.07);
    int corner_width = corner_height; // square

    // Center crop coordinates
    double center_x1 = width * 0.58;
    double center_y1 = height * 0.37;
    double center_x2 = width * 0.61;
    double center_y2 = height * 0.42;
    int center_w = (int)(center_x2 - center_x1);
    int center_h = (int)(center_y2 - center_y1);

    // Crop center
    VipsImage *center_crop = NULL;
    if (vips_crop(img, &center_crop, center_x1, center_y1, center_w, center_h, NULL)) {
        fprintf(stderr, "Error cropping center: %s\n", vips_error_buffer());
        g_object_unref(img);
        return;
    }

    // Corner positions
    double corners[4][2] = {
        {0.095, 0.120}, // top_left
        {0.862, 0.143}, // top_right
        {0.078, 0.779}, // bottom_left
        {0.848, 0.801}  // bottom_right
    };

    VipsImage *corner_crops[4] = {NULL};
    for (int i = 0; i < 4; i++) {
        int x = (int)(width * corners[i][0]);
        int y = (int)(height * corners[i][1]);
        if (vips_crop(img, &corner_crops[i], x, y, corner_width, corner_height, NULL)) {
            fprintf(stderr, "Error cropping corner %d: %s\n", i, vips_error_buffer());
            g_object_unref(img);
            g_object_unref(center_crop);
            for (int j = 0; j < i; j++) g_object_unref(corner_crops[j]);
            return;
        }
    }

    // Create composite image
    int comp_width = 2 * corner_width;
    int comp_height = 2 * corner_height;
    VipsImage *composite = NULL;
    if (vips_black(&composite, comp_width, comp_height, "bands", 3, NULL)) {
        fprintf(stderr, "Error creating composite: %s\n", vips_error_buffer());
        g_object_unref(img);
        g_object_unref(center_crop);
        for (int i = 0; i < 4; i++) g_object_unref(corner_crops[i]);
        return;
    }

    // Composite corners (top-left, top-right, bottom-left, bottom-right)
    VipsImage *temp = NULL;
    if (vips_composite2(composite, corner_crops[0], &temp, VIPS_BLEND_MODE_OVER, 0, 0, NULL)) {
        fprintf(stderr, "Error compositing top-left: %s\n", vips_error_buffer());
        goto cleanup;
    }
    g_object_unref(composite);
    composite = temp;

    if (vips_composite2(composite, corner_crops[1], &temp, VIPS_BLEND_MODE_OVER, corner_width, 0, NULL)) {
        fprintf(stderr, "Error compositing top-right: %s\n", vips_error_buffer());
        goto cleanup;
    }
    g_object_unref(composite);
    composite = temp;

    if (vips_composite2(composite, corner_crops[2], &temp, VIPS_BLEND_MODE_OVER, 0, corner_height, NULL)) {
        fprintf(stderr, "Error compositing bottom-left: %s\n", vips_error_buffer());
        goto cleanup;
    }
    g_object_unref(composite);
    composite = temp;

    if (vips_composite2(composite, corner_crops[3], &temp, VIPS_BLEND_MODE_OVER, corner_width, corner_height, NULL)) {
        fprintf(stderr, "Error compositing bottom-right: %s\n", vips_error_buffer());
        goto cleanup;
    }
    g_object_unref(composite);
    composite = temp;

    // Composite center crop on top
    int cx = (comp_width - vips_image_get_width(center_crop)) / 2;
    int cy = (comp_height - vips_image_get_height(center_crop)) / 2;
    if (vips_composite2(composite, center_crop, &temp, VIPS_BLEND_MODE_OVER, cx, cy, NULL)) {
        fprintf(stderr, "Error compositing center: %s\n", vips_error_buffer());
        goto cleanup;
    }
    g_object_unref(composite);
    composite = temp;

    // Save composite
    char out_path[1024];
    char base[256];
    strcpy(base, filename);
    char *dot = strrchr(base, '.');
    if (dot) *dot = '\0';
    snprintf(out_path, sizeof(out_path), "%s/%s_composite.png", output_dir, base);
    if (vips_image_write_to_file(composite, out_path, "compression", 0, NULL)) {
        fprintf(stderr, "Error saving %s: %s\n", out_path, vips_error_buffer());
        goto cleanup;
    }

    printf("Created composite: %s\n", out_path);
    printf("Composite size: %dx%d\n", comp_width, comp_height);
    printf("Center crop: %dx%d\n", center_w, center_h);
    printf("Corner crops: %dx%d\n", corner_width, corner_height);
    printf("--------------------------------------------------\n");

cleanup:
    g_object_unref(img);
    g_object_unref(center_crop);
    for (int i = 0; i < 4; i++) {
        if (corner_crops[i]) g_object_unref(corner_crops[i]);
    }
    if (composite) g_object_unref(composite);
}

void print_usage(void) {
    printf("Test Target Cropper %s\n", VERSION);
    printf("Create composite images from test target photos for pixel peeping analysis.\n\n");
    printf("Usage: ttc [INPUT_DIR] [OPTIONS]\n\n");
    printf("Arguments:\n");
    printf("  INPUT_DIR    Directory containing PNG/DNG files (default: current directory)\n\n");
    printf("Options:\n");
    printf("  -o, --output DIR        Output directory for composite images (default: INPUT_DIR/crops)\n");
    printf("  -p, --use-pngs-only     Only process PNG files; default is to prefer DNG\n");
    printf("  -h, --help              Show this help message\n");
    printf("  -v, --version           Show version information\n\n");
    printf("Examples:\n");
    printf("  ttc                     Process current directory\n");
    printf("  ttc ../photos           Process parent directory\n");
    printf("  ttc /path/to/photos     Process absolute path\n");
    printf("  ttc . -o results        Custom output directory\n");
    printf("  ttc --use-pngs-only     Only process PNG files\n");
}

void print_version(void) {
    printf("Test Target Cropper %s\n", VERSION);
    printf("License: MIT\n");
    printf("Author: hsnilsson\n");
}
