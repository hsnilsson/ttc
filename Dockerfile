FROM gcc:12.4-bookworm

# Install required libraries with security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    libraw-dev \
    libpng-dev \
    libjpeg-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Copy source files
COPY ttc-simple.c .
COPY stb_image.h .
COPY stb_image_write.h .

# Build with libraw support
RUN gcc -O2 -I/usr/include/libraw \
    -DLIBRAW_BUILDLIB \
    ttc-simple.c -o ttc-simple.exe \
    -lraw -lstdc++ -lpng -ljpeg -lm

# Test the executable
RUN ./ttc-simple.exe --help

CMD ["./ttc-simple.exe"]
