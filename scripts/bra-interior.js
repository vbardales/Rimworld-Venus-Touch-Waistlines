'use strict';
// WDI's bra for the four female bodies, as the bust fit uses it: row 1 the bra as drawn, row 2 only its inside (the black lines
// are dropped, shown here as magenta so that the holes can be seen).
//   node bra-interior.js        writes Art/work/bra-interior.png
const path = require('path');
const { decode, encode } = require('./png');
const WDI = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/UWUnderwear/bra';
const BODIES = ['Female', 'Thin_Female', 'Fat_Female', 'Hulk_Female'];
const CW = 340, CH = 140, X0 = 86, Y0 = 220;
const W = CW * BODIES.length, H = CH * 2;
const out = Buffer.alloc(W * H * 4);
for (let i = 0; i < W * H; i++) { out[i * 4] = 150; out[i * 4 + 1] = 150; out[i * 4 + 2] = 140; out[i * 4 + 3] = 255; }
BODIES.forEach((b, c) => {
    const bra = decode(`${WDI}/bra_${b}_south.png`);
    for (let row = 0; row < 2; row++) for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
        const s = ((y + Y0) * bra.width + (x + X0)) * 4, a = bra.data[s + 3] / 255;
        if (a < 0.03) continue;
        const dark = bra.data[s] < 60 && bra.data[s + 1] < 60 && bra.data[s + 2] < 60;
        const d = ((row * CH + y) * W + c * CW + x) * 4;
        const rgb = row === 1 && dark ? [230, 0, 230] : [bra.data[s], bra.data[s + 1], bra.data[s + 2]];
        for (let k = 0; k < 3; k++) out[d + k] = Math.round(rgb[k] * a + out[d + k] * (1 - a));
    }
});
const file = path.join(__dirname, '..', 'Art', 'work', 'bra-interior.png');
encode(file, { width: W, height: H, data: out });
console.log(file);
