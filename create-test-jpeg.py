#!/usr/bin/env python3
"""
Create a simple test JPEG image
"""

from PIL import Image
import numpy as np

# Create a simple 100x100 RGB image
data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
img = Image.fromarray(data, 'RGB')
img.save('test_image.jpg')
print("Created test_image.jpg")
