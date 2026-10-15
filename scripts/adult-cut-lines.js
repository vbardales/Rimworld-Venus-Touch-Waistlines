'use strict';
// Shows, on three WDI adult bodies, the two lines of the proposed cut rule:
//   blue  = top of WDI's boxers   (where the trousers would start),
//   green = top of WDI's panties  (where the T-shirt would stop),
//   pink  = the skin left between them where the panties line is the higher one.
//   node adult-cut-lines.js        writes Art/work/adult-cut-lines.png
const path = require('path');
const { decode, encode } = require('./png');

const WDI = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures';
const panels = [['Female', 'south'], ['Male', 'north'], ['Fat_Female', 'north'], ['Hulk_Female', 'south']];
const SCALE = 2, CROP = 256, X0 = 128, Y0 = 200;

function topLine(img) {
    return Array.from({ length: img.width }, (_, x) => {
        for (let y = 0; y < img.height; y++) if (img.data[(y * img.width + x) * 4 + 3] > 0) return y;
        return -1;
    });
}

const W = CROP * SCALE * panels.length, H = CROP * SCALE;
const out = Buffer.alloc(W * H * 4, 255);
function put(px, py, rgb) {
    if (px < 0 || py < 0 || px >= W || py >= H) return;
    const i = (py * W + px) * 4;
    out[i] = rgb[0]; out[i + 1] = rgb[1]; out[i + 2] = rgb[2]; out[i + 3] = 255;
}

panels.forEach(([body, facing], p) => {
    const naked = decode(`${WDI}/Things/Pawn/Humanlike/Bodies/Naked_${body}_${facing}.png`);
    const boxers = topLine(decode(`${WDI}/UWUnderwear/boxers/boxers_${body}_${facing}.png`));
    const panties = topLine(decode(`${WDI}/UWUnderwear/panties/panties_${body}_${facing}.png`));
    const w = naked.width;
    const ox = p * CROP * SCALE;
    for (let y = 0; y < CROP; y++) for (let x = 0; x < CROP; x++) {
        const sx = X0 + x, sy = Y0 + y, i = (sy * w + sx) * 4, a = naked.data[i + 3] / 255;
        let rgb = [0, 1, 2].map(c => Math.round(naked.data[i + c] * a + 255 * (1 - a)));
        const gap = a > 0 && panties[sx] >= 0 && boxers[sx] >= 0 && sy >= panties[sx] && sy < boxers[sx];
        if (gap) rgb = rgb.map((v, c) => Math.round(v * 0.5 + [255, 80, 160][c] * 0.5));
        for (let dy = 0; dy < SCALE; dy++) for (let dx = 0; dx < SCALE; dx++) put(ox + x * SCALE + dx, y * SCALE + dy, rgb);
    }
    for (const [line, rgb] of [[boxers, [40, 90, 230]], [panties, [20, 170, 60]]])
        for (let x = 0; x < CROP; x++) {
            const y = line[X0 + x];
            if (y < 0) continue;
            for (let dx = 0; dx < SCALE; dx++) for (let t = -1; t <= 1; t++) put(ox + x * SCALE + dx, (y - Y0) * SCALE + t, rgb);
        }
    for (let y = 0; y < H; y++) put(ox, y, [170, 170, 170]);
});

const file = path.join(__dirname, '..', 'Art', 'work', 'adult-cut-lines.png');
encode(file, { width: W, height: H, data: out });
console.log('wrote', file);
