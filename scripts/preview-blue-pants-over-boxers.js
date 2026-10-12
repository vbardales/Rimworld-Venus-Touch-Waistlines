'use strict';
// First profile proof for trousers: body, underwear, then translucent blue
// source pants.  The source contours remain visible for alignment review.
const path = require('path');
const { decode, encode } = require('./png');
const body = decode('C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_Male_east.png');
const boxers = decode('C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/UWUnderwear/boxers/boxers_Male_east.png');
const pants = decode('C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/sized-apparel-zero/Mods/Visible Pants/Textures/Core/Things/Pawn/Humanlike/Apparel/Pants/Pants_Male_east.png');
const data = Buffer.from(body.data);
function blend(i, rgb, a) {
    for (let c = 0; c < 3; c++) data[i + c] = Math.round(rgb[c] * a + data[i + c] * (1 - a));
    data[i + 3] = Math.max(data[i + 3], Math.round(a * 255));
}
for (let i = 0; i < data.length; i += 4) if (boxers.data[i + 3]) {
    const a = boxers.data[i + 3] / 255;
    const l = boxers.data[i] * .3 + boxers.data[i + 1] * .59 + boxers.data[i + 2] * .11;
    blend(i, l < 110 ? [65, 48, 24] : [214, 160, 82], a);
}
for (let i = 0; i < data.length; i += 4) if (pants.data[i + 3]) {
    const a = pants.data[i + 3] / 255;
    const l = pants.data[i] * .3 + pants.data[i + 1] * .59 + pants.data[i + 2] * .11;
    const edge = l < 110;
    blend(i, edge ? [20, 55, 145] : [40, 90, 215], a * (edge ? .9 : .30));
}
encode(path.join(__dirname, '..', 'Art', 'work', 'wdi-male-east-blue-pants-over-boxers-unfitted.png'), { width: body.width, height: body.height, data });
