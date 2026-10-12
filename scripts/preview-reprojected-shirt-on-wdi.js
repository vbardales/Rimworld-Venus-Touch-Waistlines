'use strict';
// First constrained refit proof: map every occupied row of the original shirt
// into the corresponding WDI body row.  The underwear top is the lower anchor,
// so no shirt pixel can cross into the boxer.
const path = require('path');
const { decode, encode } = require('./png');
const facingIndex = process.argv.indexOf('--facing');
const facing = facingIndex >= 0 ? process.argv[facingIndex + 1] : 'east';
const bodyIndex = process.argv.indexOf('--body');
const bodyType = bodyIndex >= 0 ? process.argv[bodyIndex + 1] : 'Male';
if (!['south', 'east', 'north'].includes(facing)) throw new Error('facing must be south, east, or north');
const donor = {
    Male: 'Male', Female: 'Female_Human_0', Thin: 'Thin', Hulk: 'Hulk', Fat: 'Fat',
    Thin_Female: 'Thin_Human_0', Hulk_Female: 'Hulk', Fat_Female: 'Fat', Child: 'Male'
}[bodyType];
if (!donor) throw new Error(`unknown WDI body type: ${bodyType}`);
const underwear = bodyType === 'Child' ? `loincloth/loincloth_${bodyType}_${facing}` : `boxers/boxers_${bodyType}_${facing}`;
const body = decode(`C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_${bodyType}_${facing}.png`);
const boxers = decode(`C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/UWUnderwear/${underwear}.png`);
const sourceName = `ShirtBasic_${donor}_${facing}`;
const source = decode(`C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/sized-apparel-zero/Textures/Things/Pawn/Humanlike/Apparel/ShirtBasic/${sourceName}.png`);
const { width: w, height: h } = body;
const alpha = (image, x, y) => image.data[(y * w + x) * 4 + 3];
function bounds(image) {
    let top = h, bottom = -1;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (alpha(image, x, y) >= 32) { top = Math.min(top, y); bottom = Math.max(bottom, y); }
    if (bottom < top) throw new Error('empty source');
    return { top, bottom };
}
function run(image, y) {
    let left = -1, right = -1;
    for (let x = 0; x < w; x++) if (alpha(image, x, y) >= 32) { if (left < 0) left = x; right = x; }
    return left < 0 ? null : { left, right };
}
function blend(data, i, rgb, a) {
    for (let c = 0; c < 3; c++) data[i + c] = Math.round(rgb[c] * a + data[i + c] * (1 - a));
    data[i + 3] = Math.max(data[i + 3], Math.round(a * 255));
}
const data = Buffer.from(body.data);
// The underwear is worn first; the shirt overlays its waistband in this view.
for (let i = 0; i < data.length; i += 4) if (boxers.data[i + 3]) {
    const a = boxers.data[i + 3] / 255;
    const l = boxers.data[i] * .3 + boxers.data[i + 1] * .59 + boxers.data[i + 2] * .11;
    blend(data, i, l < 110 ? [65, 48, 24] : [214, 160, 82], a);
}
const bodyBox = bounds(body), sourceBox = bounds(source);
const UNDER_WAISTBAND_OVERLAP = 10; // Two pixels deeper behind the boxer than the prior preview.
// The waistband is not a horizontal row, particularly in profile.  Read its
// upper edge per column and use that curve as the shirt's hem.
const bodyTop = new Int32Array(w).fill(-1);
const waistband = new Int32Array(w).fill(-1);
for (let x = 0; x < w; x++) for (let y = 0; y < h; y++) {
    if (bodyTop[x] < 0 && alpha(body, x, y) >= 32) bodyTop[x] = y;
    if (waistband[x] < 0 && alpha(boxers, x, y) >= 32) waistband[x] = y;
}
// The loincloth's decorative upper fringe is not a waistband.  For children,
// use the first solid run beneath it, then let the normal interpolation make
// that lower seam continuous.
if (bodyType === 'Child') for (let x = 0; x < w; x++) {
    waistband[x] = -1;
    for (let y = 0; y < h - 5; y++) {
        let solid = true;
        for (let yy = y; yy < y + 6; yy++) if (alpha(boxers, x, yy) < 32) { solid = false; break; }
        if (solid) { waistband[x] = y; break; }
    }
}
// The boxer does not occupy every column of a profile sprite.  Its visible
// waistband is nevertheless a continuous garment line, so interpolate that
// line through the front/back columns rather than cutting the shirt away.
for (let x = 0; x < w; x++) {
    if (bodyTop[x] < 0 || waistband[x] >= 0) continue;
    let left = x - 1, right = x + 1;
    while (left >= 0 && waistband[left] < 0) left--;
    while (right < w && waistband[right] < 0) right++;
    if (left >= 0 && right < w) waistband[x] = Math.round(waistband[left] + (waistband[right] - waistband[left]) * (x - left) / (right - left));
    else if (left >= 0) waistband[x] = waistband[left];
    else if (right < w) waistband[x] = waistband[right];
}
if (bodyType === 'Child') {
    const smoothed = new Int32Array(waistband);
    for (let x = 0; x < w; x++) if (waistband[x] >= 0) {
        const values = [];
        for (let dx = -3; dx <= 3; dx++) if (x + dx >= 0 && x + dx < w && waistband[x + dx] >= 0) values.push(waistband[x + dx]);
        values.sort((a, b) => a - b);
        // Move below the complete decorative fringe to the loincloth's
        // lower, usable seam.
        smoothed[x] = Math.min(h - 1, values[Math.floor(values.length / 2)] + 5);
    }
    const active = [];
    for (let x = 0; x < w; x++) if (smoothed[x] >= 0) active.push(x);
    if (facing === 'east') {
        const left = active[0], right = active[active.length - 1];
        for (const x of active) smoothed[x] = Math.round(smoothed[left] + (smoothed[right] - smoothed[left]) * (x - left) / Math.max(1, right - left));
    } else {
        const heights = active.map(x => smoothed[x]).sort((a, b) => a - b);
        const line = heights[Math.floor(heights.length / 2)];
        for (const x of active) smoothed[x] = line;
    }
    for (let x = 0; x < w; x++) if (smoothed[x] >= 0) {
        let fringeTop = -1;
        for (let y = 0; y < h; y++) if (alpha(boxers, x, y) >= 32) { fringeTop = y; break; }
        for (let y = fringeTop; y >= 0 && y < smoothed[x]; y++) {
            const i = (y * w + x) * 4, bi = i;
            data[i] = body.data[bi]; data[i + 1] = body.data[bi + 1]; data[i + 2] = body.data[bi + 2]; data[i + 3] = body.data[bi + 3];
        }
        waistband[x] = smoothed[x];
    }
}
for (let y = bodyBox.top; y < h; y++) {
    const target = run(body, y);
    if (!target) continue;
    for (let x = target.left; x <= target.right; x++) {
        const shirtHem = Math.min(h - 1, waistband[x] + UNDER_WAISTBAND_OVERLAP);
        if (bodyTop[x] < 0 || waistband[x] < 0 || y < bodyTop[x] || y > shirtHem) continue;
        const t = (y - bodyTop[x]) / Math.max(1, shirtHem - bodyTop[x]);
        const sy = Math.round(sourceBox.top + t * (sourceBox.bottom - sourceBox.top));
        const original = run(source, sy) || (bodyType === 'Child' ? { left: 0, right: w - 1 } : null);
        if (!original) continue;
        const u = (x - target.left) / Math.max(1, target.right - target.left);
        const sx = Math.round(original.left + u * (original.right - original.left));
        const si = (sy * w + sx) * 4;
        const a = source.data[si + 3] / 255;
        // The adult donor reaches its own hem.  The scaled child donor does
        // not, so extend only the child mask to the smooth loincloth seam.
        const coverage = a || bodyType === 'Child' ? 1 : 0;
        if (!coverage) continue;
        const l = source.data[si] * .3 + source.data[si + 1] * .59 + source.data[si + 2] * .11;
        // The source hem is deliberately hidden behind the underwear waistband.
        // Its black contour must not become a second red belt above the boxer.
        const edge = sy < sourceBox.bottom - 8 && l < 110;
        blend(data, (y * w + x) * 4, edge ? [145, 20, 20] : [210, 45, 45], coverage * (edge ? .9 : .30));
    }
}
encode(path.join(__dirname, '..', 'Art', 'work', `wdi-${bodyType.toLowerCase()}-${facing}-red-shirt-waistband-aligned-over-boxers.png`), { width: w, height: h, data });
