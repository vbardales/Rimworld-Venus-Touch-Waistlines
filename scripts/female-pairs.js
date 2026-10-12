'use strict';
// Every standard-Female south picture of the clothing mods under test, each next to WDI's naked standard Female.
//   node female-pairs.js        writes Art/work/female-pairs-<n>.png (6 pairs per sheet)
const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');
const WS = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100';
const NAKED = WS + '/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_Female_south.png';
const A = 'Textures/Things/Pawn/Humanlike/Apparel';
const list = [
    ...['UNARoyalDress', 'UNA_dressR', 'UNA_Dress_sitagi', 'UNA_F_sitadoresu', 'UNA_gothicdress', 'UNA_MstyleShirtpants', 'UNA_RibbonDress', 'UNA_RoyalRobe'].map(n => `3352990362/${A}/${n}/${n}_Female_south.png`),
    `3301577366/${A}/UNABmaidsuit/UNAmaidsuit_Female_south.png`, `3301577366/${A}/UNA_FlakDress/UNA_FlakDress_Female_south.png`, `3301577366/${A}/UNA_PlateDress/UNA_PlateDress_Female_south.png`,
    ...['UNAGIapaka', 'UNAGImohukepu'].map(n => `3266399912/${A}/${n}/${n}_Female_south.png`),
    ...['UNAGInoEshirt', 'UNAGInoSDs'].map(n => `3253298952/${A}/${n}/${n}_Female_south.png`),
    ...['UNAdotera', 'UNAkariginu', 'UNAwaboudan', 'UNAwahaori', 'UNAwasitagi'].map(n => `3297676809/${A}/${n}/${n}_Female_south.png`),
    ...['UNAcafe_belt', 'UNAcafe_epuron', 'UNAcafe_wanpi'].map(n => `3325530853/${A}/${n}/${n}_Female_south.png`),
    ...['FlakiniVest', 'MicroSkirt', 'TubeTop'].map(n => `3275648920/Textures/Things/Apparel/${n}/${n}_Female_south.png`),
    ...['ChefMaid', 'CleanerMaid', 'CrafterMaid', 'FightMaid', 'HeaderMaid', 'NurseMaid'].map(n => `1498756997/Textures/Things/Apparel/${n}_Female_south.png`),
];
const X0 = 96, Y0 = 70, CW = 320, CH = 400, PER = 6, COLS = 2;
// every body type a garment is drawn for: garment suffix -> WDI naked picture
const TYPES = [['Female', 'Female'], ['Male', 'Male'], ['Thin', 'Thin_Female'], ['Fat', 'Fat_Female'], ['Hulk', 'Hulk_Female']];
const only = process.argv[2];
for (const [type, bodyKey] of TYPES) {
if (only && only !== type) continue;
const naked = decode(NAKED.replace('Naked_Female_south', `Naked_${bodyKey}_south`));
const have = list.map(r => r.replace('_Female_south', `_${type}_south`)).filter(r => fs.existsSync(`${WS}/${r}`));
console.log(`${type}: ${have.length} of ${list.length} garments have a picture`);
for (let s = 0; s * PER < have.length; s++) {
    const items = have.slice(s * PER, s * PER + PER);
    const rows = Math.ceil(items.length / COLS), W = COLS * CW * 2, H = rows * CH;
    const out = Buffer.alloc(W * H * 4);
    for (let i = 0; i < W * H; i++) { out[i * 4] = 150; out[i * 4 + 1] = 150; out[i * 4 + 2] = 140; out[i * 4 + 3] = 255; }
    const paste = (img, ox, oy) => {
        for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
            const sx = x + X0, sy = y + Y0;
            if (sx >= img.width || sy >= img.height) continue;
            const p = (sy * img.width + sx) * 4, a = img.data[p + 3] / 255;
            if (a === 0) continue;
            const d = ((oy + y) * W + ox + x) * 4;
            for (let k = 0; k < 3; k++) out[d + k] = Math.round(img.data[p + k] * a + out[d + k] * (1 - a));
        }
    };
    items.forEach((rel, i) => {
        const col = i % COLS, row = Math.floor(i / COLS);
        paste(naked, col * CW * 2, row * CH);
        const f = `${WS}/${rel}`;
        if (fs.existsSync(f)) paste(decode(f), col * CW * 2 + CW, row * CH);
        console.log(`sheet ${s + 1} cell ${i + 1}: ${path.basename(rel)}`);
    });
    const file = path.join(__dirname, '..', 'Art', 'work', `pairs-${type}-${s + 1}.png`);
    encode(file, { width: W, height: H, data: out });
    console.log(file);
}
}
