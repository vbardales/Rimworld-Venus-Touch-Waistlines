'use strict';
// The cut rule exactly as WdiAppPatterns applies it in game, drawn offline on WDI's bodies: the
// reference the Pickle captures are compared with. One row per WDI texture, south / east / north.
//   blue  = trousers, from one row above the higher of WDI's boxers and panties lines,
//   red   = shirt, down to the lower of the two lines (purple where both overlap),
//   children: trousers from the smoothed fundoshi line, shirt with no hem cut.
//   node game-cut-preview.js        writes Art/work/game-cut-preview.png
// Keep in step with Source/TailorMadeWaistlines/WdiAppPatterns.cs (WaistLines, CombineUnderwearLines,
// UnderwearTopLine, SmoothChildFundoshiLine, AlphaMask).
const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');

const WDI = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures';
const KEYS = ['Male', 'Female', 'Thin', 'Thin_Female', 'Hulk', 'Hulk_Female', 'Fat', 'Fat_Female', 'Child'];
const FACINGS = ['south', 'east', 'north'];
const CROP = 320, X0 = 96, Y0 = 120;

function underwearTopLine(kind, key, facing, width) {
    const file = `${WDI}/UWUnderwear/${kind}/${kind}_${key}_${facing}.png`;
    if (!fs.existsSync(file)) return null;
    const img = decode(file);
    const line = new Array(width).fill(-1);
    for (let x = 0; x < width; x++) {
        const sx = Math.min(img.width - 1, Math.floor(x * img.width / width));
        for (let y = 0; y < img.height; y++) if (img.data[(y * img.width + sx) * 4 + 3] !== 0) { line[x] = y; break; }
    }
    let last = -1;
    for (let x = 0; x < width; x++) { if (line[x] >= 0) last = line[x]; else if (last >= 0) line[x] = last; }
    last = -1;
    for (let x = width - 1; x >= 0; x--) { if (line[x] >= 0) last = line[x]; else if (last >= 0) line[x] = last; }
    return line;
}

function smoothChildFundoshiLine(waist, facing) {
    const values = waist.filter(v => v >= 0).sort((a, b) => a - b);
    if (!values.length) return;
    if (facing !== 'east') {
        const line = values[values.length >> 1] + 1;
        for (let x = 0; x < waist.length; x++) if (waist[x] >= 0) waist[x] = line;
        return;
    }
    const first = waist.findIndex(v => v >= 0);
    let last = waist.length - 1; while (waist[last] < 0) last--;
    if (last <= first) return;
    const from = waist[first] + 1, to = waist[last] + 1;
    for (let x = first; x <= last; x++) waist[x] = from + Math.trunc((to - from) * (x - first) / (last - first));
}

function waistLines(key, facing, width) {
    if (key === 'Child') {
        const f = underwearTopLine('loincloth', key, facing, width);
        smoothChildFundoshiLine(f, facing);
        return { trouserTop: f.map(y => y < 0 ? y : y - 1), shirtHem: null };
    }
    const b = underwearTopLine('boxers', key, facing, width), p = underwearTopLine('panties', key, facing, width);
    const boxers = b || p, panties = p || b;
    const trouserTop = [], shirtHem = [];
    for (let x = 0; x < width; x++) {
        let u = boxers[x], v = panties[x];
        if (u < 0 && v < 0) { trouserTop.push(-1); shirtHem.push(-1); continue; }
        if (u < 0) u = v;
        if (v < 0) v = u;
        trouserTop.push(Math.min(u, v) - 1);
        shirtHem.push(Math.max(u, v));
    }
    return { trouserTop, shirtHem };
}

const W = CROP * FACINGS.length, H = CROP * KEYS.length;
const out = Buffer.alloc(W * H * 4, 255);
KEYS.forEach((key, r) => FACINGS.forEach((facing, c) => {
    const body = decode(`${WDI}/Things/Pawn/Humanlike/Bodies/Naked_${key}_${facing}.png`);
    const w = body.width;
    const { trouserTop, shirtHem } = waistLines(key, facing, w);
    for (let y = 0; y < CROP; y++) for (let x = 0; x < CROP; x++) {
        const sx = X0 + x, sy = Y0 + y, i = (sy * w + sx) * 4, a = body.data[i + 3] / 255;
        let rgb = [0, 1, 2].map(k => body.data[i + k] * a + 255 * (1 - a));
        if (a > 0) {
            const top = trouserTop[sx], hem = shirtHem ? shirtHem[sx] : -1;
            if (top >= 0 && sy >= top) rgb = rgb.map((v, k) => v * 0.55 + [40, 90, 215][k] * 0.45);
            if (hem < 0 || sy <= hem) rgb = rgb.map((v, k) => v * 0.55 + [215, 40, 40][k] * 0.45);
        }
        const o = ((r * CROP + y) * W + c * CROP + x) * 4;
        out[o] = Math.round(rgb[0]); out[o + 1] = Math.round(rgb[1]); out[o + 2] = Math.round(rgb[2]); out[o + 3] = 255;
        if (x === 0 || y === 0) out[o] = out[o + 1] = out[o + 2] = 170;
    }
}));

const file = path.join(__dirname, '..', 'Art', 'work', 'game-cut-preview.png');
fs.mkdirSync(path.dirname(file), { recursive: true });
encode(file, { width: W, height: H, data: out });
console.log('wrote', file);
