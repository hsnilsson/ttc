"""Regenerate the compact detector reference from the documented local preview."""
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build' / 'python-deps'))
import cv2
import numpy as np

source = Path(sys.argv[1])
data = source.read_bytes()
gray = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
assert gray is not None and gray.shape == (1066, 1600)
cv2.setNumThreads(1)
features, descriptors = cv2.SIFT_create(nfeatures=0, contrastThreshold=.025, edgeThreshold=12).detectAndCompute(gray, None)
# Dot-grid features dominate response ranking. Larger landmarks retain text,
# QR structure and panel context instead of thousands of identical dots.
indices = [i for i, feature in enumerate(features) if feature.size >= 6]
features = [features[i] for i in indices]
descriptors = descriptors[indices]
np.savez_compressed(ROOT / 'local' / 'vlad-reference.npz', gray=gray,
                    points=np.float32([f.pt for f in features]),
                    descriptors=descriptors.astype(np.uint8))
print('source sha256:', hashlib.sha256(data).hexdigest(), 'features:', len(features))
