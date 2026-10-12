'use strict';
// Uncorrected diagnostic composite: the source shirt is placed as-is on WDI.
// This deliberately exposes the mismatch that the refit must solve.
const path = require('path');
const { decode, encode } = require('./png');
const root = path.join(__dirname, '..');
const body = decode('C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_Male_east.png');
const shirt = decode('C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/sized-apparel-zero/Textures/Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Male_east.png');
const data = Buffer.from(body.data);
for (let i = 0; i < data.length; i += 4) {
    const a = shirt.data[i + 3] / 255;
    if (a === 0) continue;
    for (let c = 0; c < 3; c++) data[i + c] = Math.round(shirt.data[i + c] * a + data[i + c] * (1 - a));
    data[i + 3] = Math.max(data[i + 3], shirt.data[i + 3]);
}
encode(path.join(root, 'Art', 'work', 'wdi-male-east-base-shirt-unfitted.png'), { width: body.width, height: body.height, data });
