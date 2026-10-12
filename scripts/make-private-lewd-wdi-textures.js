'use strict';
// PRIVATE ONLY.  Reprojects locally installed LEWD Hooman Apparel sprites
// into WDI silhouette bands.  The source carries no redistribution licence;
// outputs are deliberately written under Parked/ and never Mod/.

const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');

const LEWD = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3275648920/Textures/Things/Apparel';
const BODIES = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies';
const OUT = path.join(__dirname, '..', 'Parked', 'LEWD-WDI-Textures', 'Textures', 'Things', 'Apparel');
const profiles = [
  ['Male', 'Male'], ['Female', 'Female'], ['Thin', 'Male'], ['Hulk', 'Male'], ['Fat', 'Male'],
  ['Thin_Female', 'Female'], ['Hulk_Female', 'Female'], ['Fat_Female', 'Female'], ['Child', 'Male']
];
const garments = [
  ['TubeTop', .21, .46], ['FlakiniVest', .20, .45], ['MicroSkirt', .52, .72]
];
const facings = ['south', 'east', 'north'];

function opaqueBounds(im) {
  let left = im.width, right = -1, top = im.height, bottom = -1;
  for (let y = 0; y < im.height; y++) for (let x = 0; x < im.width; x++) {
    if (!im.data[(y * im.width + x) * 4 + 3]) continue;
    left = Math.min(left, x); right = Math.max(right, x); top = Math.min(top, y); bottom = Math.max(bottom, y);
  }
  if (right < left) throw new Error('empty texture');
  return { left, right, top, bottom };
}
function alpha(im, x, y) {
  return x >= 0 && y >= 0 && x < im.width && y < im.height && im.data[(y * im.width + x) * 4 + 3];
}

for (const [garment, firstShare, lastShare] of garments) for (const [profile, sourceSex] of profiles) for (const facing of facings) {
  const source = decode(path.join(LEWD, garment, `${garment}_${sourceSex}_${facing}.png`));
  const body = decode(path.join(BODIES, `Naked_${profile}_${facing}.png`));
  const sourceBox = opaqueBounds(source), bodyBox = opaqueBounds(body);
  const bodyHeight = bodyBox.bottom - bodyBox.top + 1;
  const top = Math.round(bodyBox.top + bodyHeight * firstShare);
  const bottom = Math.round(bodyBox.top + bodyHeight * lastShare);
  const centre = Math.round((bodyBox.left + bodyBox.right) / 2);
  const widthAtTop = Math.max(1, Math.round((bodyBox.right - bodyBox.left + 1) * .72));
  const left = centre - Math.floor(widthAtTop / 2), right = left + widthAtTop - 1;
  const data = Buffer.alloc(body.width * body.height * 4);

  for (let y = top; y <= bottom; y++) for (let x = left; x <= right; x++) {
    if (!alpha(body, x, y)) continue;
    const u = (x - left) / Math.max(1, right - left);
    const v = (y - top) / Math.max(1, bottom - top);
    const sx = Math.round(sourceBox.left + u * (sourceBox.right - sourceBox.left));
    const sy = Math.round(sourceBox.top + v * (sourceBox.bottom - sourceBox.top));
    const si = (sy * source.width + sx) * 4;
    if (!source.data[si + 3]) continue;
    const di = (y * body.width + x) * 4;
    source.data.copy(data, di, si, si + 4);
  }
  const folder = path.join(OUT, garment);
  fs.mkdirSync(folder, { recursive: true });
  const target = { width: body.width, height: body.height, data };
  encode(path.join(folder, `${garment}_${profile}_${facing}.png`), target);
  // Graphic_Multi resolves its unsuffixed texture before body/facing variants.
  // Keep a real fallback instead of making the entire graphic fail to load.
  if (profile === 'Male' && facing === 'south')
    encode(path.join(folder, `${garment}.png`), target);
}
console.log('generated 81 private LEWD-derived WDI textures and 3 Graphic_Multi fallbacks');
