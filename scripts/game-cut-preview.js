'use strict';
// The cut rule exactly as WdiAppPatterns applies it in game, drawn offline on WDI's bodies: the
// reference the Pickle captures are compared with. One row per WDI texture, south / east / north.
//   blue  = trousers, from one row above the higher of WDI's boxers and panties lines,
//   red   = shirt, down to the lower of the two lines (purple where both overlap),
//   children: trousers from the smoothed fundoshi line, shirt with no hem cut.
//   node game-cut-preview.js        writes Art/work/game-cut-preview.png
// Keep in step with Source/TailorMadeWaistlines/WdiAppPatterns.cs (WaistLines, CombineUnderwearLines,
// UnderwearTopLine, SmoothChildFundoshiLine, AlphaMask).
const fs = require('fs');
const path = require('path');
const { decode, encode } = require('./png');

const WDI = 'C:/Program Files (x86)/Steam/steamapps/workshop/content/294100/3527486510/Textures';
const argOf = name => { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : null; };
// --keys A,B --facings north,east --scale N: a few bodies, enlarged (nearest neighbour), to read single pixels.
const KEYS = argOf('--keys') ? argOf('--keys').split(',') : ['Male', 'Female', 'Thin', 'Thin_Female', 'Hulk', 'Hulk_Female', 'Fat', 'Fat_Female', 'Child'];
const FACINGS = argOf('--facings') ? argOf('--facings').split(',') : ['south', 'east', 'north'];
const SCALE = parseInt(argOf('--scale'), 10) || 1;
const CROP = 320, X0 = 96, Y0 = 120;

function underwearTopLine(kind, key, facing, width) {
    const file = `${WDI}/UWUnderwear/${kind}/${kind}_${key}_${facing}.png`;
    if (!fs.existsSync(file)) return null;
    const img = decode(file);
    const line = new Array(width).fill(-1);
    for (let x = 0; x < width; x++) {
        const sx = Math.min(img.width - 1, Math.floor(x * img.width / width));
        for (let y = 0; y < img.height; y++) if (img.data[(y * img.width + sx) * 4 + 3] !== 0) { line[x] = y; break; }
    }
    extrapolateToBody(line, key, facing);
    let last = -1;
    for (let x = 0; x < width; x++) { if (line[x] >= 0) last = line[x]; else if (last >= 0) line[x] = last; }
    last = -1;
    for (let x = width - 1; x >= 0; x--) { if (line[x] >= 0) last = line[x]; else if (last >= 0) line[x] = last; }
    return line;
}

// The rule (Virginie, 2026-10-18): follow the edge of the underwear as drawn, and at each side, where the sprite's rounded
// corner begins, extrapolate the line out to the white pixels of the body.  The corner is the stretch of outer columns whose
// step to the next one is more than HOOK rows (5 to 14 rows in 3 to 5 columns on the front and back, up to 37 rows over 15
// columns on the back of a profile); from the first smooth column the slope is measured over WINDOW columns and carried on
// outward to the body's last column, replacing the corner.  Keep in step with WdiAppPatterns.ExtrapolateToBody.
const HOOK = 2, WINDOW = 10, MAX_CORNER = 90;   // a corner never takes more than a third of the sprite
function bodyExtent(key, facing) {
    const body = decode(`${WDI}/Things/Pawn/Humanlike/Bodies/Naked_${key}_${facing}.png`);
    let min = body.width, max = -1;
    for (let y = 0; y < body.height; y++) for (let x = 0; x < body.width; x++) if (body.data[(y * body.width + x) * 4 + 3]) { if (x < min) min = x; if (x > max) max = x; }
    return { min, max };
}
// A parabola through the three interior points y0 (the first smooth column), y1 and y2 (WINDOW and 2 WINDOW columns further in),
// followed outward for SMOOTH columns, then straight on with the slope it reached: the line leaves the corner with the curve it
// had inside, not at an angle.  s = columns outward from y0.
const SMOOTH = 16;
function extend(y0, y1, y2, s) {
    const d1 = y1 - y0, d2 = y2 - y0, c = (d2 - 2 * d1) / (WINDOW * WINDOW), b = d1 / WINDOW - 0.5 * c * WINDOW;
    const sc = Math.min(s, SMOOTH);
    let y = y0 - b * sc + 0.5 * c * sc * sc;
    if (s > SMOOTH) y += (-b + c * SMOOTH) * (s - SMOOTH);
    return Math.round(y);
}
function extrapolateToBody(line, key, facing) {
    const first = line.findIndex(v => v >= 0);
    let last = line.length - 1; while (last >= 0 && line[last] < 0) last--;
    if (first < 0 || last - first < 60) return;
    const corner = Math.min(MAX_CORNER, Math.floor((last - first) / 3) - WINDOW);
    const { min, max } = bodyExtent(key, facing);
    // the corner ends where the line stops moving against its dominant direction (the top of the buttock on a profile, the bottom of the hook on the front and back) and is no longer steep
    const lead = Math.sign(line[first + corner + WINDOW] - line[first + corner]);
    let a = first; while (a < first + corner && ((lead && (line[a + 1] - line[a]) * lead < 0) || Math.abs(line[a + 1] - line[a]) > HOOK)) a++;
    for (let x = a - 1; x >= Math.min(min, first); x--) line[x] = extend(line[a], line[a + WINDOW], line[a + 2 * WINDOW], a - x);
    const trail = Math.sign(line[last - corner - WINDOW] - line[last - corner]);
    let b = last; while (b > last - corner && ((trail && (line[b - 1] - line[b]) * trail < 0) || Math.abs(line[b - 1] - line[b]) > HOOK)) b--;
    for (let x = b + 1; x <= Math.max(max, last); x++) line[x] = extend(line[b], line[b - WINDOW], line[b - 2 * WINDOW], x - b);
}
// The child profile follows the fundoshi edge, which ripples by 1 to 3 rows: a moving average over 2 * RIPPLE + 1 columns takes it
// out and keeps the slope and the curve of the back (Virginie, 2026-10-18).  Keep in step with WdiAppPatterns.SmoothRipple.
const RIPPLE = 8;
function smoothRipple(line) {
    const src = line.slice();
    for (let x = 0; x < line.length; x++) {
        if (src[x] < 0) continue;
        let sum = 0, n = 0;
        for (let k = Math.max(0, x - RIPPLE); k <= Math.min(line.length - 1, x + RIPPLE); k++) if (src[k] >= 0) { sum += src[k]; n++; }
        line[x] = Math.round(sum / n);
    }
}

