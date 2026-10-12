'use strict';
// Produces renderer-ready blue diagnostic trousers.  These are deliberately
// plain RGBA apparel assets: Pickle therefore verifies RimWorld's actual worn
// texture pipeline instead of an APP preview compositor.
const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');

const BODY_ROOT = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies';
const OUTPUT = path.join(__dirname, '..', 'Mod', 'Textures', 'Venus', 'Diagnostics', 'TransparentPants');
const SOURCES = ['Male', 'Female', 'Thin', 'Hulk', 'Fat', 'Thin_Female', 'Hulk_Female', 'Fat_Female', 'Child'];
const FACINGS = ['south', 'east', 'north'];
const BLUE = [40, 90, 215], EDGE = [18, 44, 112], BLACK = [0, 0, 0];
const FILL_ALPHA = 77, EDGE_ALPHA = 210;

function bounds(im) {
  let left = im.width, right = -1, top = im.height, bottom = -1;
  for (let y = 0; y < im.height; y++) for (let x = 0; x < im.width; x++) {
    if (!im.data[(y * im.width + x) * 4 + 3]) continue;
    left = Math.min(left, x); right = Math.max(right, x); top = Math.min(top, y); bottom = Math.max(bottom, y);
  }
  return { left, right, top, bottom };
}
function put(data, width, x, y, color, alpha) {
  const i = (y * width + x) * 4;
  data[i] = color[0]; data[i + 1] = color[1]; data[i + 2] = color[2]; data[i + 3] = alpha;
}
for (const source of SOURCES) for (const facing of FACINGS) {
  const body = decode(path.join(BODY_ROOT, `Naked_${source}_${facing}.png`));
  const box = bounds(body), data = Buffer.alloc(body.width * body.height * 4);
  // The one-pixel top border is above the underwear waist.  This stable
  // diagnostic proxy uses a body-relative waist; final refits replace it with
  // the per-underwear sampled waist curve.
  const waist = Math.round(box.top + (box.bottom - box.top + 1) * 0.52);
  for (let y = waist; y <= box.bottom; y++) for (let x = box.left; x <= box.right; x++) {
    if (!body.data[(y * body.width + x) * 4 + 3]) continue;
    put(data, body.width, x, y, BLUE, FILL_ALPHA);
  }
  // Dark waist/outer hem: makes a clearly inspectable contour even at 30% fill.
  for (let x = box.left; x <= box.right; x++) {
    if (body.data[(waist * body.width + x) * 4 + 3]) put(data, body.width, x, waist, EDGE, EDGE_ALPHA);
  }
  for (let x = box.left; x <= box.right; x++) {
    if (body.data[(box.bottom * body.width + x) * 4 + 3]) put(data, body.width, x, box.bottom, EDGE, EDGE_ALPHA);
  }
  // Long front/back trousers show the black between-leg split.  A side view
  // deliberately has no split, as agreed for the diagnostic convention.
  if (facing !== 'east' && source !== 'Child') {
    const mid = Math.round((box.left + box.right) / 2), start = Math.round(waist + (box.bottom - waist) * .54);
    for (let y = start; y <= box.bottom; y++) {
      const half = Math.max(0, Math.round((y - start) * .42));
      for (let x = mid - half; x <= mid + half; x++) if (x >= box.left && x <= box.right && body.data[(y * body.width + x) * 4 + 3]) put(data, body.width, x, y, BLACK, 255);
    }
  }
  fs.mkdirSync(OUTPUT, { recursive: true });
  encode(path.join(OUTPUT, `Pants_${source}_${facing}.png`), { width: body.width, height: body.height, data });
}
