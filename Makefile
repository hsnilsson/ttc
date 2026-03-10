# Makefile for Test Target Cropper (C Implementation)
# Cross-platform build system for Windows, Linux, and macOS

# Compiler and flags
CC = gcc
CFLAGS = -Wall -O2 -std=c99
LDFLAGS = -lvips -lglib-2.0

# Target executable
TARGET = ttc
TARGET_EXT = .exe

# Source files
SOURCES = ttc.c

# Object files
OBJECTS = $(SOURCES:.c=.o)

# Platform-specific settings
ifeq ($(OS),Windows_NT)
    # Windows-specific settings
    TARGET := $(TARGET)$(TARGET_EXT)
    # VIPS installation paths for Windows (adjust as needed)
    CFLAGS += -I"C:/vips/include"
    LDFLAGS += -L"C:/vips/lib" -lvips -lglib-2.0 -lintl
else
    # Unix-like systems (Linux, macOS)
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        # macOS-specific settings
        CFLAGS += $(shell pkg-config --cflags vips)
        LDFLAGS += $(shell pkg-config --libs vips)
    else
        # Linux-specific settings
        CFLAGS += $(shell pkg-config --cflags vips)
        LDFLAGS += $(shell pkg-config --libs vips)
    endif
endif

# Default target
all: $(TARGET)

# Build the executable
$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(TARGET) $(LDFLAGS)

# Compile source files
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -f $(OBJECTS) $(TARGET) $(TARGET).exe

# Install dependencies (platform-specific)
install-deps:
ifeq ($(OS),Windows_NT)
	@echo "On Windows, please install VIPS manually:"
	@echo "1. Download from https://github.com/libvips/libvips/releases"
	@echo "2. Install to C:/vips or update paths in Makefile"
else ifeq ($(UNAME_S),Darwin)
	brew install vips
else
	sudo apt-get update
	sudo apt-get install libvips-dev pkg-config
endif

# Test the build
test: $(TARGET)
	./$(TARGET) --help
	./$(TARGET) --version

# Static build for distribution (if supported)
static: LDFLAGS += -static
static: $(TARGET)

# Development build with debug info
debug: CFLAGS += -g -DDEBUG
debug: $(TARGET)

# Show configuration
show-config:
	@echo "Compiler: $(CC)"
	@echo "Flags: $(CFLAGS)"
	@echo "Linker: $(LDFLAGS)"
	@echo "Target: $(TARGET)"
	@echo "Platform: $(OS) ($(UNAME_S))"

# Help target
help:
	@echo "Available targets:"
	@echo "  all          - Build the executable (default)"
	@echo "  clean        - Remove build artifacts"
	@echo "  install-deps - Install required dependencies"
	@echo "  test         - Build and test the executable"
	@echo "  static       - Build static executable for distribution"
	@echo "  debug        - Build with debug information"
	@echo "  show-config  - Display build configuration"
	@echo "  help         - Show this help message"

.PHONY: all clean install-deps test static debug show-config help