function smoothChildFundoshiLine(waist, facing) {
    const values = waist.filter(v => v >= 0).sort((a, b) => a - b);
    if (!values.length) return;
    if (facing !== 'east') {
        const line = values[values.length >> 1] + 1;
        for (let x = 0; x < waist.length; x++) if (waist[x] >= 0) waist[x] = line;
        return;
    }
    const first = waist.findIndex(v => v >= 0);
    let last = waist.length - 1; while (waist[last] < 0) last--;
    if (last <= first) return;
    const from = waist[first] + 1, to = waist[last] + 1;
    for (let x = first; x <= last; x++) waist[x] = from + Math.trunc((to - from) * (x - first) / (last - first));
}

function waistLines(key, facing, width) {
    if (key === 'Child') {
        // The child's two lines are the fundoshi's edge (Virginie, 2026-10-18): the shirt ends on it, the trousers start one row
        // above it.  Front and back keep the flat smoothing (the sprite's top ripples by 2 rows); the profile follows the edge,
        // extrapolated at the back like the adults', instead of a straight slope between its two ends.
        const f = underwearTopLine('loincloth', key, facing, width);
        if (facing !== 'east') smoothChildFundoshiLine(f, facing); else smoothRipple(f);
        return { trouserTop: f.map(y => y < 0 ? y : y - 1), shirtHem: f.slice() };
    }
    const b = underwearTopLine('boxers', key, facing, width), p = underwearTopLine('panties', key, facing, width);
    // Each line follows its own sprite (Virginie, 2026-10-18): the slip (panties) gives the top of the trousers, the boxers the
    // hem of the shirt.  Following the lower of the two for both put a man's hem on a smile below the boxers' flat top, and the
    // boxers alone for both left the trousers unrelated to the slip.  Keep in step with WdiAppPatterns.CombineUnderwearLines.
    const boxers = b || p, panties = p || b;
    const trouserTop = [], shirtHem = [];
    for (let x = 0; x < width; x++) {
        let u = boxers[x], v = panties[x];
        if (u < 0 && v < 0) { trouserTop.push(-1); shirtHem.push(-1); continue; }
        if (u < 0) u = v;
        if (v < 0) v = u;
        trouserTop.push(v - 1);
        shirtHem.push(u);
    }
    // Where the boxers' edge is higher than the slip's, bare skin is left between the two lines.  Both lines move apart by half of the
    // largest such gap of the body and facing (the hem down, the trousers up), so they meet there and overlap elsewhere (Virginie,
    // 2026-10-18).  Keep in step with WdiAppPatterns.CombineUnderwearLines.
    let gap = 0;
    for (let x = 0; x < width; x++) if (shirtHem[x] >= 0) gap = Math.max(gap, trouserTop[x] - shirtHem[x] - 1);
    const shift = Math.ceil(gap / 2);
    if (shift > 0) for (let x = 0; x < width; x++) if (shirtHem[x] >= 0) { shirtHem[x] += shift; trouserTop[x] -= shift; }
    return { trouserTop, shirtHem };
}

