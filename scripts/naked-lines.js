'use strict';
// The naked WDI bodies from the front, the side and the back, with the two lines the mod cares about.
//   node naked-lines.js            writes Art/work/naked-lines-men.png and naked-lines-women.png
//
// Blue: where a shirt is cut. The top edge of WDI's underwear (boxers or panties) for the same body and facing, column by
// column on the front and the back; a straight line at the body's underwear height on the side (what ShirtCut does).
// Green: the top edge of the trousers' art as General Textures Collection ships it (Pants_<body>_<facing>), column by
// column. This is the raw art, before the mod stretches its top to the navel, so it is where the trousers start in the file,
// not necessarily where they end up in the game.
const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');

const WDI = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures';
const KAS = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3789119336/Mods/VisiblePants/Textures/Core/Things/Pawn/Humanlike/Apparel/Pants';
const OUT = path.join(__dirname, '..', 'Art', 'work');
const WITH_UNDERWEAR = process.argv.includes('--underwear');
const LINE = { Male: 0.711, Female: 0.686, Thin: 0.699, Thin_Female: 0.674, Fat: 0.643, Fat_Female: 0.643, Hulk: 0.799, Hulk_Female: 0.783 };
const SETS = { men: ['Male', 'Thin', 'Fat', 'Hulk'], women: ['Female', 'Thin_Female', 'Fat_Female', 'Hulk_Female'] };
const FACINGS = ['south', 'east', 'north'];
const CELL = 340, X0 = 86, Y0 = 130, SPAN = 340;      // crop of the 512 picture: x 86..426, y 130..470, drawn at 1:1

function read(file) { return fs.existsSync(file) ? decode(file) : null; }

// first opaque row of every column, or -1
function tops(img) {
    const t = new Array(img.width).fill(-1);
    for (let x = 0; x < img.width; x++)
        for (let y = 0; y < img.height; y++)
            if (img.data[(y * img.width + x) * 4 + 3] >= 128) { t[x] = y; break; }
    return t;
}

function put(canvas, W, x, y, r, g, b) {
    if (x < 0 || y < 0 || x >= W || y >= canvas.length / (W * 4)) return;
    const i = (y * W + x) * 4; canvas[i] = r; canvas[i + 1] = g; canvas[i + 2] = b; canvas[i + 3] = 255;
}

for (const [name, bodies] of Object.entries(SETS)) {
    const W = CELL * bodies.length, H = CELL * FACINGS.length;
    const canvas = Buffer.alloc(W * H * 4);
    for (let i = 0; i < W * H; i++) { canvas[i * 4] = 150; canvas[i * 4 + 1] = 150; canvas[i * 4 + 2] = 140; canvas[i * 4 + 3] = 255; }
    bodies.forEach((body, c) => FACINGS.forEach((facing, r) => {
        const img = read(`${WDI}/Things/Pawn/Humanlike/Bodies/Naked_${body}_${facing}.png`);
        if (!img) return;
        const ox = c * CELL, oy = r * CELL;
        for (let y = 0; y < SPAN; y++) for (let x = 0; x < SPAN; x++) {
            const s = ((y + Y0) * img.width + (x + X0)) * 4, a = img.data[s + 3] / 255;
            if (a <= 0) continue;
            const d = ((oy + y) * W + (ox + x)) * 4;
            for (let k = 0; k < 3; k++) canvas[d + k] = Math.round(img.data[s + k] * a + canvas[d + k] * (1 - a));
        }
        // blue: the shirt cut
        const kind = body.startsWith('Male') || ['Thin', 'Fat', 'Hulk'].includes(body) ? 'boxers' : 'panties';
        const uw = read(`${WDI}/UWUnderwear/${kind}/${kind}_${body}_${facing}.png`);
        if (WITH_UNDERWEAR && uw) for (let y = 0; y < SPAN; y++) for (let x = 0; x < SPAN; x++) {
            const s2 = ((y + Y0) * uw.width + (x + X0)) * 4, a = uw.data[s2 + 3] / 255;
            if (a <= 0) continue;
            const d = ((oy + y) * W + (ox + x)) * 4;
            for (let k = 0; k < 3; k++) canvas[d + k] = Math.round(uw.data[s2 + k] * a + canvas[d + k] * (1 - a));
        }
        const uwTop = uw ? tops(uw) : null;
        for (let x = 0; x < SPAN; x++) {
            let y = facing === 'east' || !uwTop ? Math.round(LINE[body] * 512) : uwTop[x + X0];
            if (y < 0) continue;
            for (let t = 0; t < 2; t++) put(canvas, W, ox + x, oy + y - Y0 + t, 20, 60, 255);
        }
        // green: the trousers' art
        const pants = read(`${KAS}/Pants_${body}_${facing}.png`);
        if (pants) {
            const pt = tops(pants);
            for (let x = 0; x < SPAN; x++) {
                const y = pt[x + X0];
                if (y < 0) continue;
                for (let t = 0; t < 2; t++) put(canvas, W, ox + x, oy + y - Y0 + t, 0, 170, 40);
            }
        }
    }));
    const file = path.join(OUT, `naked-lines${WITH_UNDERWEAR ? '-slip' : ''}-${name}.png`);
    encode(file, { width: W, height: H, data: canvas });
    console.log(file);
}
