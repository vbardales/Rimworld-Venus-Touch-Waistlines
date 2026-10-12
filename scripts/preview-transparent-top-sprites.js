'use strict';
// Preview only: composites the existing RGBA sprites over a checkerboard.
// It never alters the source PNGs.
const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');

const root = path.join(__dirname, '..', 'Mod', 'Textures', 'Venus', 'Diagnostics', 'TransparentTop');
const output = path.join(__dirname, '..', 'Art', 'work', 'transparent-top-male-sprites.png');
const dirs = ['south', 'east', 'north'];
const tile = 512;
const data = Buffer.alloc(tile * dirs.length * tile * 4);
for (let y = 0; y < tile; y++) for (let x = 0; x < tile * dirs.length; x++) {
    const c = ((Math.floor(x / 32) + Math.floor(y / 32)) & 1) ? 210 : 170;
    const i = (y * tile * dirs.length + x) * 4;
    data[i] = data[i + 1] = data[i + 2] = c; data[i + 3] = 255;
}
dirs.forEach((dir, column) => {
    const sprite = decode(path.join(root, `Top_Male_${dir}.png`));
    for (let y = 0; y < tile; y++) for (let x = 0; x < tile; x++) {
        const source = (y * tile + x) * 4;
        const target = (y * tile * dirs.length + column * tile + x) * 4;
        const alpha = sprite.data[source + 3] / 255;
        for (let channel = 0; channel < 3; channel++)
            data[target + channel] = Math.round(sprite.data[source + channel] * alpha + data[target + channel] * (1 - alpha));
    }
});
encode(output, { width: tile * dirs.length, height: tile, data });
console.log(path.relative(path.join(__dirname, '..'), output));
