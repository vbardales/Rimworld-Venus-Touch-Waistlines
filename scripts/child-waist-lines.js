'use strict';
// Shows, on WDI's child body and fundoshi, the two waist lines that disagree:
//   red  = the line WdiAppPatterns cuts at in game (median + 1 facing south/north,
//          a straight line between the two ends facing east),
//   blue = the line scripts/preview-reprojected-*.js used (first six-pixel solid run).
//   node child-waist-lines.js        writes Art/work/child-waist-lines.png
const path = require('path');
const { decode, encode } = require('./png');

const WDI = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures';
const facings = ['south', 'east', 'north'];
const SCALE = 2, CROP = 256, X0 = 128, Y0 = 160;

function codeLine(cloth, facing) {
    const w = cloth.width;
    const line = new Array(w).fill(-1);
    for (let x = 0; x < w; x++) for (let y = 0; y < cloth.height; y++) if (cloth.data[(y * w + x) * 4 + 3] > 0) { line[x] = y; break; }
    const values = line.filter(v => v >= 0).sort((a, b) => a - b);
    if (facing !== 'east') { const y = values[values.length >> 1] + 1; return line.map(v => v < 0 ? v : y); }
    const first = line.findIndex(v => v >= 0);
    let last = w - 1; while (line[last] < 0) last--;
    const a = line[first] + 1, b = line[last] + 1;
    for (let x = first; x <= last; x++) line[x] = a + Math.trunc((b - a) * (x - first) / (last - first));
    return line;
}

function scriptLine(cloth) {
    const w = cloth.width;
    return Array.from({ length: w }, (_, x) => {
        for (let y = 0; y < cloth.height - 5; y++) {
            let solid = true;
            for (let k = 0; k < 6; k++) if (cloth.data[((y + k) * w + x) * 4 + 3] < 32) { solid = false; break; }
            if (solid) return y;
        }
        return -1;
    });
}

const W = CROP * SCALE * facings.length, H = CROP * SCALE;
const out = Buffer.alloc(W * H * 4, 255);
function put(px, py, rgb) {
    if (px < 0 || py < 0 || px >= W || py >= H) return;
    const i = (py * W + px) * 4;
    out[i] = rgb[0]; out[i + 1] = rgb[1]; out[i + 2] = rgb[2]; out[i + 3] = 255;
}

facings.forEach((facing, panel) => {
    const body = decode(`${WDI}/Things/Pawn/Humanlike/Bodies/Naked_Child_${facing}.png`);
    const cloth = decode(`${WDI}/UWUnderwear/loincloth/loincloth_Child_${facing}.png`);
    const w = body.width;
    for (let y = 0; y < CROP; y++) for (let x = 0; x < CROP; x++) {
        const i = ((Y0 + y) * w + X0 + x) * 4;
        const rgb = [255, 255, 255];
        for (const img of [body, cloth]) {
            const a = img.data[i + 3] / 255;
            for (let c = 0; c < 3; c++) rgb[c] = Math.round(img.data[i + c] * a + rgb[c] * (1 - a));
        }
        for (let dy = 0; dy < SCALE; dy++) for (let dx = 0; dx < SCALE; dx++) put(panel * CROP * SCALE + x * SCALE + dx, y * SCALE + dy, rgb);
    }
    const lines = [[scriptLine(cloth), [40, 90, 230]], [codeLine(cloth, facing), [220, 30, 30]]];
    for (const [line, rgb] of lines) for (let x = 0; x < CROP; x++) {
        const y = line[X0 + x];
        if (y < 0 || body.data[(y * w + X0 + x) * 4 + 3] === 0 && cloth.data[(y * w + X0 + x) * 4 + 3] === 0) continue;
        for (let dx = 0; dx < SCALE; dx++) for (let t = -1; t <= 1; t++) put(panel * CROP * SCALE + x * SCALE + dx, (y - Y0) * SCALE + t, rgb);
    }
    for (let y = 0; y < H; y++) put(panel * CROP * SCALE, y, [170, 170, 170]);
});

const file = path.join(__dirname, '..', 'Art', 'work', 'child-waist-lines.png');
encode(file, { width: W, height: H, data: out });
console.log('wrote', file);
