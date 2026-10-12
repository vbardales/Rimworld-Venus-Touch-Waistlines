'use strict';
// Preview only: naked WDI body, its boxer, then the translucent source shirt.
const path = require('path');
const { decode, encode } = require('./png');
const body = decode('C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_Male_east.png');
const boxers = decode('C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/UWUnderwear/boxers/boxers_Male_east.png');
const shirt = decode('C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/sized-apparel-zero/Textures/Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_Male_east.png');
const data = Buffer.from(body.data);
function blend(i, rgb, alpha) {
    for (let c = 0; c < 3; c++) data[i + c] = Math.round(rgb[c] * alpha + data[i + c] * (1 - alpha));
    data[i + 3] = Math.max(data[i + 3], Math.round(alpha * 255));
}
for (let i = 0; i < data.length; i += 4) {
    const a = boxers.data[i + 3] / 255;
    if (a) {
        const luma = boxers.data[i] * 0.3 + boxers.data[i + 1] * 0.59 + boxers.data[i + 2] * 0.11;
        blend(i, luma < 110 ? [65, 48, 24] : [214, 160, 82], a);
    }
    const shirtAlpha = shirt.data[i + 3] / 255;
    if (shirtAlpha) {
        const luma = shirt.data[i] * 0.3 + shirt.data[i + 1] * 0.59 + shirt.data[i + 2] * 0.11;
        const edge = luma < 110;
        blend(i, edge ? [145, 20, 20] : [210, 45, 45], shirtAlpha * (edge ? 0.9 : 0.30));
    }
}
encode(path.join(__dirname, '..', 'Art', 'work', 'wdi-male-east-red-shirt-over-boxers.png'), { width: body.width, height: body.height, data });