// --ring: draw only the border of each cut mask (the garment outline, interior left empty), as the ring a
// translucent garment would show.  A mask pixel is on the ring when a pixel within RING px of it is outside the
// mask: transparent body, or a row cut away by the waist rule.  So the cut line itself is part of the ring.
//   node game-cut-preview.js --ring [top [bottom]]   writes Art/work/game-cut-ring-<top>-<bottom>px-preview.png
// top = ring thickness of the shirt, bottom = of the trousers (default 2 and 3); where both rings meet, the shirt's colour wins.
// --underwear: the WDI boxers (orange) with the shirt hem (red line) over them, to see what the hem follows.  Panties,
// loincloth and the trousers' line are left out on purpose (Virginie, 2026-10-18).
//   node game-cut-preview.js --underwear   writes Art/work/game-cut-underwear-preview.png
// --slip (with --underwear): the panties (green) and the top of the trousers (blue line) instead of the boxers and the hem.
const SLIP = process.argv.includes('--slip') || process.argv.includes('--fundoshi');   // --fundoshi: the child's loincloth (violet) and the top of its trousers (blue line)
const UW_MODE = process.argv.includes('--underwear');
const RING_MODE = process.argv.includes('--ring');
const ringArg = i => Math.max(0, parseInt(process.argv[process.argv.indexOf('--ring') + i], 10) || 0);
const RING_TOP = ringArg(1) || 2, RING_BOTTOM = ringArg(2) || (ringArg(1) ? RING_TOP : 3);

function ringOf(inMask, w, h, RING) {
    const ring = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        if (!inMask[y * w + x]) continue;
        search: for (let dy = -RING; dy <= RING; dy++) for (let dx = -RING; dx <= RING; dx++) {
            if (dx * dx + dy * dy > RING * RING) continue;
            const nx = x + dx, ny = y + dy;
            if (nx < 0 || ny < 0 || nx >= w || ny >= h || !inMask[ny * w + nx]) { ring[y * w + x] = 1; break search; }
        }
    }
    return ring;
}

