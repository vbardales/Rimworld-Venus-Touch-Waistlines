'use strict';
// WDI's naked standard Female next to the naked Female of the Hooman Cute mods.
//   node hooman-bodies.js        writes Art/work/hooman-bodies.png
const path = require('path');
const { decode, encode } = require('./png');
const WS = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100';
const FILES = [
    WS + '/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_Female_south.png',
    WS + '/3366699008/Textures/Things/Pawn/Humanlike/Bodies/Naked_Female_south.png',
    WS + '/3765107071/Textures/Things/Pawn/Humanlike/Bodies/Female_Naked_Female_south.png',
];
const imgs = FILES.map(f => decode(f));
imgs.forEach((im, i) => console.log(i, im.width + 'x' + im.height, FILES[i]));
const W = imgs.reduce((s, im) => s + im.width, 0), H = Math.max(...imgs.map(im => im.height));
const out = Buffer.alloc(W * H * 4);
for (let i = 0; i < W * H; i++) { out[i * 4] = 150; out[i * 4 + 1] = 150; out[i * 4 + 2] = 140; out[i * 4 + 3] = 255; }
let ox = 0;
for (const im of imgs) {
    for (let y = 0; y < im.height; y++) for (let x = 0; x < im.width; x++) {
        const p = (y * im.width + x) * 4, a = im.data[p + 3] / 255;
        if (a === 0) continue;
        const d = (y * W + ox + x) * 4;
        for (let k = 0; k < 3; k++) out[d + k] = Math.round(im.data[p + k] * a + out[d + k] * (1 - a));
    }
    ox += im.width;
}
const file = path.join(__dirname, '..', 'Art', 'work', 'hooman-bodies.png');
encode(file, { width: W, height: H, data: out });
console.log(file);
