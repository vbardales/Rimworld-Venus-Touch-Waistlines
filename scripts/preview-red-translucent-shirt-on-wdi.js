'use strict';
// Render-only preview of the intended diagnostic treatment:
// naked WDI body + translucent red cloth + stronger red source contours.
const path = require('path');
const { decode, encode } = require('./png');
const body = decode('C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_Male_east.png');
const shirt = decode('C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/sized-apparel-zero/Textures/Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Male_east.png');
const data = Buffer.from(body.data);
for (let i = 0; i < data.length; i += 4) {
    const sourceAlpha = shirt.data[i + 3] / 255;
    if (sourceAlpha === 0) continue;
    const luma = shirt.data[i] * 0.3 + shirt.data[i + 1] * 0.59 + shirt.data[i + 2] * 0.11;
    const edge = luma < 110;
    const clothAlpha = sourceAlpha * (edge ? 0.9 : 0.30);
    const red = edge ? [145, 20, 20] : [210, 45, 45];
    for (let c = 0; c < 3; c++) data[i + c] = Math.round(red[c] * clothAlpha + data[i + c] * (1 - clothAlpha));
    data[i + 3] = Math.max(data[i + 3], Math.round(clothAlpha * 255));
}
encode(path.join(__dirname, '..', 'Art', 'work', 'wdi-male-east-red-translucent-base-shirt.png'), { width: body.width, height: body.height, data });