const W = CROP * FACINGS.length, H = CROP * KEYS.length;
const out = Buffer.alloc(W * H * 4, 255);
KEYS.forEach((key, r) => FACINGS.forEach((facing, c) => {
    const body = decode(`${WDI}/Things/Pawn/Humanlike/Bodies/Naked_${key}_${facing}.png`);
    const w = body.width, h = body.height;
    const { trouserTop, shirtHem } = waistLines(key, facing, w);
    let trouserRing, shirtRing;
    if (RING_MODE) {
        const pants = new Uint8Array(w * h), shirt = new Uint8Array(w * h);
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
            if (body.data[(y * w + x) * 4 + 3] === 0) continue;
            const top = trouserTop[x], hem = shirtHem ? shirtHem[x] : -1;
            if (top >= 0 && y >= top) pants[y * w + x] = 1;
            if (hem < 0 || y <= hem) shirt[y * w + x] = 1;
        }
        trouserRing = ringOf(pants, w, h, RING_BOTTOM);
        shirtRing = ringOf(shirt, w, h, RING_TOP);
    }
    let uwImages;
    if (UW_MODE) {
        const load = kind => { const f = `${WDI}/UWUnderwear/${kind}/${kind}_${key}_${facing}.png`; return fs.existsSync(f) ? decode(f) : null; };
        uwImages = { boxers: load('boxers'), panties: load('panties'), loincloth: load('loincloth') };
    }
    for (let y = 0; y < CROP; y++) for (let x = 0; x < CROP; x++) {
        if (UW_MODE) {
            const sx = X0 + x, sy = Y0 + y, i = (sy * w + sx) * 4, a = body.data[i + 3] / 255;
            let rgb = [0, 1, 2].map(k => (body.data[i + k] * a + 255 * (1 - a)) * 0.35 + 255 * 0.65);
            const solid = img => img && img.data[(Math.min(img.height - 1, Math.floor(sy * img.height / h)) * img.width + Math.min(img.width - 1, Math.floor(sx * img.width / w))) * 4 + 3] !== 0;
            if (SLIP) {
                if (solid(uwImages.panties)) rgb = rgb.map((v, k) => v * 0.5 + [60, 170, 90][k] * 0.5);
                if (solid(uwImages.loincloth)) rgb = rgb.map((v, k) => v * 0.5 + [150, 90, 200][k] * 0.5);
            }
            else if (solid(uwImages.boxers)) rgb = rgb.map((v, k) => v * 0.5 + [235, 160, 40][k] * 0.5);
            if (a > 0 && SLIP) {
                const tl = trouserTop[sx];
                if (tl >= 0) {
                    const lo = Math.min(tl, trouserTop[sx - 1] >= 0 ? trouserTop[sx - 1] : tl, trouserTop[sx + 1] >= 0 ? trouserTop[sx + 1] : tl);
                    const hi = Math.max(tl, trouserTop[sx - 1] >= 0 ? trouserTop[sx - 1] : tl, trouserTop[sx + 1] >= 0 ? trouserTop[sx + 1] : tl);
                    if (sy >= lo - 1 && sy <= hi + 1) rgb = [40, 90, 215];
                }
            } else if (a > 0) {
                // every row the line crosses between the neighbouring columns, so a steep stretch stays a continuous line
                const hem = shirtHem ? shirtHem[sx] : -1;
                if (hem >= 0) {
                    const lo = Math.min(hem, shirtHem[Math.max(0, sx - 1)] >= 0 ? shirtHem[sx - 1] : hem, shirtHem[sx + 1] >= 0 ? shirtHem[sx + 1] : hem);
                    const hi = Math.max(hem, shirtHem[Math.max(0, sx - 1)] >= 0 ? shirtHem[sx - 1] : hem, shirtHem[sx + 1] >= 0 ? shirtHem[sx + 1] : hem);
                    if (sy >= lo - 1 && sy <= hi + 1) rgb = [215, 40, 40];
                }
            }
            const o = ((r * CROP + y) * W + c * CROP + x) * 4;
            out[o] = Math.round(rgb[0]); out[o + 1] = Math.round(rgb[1]); out[o + 2] = Math.round(rgb[2]); out[o + 3] = 255;
            if (x === 0 || y === 0) out[o] = out[o + 1] = out[o + 2] = 170;
            continue;
        }
        if (RING_MODE) {
            const sx = X0 + x, sy = Y0 + y, i = (sy * w + sx) * 4, a = body.data[i + 3] / 255;
            let rgb = [0, 1, 2].map(k => (body.data[i + k] * a + 255 * (1 - a)) * 0.25 + 255 * 0.75);
            if (trouserRing[sy * w + sx]) rgb = [40, 90, 215];
            if (shirtRing[sy * w + sx]) rgb = [215, 40, 40];
            const o = ((r * CROP + y) * W + c * CROP + x) * 4;
            out[o] = Math.round(rgb[0]); out[o + 1] = Math.round(rgb[1]); out[o + 2] = Math.round(rgb[2]); out[o + 3] = 255;
            if (x === 0 || y === 0) out[o] = out[o + 1] = out[o + 2] = 170;
            continue;
        }
        const sx = X0 + x, sy = Y0 + y, i = (sy * w + sx) * 4, a = body.data[i + 3] / 255;
        let rgb = [0, 1, 2].map(k => body.data[i + k] * a + 255 * (1 - a));
        if (a > 0) {
            const top = trouserTop[sx], hem = shirtHem ? shirtHem[sx] : -1;
            if (top >= 0 && sy >= top) rgb = rgb.map((v, k) => v * 0.55 + [40, 90, 215][k] * 0.45);
            if (hem < 0 || sy <= hem) rgb = rgb.map((v, k) => v * 0.55 + [215, 40, 40][k] * 0.45);
        }
        const o = ((r * CROP + y) * W + c * CROP + x) * 4;
        out[o] = Math.round(rgb[0]); out[o + 1] = Math.round(rgb[1]); out[o + 2] = Math.round(rgb[2]); out[o + 3] = 255;
        if (x === 0 || y === 0) out[o] = out[o + 1] = out[o + 2] = 170;
    }
}));

const file = path.join(__dirname, '..', 'Art', 'work', UW_MODE ? (SLIP ? (process.argv.includes('--fundoshi') ? 'game-cut-fundoshi-preview.png' : 'game-cut-slip-preview.png') : 'game-cut-underwear-preview.png') : RING_MODE ? `game-cut-ring-${RING_TOP}-${RING_BOTTOM}px-preview.png` : 'game-cut-preview.png');
fs.mkdirSync(path.dirname(file), { recursive: true });
if (SCALE > 1) {
    const big = Buffer.alloc(W * SCALE * H * SCALE * 4);
    for (let y = 0; y < H * SCALE; y++) for (let x = 0; x < W * SCALE; x++) out.copy(big, (y * W * SCALE + x) * 4, (Math.floor(y / SCALE) * W + Math.floor(x / SCALE)) * 4, (Math.floor(y / SCALE) * W + Math.floor(x / SCALE)) * 4 + 4);
    encode(file, { width: W * SCALE, height: H * SCALE, data: big });
} else encode(file, { width: W, height: H, data: out });
console.log('wrote', file);
