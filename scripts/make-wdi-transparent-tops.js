'use strict';
// Builds deliberately simple, inspectable source art for the WDI apparel
// gallery.  This is not an APP mask: each output is a real RGBA shirt texture
// that RimWorld can load normally.  Only WDI's alpha shape is read; none of
// its colour/shading art is copied.

const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');

const BODY_ROOT = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies';
const OUTPUT = path.join(__dirname, '..', 'Mod', 'Textures', 'Venus', 'Diagnostics', 'TransparentTop');
const SOURCES = [
    'Male', 'Female', 'Thin', 'Hulk', 'Fat', 'Thin_Female', 'Hulk_Female', 'Fat_Female', 'Child'
];
const FACINGS = ['south', 'east', 'north'];
const RED = [210, 45, 45];
const OPACITY = 77; // 30 percent, rounded from 255 * 0.30.
const TOP_SHARE = 0.58; // shoulder to natural waist; deliberately no legs.

function opaqueBounds(image) {
    let left = image.width, right = -1, top = image.height, bottom = -1;
    for (let y = 0; y < image.height; y++) for (let x = 0; x < image.width; x++) {
        if (image.data[(y * image.width + x) * 4 + 3] === 0) continue;
        left = Math.min(left, x); right = Math.max(right, x);
        top = Math.min(top, y); bottom = Math.max(bottom, y);
    }
    if (right < left) throw new Error('empty WDI body texture');
    return { left, right, top, bottom };
}

for (const source of SOURCES) for (const facing of FACINGS) {
    const input = path.join(BODY_ROOT, `Naked_${source}_${facing}.png`);
    const body = decode(input);
    const box = opaqueBounds(body);
    const hem = Math.round(box.top + (box.bottom - box.top + 1) * TOP_SHARE);
    const data = Buffer.alloc(body.width * body.height * 4);
    for (let y = box.top; y <= Math.min(hem, box.bottom); y++) for (let x = box.left; x <= box.right; x++) {
        const i = (y * body.width + x) * 4;
        const alpha = body.data[i + 3];
        if (alpha === 0) continue;
        data[i] = RED[0]; data[i + 1] = RED[1]; data[i + 2] = RED[2];
        data[i + 3] = Math.round(alpha * OPACITY / 255);
    }
    fs.mkdirSync(OUTPUT, { recursive: true });
    const target = path.join(OUTPUT, `Top_${source}_${facing}.png`);
    encode(target, { width: body.width, height: body.height, data });
    console.log(path.relative(path.join(__dirname, '..'), target));
}
