#!/bin/bash
# Create favicon.ico from favicon_full.png with multiple sizes
convert favicon_full.png \
  \( -clone 0 -resize 16x16 \) \
  \( -clone 0 -resize 32x32 \) \
  \( -clone 0 -resize 48x48 \) \
  -delete 0 web/favicon.ico

# Also create individual PNG files for modern web use
convert favicon_full.png -resize 16x16 web/favicon-16x16.png
convert favicon_full.png -resize 32x32 web/favicon-32x32.png
convert favicon_full.png -resize 64x64 web/favicon-64x64.png
convert favicon_full.png -resize 180x180 web/apple-touch-icon.png

