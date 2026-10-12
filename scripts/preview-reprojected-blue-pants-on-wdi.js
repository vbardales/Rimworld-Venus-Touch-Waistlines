'use strict';
// Map the source pants onto the exact profile silhouette of WDI's boxer.
// This is the lower-garment analogue of the approved shirt experiment.
const path = require('path');
const { decode, encode } = require('./png');
const facingIndex = process.argv.indexOf('--facing');
const facing = facingIndex >= 0 ? process.argv[facingIndex + 1] : 'east';
const bodyIndex = process.argv.indexOf('--body');
const bodyType = bodyIndex >= 0 ? process.argv[bodyIndex + 1] : 'Male';
const noLegSplit = process.argv.includes('--no-leg-split');
if (!['south', 'east', 'north'].includes(facing)) throw new Error('facing must be south, east, or north');
const donor = {
    Male: 'Male', Female: 'Female', Thin: 'Thin', Hulk: 'Hulk', Fat: 'Fat',
    Thin_Female: 'Thin', Hulk_Female: 'Hulk', Fat_Female: 'Fat', Child: 'Male'
}[bodyType];
if (!donor) throw new Error(`unknown WDI body type: ${bodyType}`);
const underwear = bodyType === 'Child' ? `loincloth/loincloth_${bodyType}_${facing}` : `boxers/boxers_${bodyType}_${facing}`;
const body = decode(`C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_${bodyType}_${facing}.png`);
const boxers = decode(`C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures/UWUnderwear/${underwear}.png`);
const source = decode(`C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/sized-apparel-zero/Mods/Visible Pants/Textures/Core/Things/Pawn/Humanlike/Apparel/Pants/Pants_${donor}_${facing}.png`);
const { width: w, height: h } = body;
const alpha = (img, x, y) => img.data[(y * w + x) * 4 + 3];
function bounds(img) { let top = h, bottom = -1; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (alpha(img, x, y) >= 32) { top = Math.min(top, y); bottom = Math.max(bottom, y); } return { top, bottom }; }
function run(img, y) { let left = -1, right = -1; for (let x = 0; x < w; x++) if (alpha(img, x, y) >= 32) { if (left < 0) left = x; right = x; } return left < 0 ? null : { left, right }; }
function blend(data, i, rgb, a) { for (let c = 0; c < 3; c++) data[i + c] = Math.round(rgb[c] * a + data[i + c] * (1 - a)); data[i + 3] = Math.max(data[i + 3], Math.round(a * 255)); }
const data = Buffer.from(body.data);
for (let i = 0; i < data.length; i += 4) if (boxers.data[i + 3]) { const a = boxers.data[i + 3] / 255; const l = boxers.data[i] * .3 + boxers.data[i + 1] * .59 + boxers.data[i + 2] * .11; blend(data, i, l < 110 ? [65, 48, 24] : [214, 160, 82], a); }
const sourceBox = bounds(source);
const waistband = new Int32Array(w).fill(-1);
const bodyBottom = new Int32Array(w).fill(-1);
for (let x = 0; x < w; x++) for (let y = 0; y < h; y++) {
    // Include the first anti-aliased pixel: the visible waistband begins
    // there, not at the later fully opaque pixel.
    if (waistband[x] < 0 && alpha(boxers, x, y) > 0) waistband[x] = y;
    if (alpha(body, x, y) >= 32) bodyBottom[x] = y;
}
// The child loincloth has a jagged decorative fringe at its top.  Its first
// six-pixel solid vertical run is the lower, smooth seam used as underwear.
if (bodyType === 'Child') for (let x = 0; x < w; x++) {
    waistband[x] = -1;
    for (let y = 0; y < h - 5; y++) {
        let solid = true;
        for (let yy = y; yy < y + 6; yy++) if (alpha(boxers, x, yy) < 32) { solid = false; break; }
        if (solid) { waistband[x] = y; break; }
    }
}
// Preserve the actual boxer span before extending its anchor curve over the
// rest of the lower-body silhouette.
let boxerLeft = -1, boxerRight = -1;
for (let x = 0; x < w; x++) if (waistband[x] >= 0) { boxerLeft = x; break; }
for (let x = w - 1; x >= 0; x--) if (waistband[x] >= 0) { boxerRight = x; break; }
// Boxer sprites do not occupy every lower-body column.  Interpolate their
// waistband curve across those columns: it anchors the trousers without
// clipping their legs to the boxer silhouette.
for (let x = 0; x < w; x++) {
    if (bodyBottom[x] < 0 || waistband[x] >= 0) continue;
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
// A trouser waistband is one deliberate arc, not the collection of small
// notches found in underwear artwork.  Smooth front/rear views from each
// flank to the low point at the centre, so it never hooks toward the crotch.
if (facing !== 'east') {
    let left = -1, right = -1;
    for (let x = 0; x < w; x++) if (waistband[x] >= 0) { left = x; break; }
    for (let x = w - 1; x >= 0; x--) if (waistband[x] >= 0) { right = x; break; }
    if (left >= 0 && right > left) {
        const edge = Math.round((waistband[left] + waistband[right]) / 2);
        let low = edge;
        for (let x = left; x <= right; x++) low = Math.max(low, waistband[x]);
        for (let x = left; x <= right; x++) {
            const u = (x - left) / (right - left);
            waistband[x] = Math.round(edge + (low - edge) * 4 * u * (1 - u));
        }
    }
}
// Unlike a top hem (which sits below the underwear waistband), trousers
// overlap it by their first visible edge from above.
const PANTS_ABOVE_WAISTBAND = 1;
for (let x = 0; x < w; x++) if (waistband[x] >= 0) waistband[x] -= PANTS_ABOVE_WAISTBAND;
// A pants hem belongs at the body's lower edge.  The boxer defines only its
// upper anchor, never its total height.
const pants = new Uint8Array(w * h);
for (let y = 0; y < h; y++) {
    const target = run(body, y);
    if (!target) continue;
    for (let x = target.left; x <= target.right; x++) {
        if (waistband[x] < 0 || bodyBottom[x] < 0 || y < waistband[x] || y > bodyBottom[x]) continue;
        const t = (y - waistband[x]) / Math.max(1, bodyBottom[x] - waistband[x]);
        const sy = Math.round(sourceBox.top + t * (sourceBox.bottom - sourceBox.top));
        const original = run(source, sy);
        if (!original) continue;
        const u = (x - target.left) / Math.max(1, target.right - target.left);
        const sx = Math.round(original.left + u * (original.right - original.left));
        const si = (sy * w + sx) * 4, a = source.data[si + 3] / 255;
        const l = source.data[si] * .3 + source.data[si + 1] * .59 + source.data[si + 2] * .11;
        // The top edge is defined by WDI's boxer waist, never by a gap in
        // the donor sprite.  This gives the trousers the exact same curve.
        const waistEdge = y <= waistband[x] + 2;
        // Donor ink includes an inner double-leg contour (a W).  It is not
        // applicable to WDI's single lower arc, so retain only our explicit
        // waistband and hem outlines.
        const dark = waistEdge;
        blend(data, (y * w + x) * 4, dark ? [20, 55, 145] : [40, 90, 215], dark ? .9 : .30);
        pants[y * w + x] = 1;
    }
}
// Define one lower arc across both legs.  In particular, do not let the
// anatomical crotch notch bend the blue hem upward; the black leg split owns
// that area instead.
const hemLeft = boxerLeft, hemRight = boxerRight;
if (hemLeft >= 0 && hemRight > hemLeft) {
    const hemEdge = Math.round((bodyBottom[hemLeft] + bodyBottom[hemRight]) / 2);
    let hemLow = hemEdge;
    for (let x = hemLeft; x <= hemRight; x++) hemLow = Math.max(hemLow, bodyBottom[x]);
    for (let x = hemLeft; x <= hemRight; x++) {
        const u = (x - hemLeft) / (hemRight - hemLeft);
        const hemY = Math.round(hemEdge + (hemLow - hemEdge) * 4 * u * (1 - u));
        // Fill any central anatomical indentation through to the garment hem.
        for (let y = Math.max(waistband[x], bodyBottom[x] + 1); y < hemY; y++) {
            blend(data, (y * w + x) * 4, [40, 90, 215], .30);
            pants[y * w + x] = 1;
        }
        for (let y = Math.max(0, hemY - 1); y <= hemY; y++) blend(data, (y * w + x) * 4, [20, 55, 145], .9);
    }
}
// A full-length pair of trousers separates the two legs on frontal/rear
// sprites.  Short garments deliberately do not get this treatment.
if (facing !== 'east' && !noLegSplit) {
    let top = h, bottom = -1;
    for (let x = 0; x < w; x++) if (waistband[x] >= 0 && bodyBottom[x] >= 0) {
        top = Math.min(top, waistband[x]);
        bottom = Math.max(bottom, bodyBottom[x]);
    }
    // The black triangle reaches the slip: it is the deliberate visual split
    // between the two trouser legs.
    const splitStart = Math.round(top + (bottom - top) * .53);
    const middle = Math.floor(w / 2);
    for (let y = splitStart; y <= bottom; y++) {
        const target = run(body, y);
        if (!target) continue;
        const spread = 1 + Math.round((y - splitStart) * 7 / Math.max(1, bottom - splitStart));
        for (let x = Math.max(target.left, middle - spread); x <= Math.min(target.right, middle + spread); x++) {
            // Permit the separator to bridge the natural gap once the legs
            // split, so it remains a continuous black triangle.
            const i = (y * w + x) * 4;
            data[i] = data[i + 1] = data[i + 2] = 0;
            data[i + 3] = 255;
        }
    }
}
encode(path.join(__dirname, '..', 'Art', 'work', `wdi-${bodyType.toLowerCase()}-${facing}-blue-pants-reprojected-over-boxers.png`), { width: w, height: h, data });
