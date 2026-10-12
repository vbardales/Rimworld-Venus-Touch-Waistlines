'use strict';
// Compose the two diagnostic projections without hiding the child's loincloth.
const path = require('path');
const { decode, encode } = require('./png');
const facingIndex = process.argv.indexOf('--facing');
const facing = facingIndex >= 0 ? process.argv[facingIndex + 1] : 'south';
if (!['south', 'east', 'north'].includes(facing)) throw new Error('facing must be south, east, or north');
const art = path.join(__dirname, '..', 'Art', 'work');
const pants = decode(path.join(art, `wdi-child-${facing}-blue-pants-reprojected-over-boxers.png`));
const shirt = decode(path.join(art, `wdi-child-${facing}-red-shirt-waistband-aligned-over-boxers.png`));
const data = Buffer.from(pants.data);
for (let i = 0; i < data.length; i += 4) {
    const r = shirt.data[i], g = shirt.data[i + 1], b = shirt.data[i + 2];
    // The diagnostic shirt is the only red-dominant layer.  Copy its already
    // composited pixels, retaining the pants/loincloth beneath elsewhere.
    if (r > g * 1.25 && r > b * 1.25) {
        data[i] = r; data[i + 1] = g; data[i + 2] = b; data[i + 3] = shirt.data[i + 3];
    }
}
encode(path.join(art, `wdi-child-${facing}-diagnostic-outfit.png`), { width: pants.width, height: pants.height, data });
