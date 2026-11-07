import sys, os
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
n = 0
for root, _, files in os.walk(src):
    for fn in files:
        if fn.endswith('.png.dds'):
            rel = os.path.relpath(os.path.join(root, fn), src)
            out = os.path.join(dst, rel[:-4])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            Image.open(os.path.join(root, fn)).convert('RGBA').save(out); n += 1
print('converted', n)
