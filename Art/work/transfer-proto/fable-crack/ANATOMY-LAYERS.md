# Layered anatomy study for the WDI body 3D (2026-11-09)

Virginie's requirement: respect the skeleton, the muscles and the fat masses biologically, and when the model is captured from front, side or back, get an image very close to WDI. The 2026-11-09 base (`base3d.py`) only reshapes a per-row section taken from the silhouette. It has no layers, so it cannot get there. This note records what the seven reference images and the anatomy4sculptors page say, and the architecture they imply. Nothing here is implemented yet.

Sources: skeleton front/back and side illustrations, two muscle charts (front/back, side), a 3-view female muscle render, a 9-panel drawing of male torsos with belly and folds, a back view with the gluteal muscles coloured (the green diamond and pink fold line are marked), and [anatomy4sculptors, gluteal muscles and fat](https://anatomy4sculptors.com/fr/blog/anatomie-des-fesses-muscles-et-graisse/). The page text is partly garbled; only what it states clearly is used, and it gives no numbers.

## 1. Skeleton: where bone carries the skin

Skin sits on bone, with almost no soft tissue, at these places. They set creases, dimples and hard edges, and they are fixed per body, whatever the fat.

| Landmark | Views | What it does to the surface |
|---|---|---|
| Clavicle, jugular notch, sternum | front | Flat plate on the midline; notch is a real hollow. Sternum is a floor, the cleavage cannot go deeper. |
| Costal arch (lower rib margin) | front, side | Edge that ends the chest; the shelf under the pecs or breasts. |
| Acromion, scapular spine, medial scapular border | back | Shoulder tip; the two shoulder-blade ridges beside the spine. |
| Spinous processes | back | Midline groove, deepest where muscle is thin (low back). |
| Iliac crest, ASIS | all | Hip edge; the waist ends on it; flank fat rides above it. |
| Sacral triangle (bony) | back | The diamond at the top of the cleft; hollow in both sexes. |
| Greater trochanter | back, side | Hollow below the hip on a lean body, covered by fat on a fat one. |

Profile posture, from the side skeleton: thoracic spine curves back (kyphosis), lumbar spine curves in (lordosis), the pelvis tilts with the ASIS forward and down and the sacrum back and up. The rib cage is a barrel, widest around ribs 7 to 9, and it leans forward at the top. The present cage is a straight, symmetric barrel; it needs these curves, because they are what makes the side profile.

## 2. Muscles: where they attach

Muscles are finite volumes between two bone attachments, not bands. From the charts and the page:

- Pectoralis major: clavicle, sternum and upper costal cartilages to the humerus; fan converging on the armpit.
- Latissimus dorsi: lumbar fascia and iliac crest to the humerus; long diagonal sheet on the back, fills the waist-to-armpit line.
- Trapezius: occiput and spine to clavicle and scapular spine; the stylised mass above the shoulder in WDI.
- Rectus abdominis: pubis to costal margin, blocks separated by tendinous intersections (the Hulk and Male abdominal pairs).
- External oblique and serratus: costal margin to iliac crest; the side wall of the abdomen.
- Gluteus medius: anterior three quarters of the iliac crest to the greater trochanter. Gluteus maximus: the biggest, inserts mostly on the iliotibial band. TFL: ASIS to the iliotibial band. Medius, maximus and TFL form a wheel around the greater trochanter.

## 3. Fat: pads and folds

Fat is the missing layer. It is not an offset of the bone and not a bump on the muscle: it is distributed in named pads, and the folds are where two pads or a pad and a bone-tied band meet.

From the page (gluteal region):
- Men: median gluteal pad (lower-middle buttock), flank pad (at the waist, around the iliac crest), inferior gluteal extension across the gluteal fold. Muscle shapes show through.
- Women: six pads: flank, lateral gluteal (upper buttock, up to the sacral triangle), posterior gluteal (the largest, over maximus and part of medius), inferior gluteal extension, outer thigh, inner thigh. Fat covers the muscles and the trochanter, so they are generally not visible. The Michaelis rhombus is the sacral triangle plus subcutaneous fat.
- The gluteal fold is a depression where the gluteal band crosses the maximus and the median pad; it is what makes the buttock round.

From the belly drawings: the belly is an apron that hangs from the lower abdomen, projects past the chest in profile, creases at the navel and under the apron, and rolls over the waistband. Flank fat shows as a roll above the iliac crest, folding when the body bends. The thin panels show the opposite: ribs, intersections, iliac crest and ASIS visible.

Not found: numbers for fat thickness per pad, the banana fold, the infragluteal fold as a separate structure, and the gluteus minimus. These stay estimates, to be set by eye against WDI.

## 4. Architecture this implies

Skin is the outside of a stack, computed from layers. The WDI silhouettes become the fit target, not the input.

1. Bone layer (rigid, per body class): rib barrel with kyphosis and forward lean, spine curve, pelvis with tilt, ASIS, iliac crest, sacral triangle, trochanter. The existing cage and pelvis are the starting point.
2. Muscle layer: each muscle is a finite volume between its attachment points on that bone layer, with a thickness profile. Thin bodies show it; fat bodies bury it.
3. Fat layer: a thickness field over the torso, the sum of named pads (flank, abdominal apron, gluteal pads, breast, inferior extensions) per body class and sex. A fold is a deliberate crease where two pads meet, with a sag (gravity) term for apron and breast. Minimum thickness is the 5 px floor over bare bone.
4. Skin: outer surface of bone, muscle and fat, with a smooth-union so creases keep a finite radius.
5. Fit: the pad amplitudes and bone parameters are solved per body so that the three silhouettes match WDI. The shaded South/North/East render is compared with the WDI texture by its grey bands (the artist's shadow lines mark creases and pad edges). Not by luminance as height (rejected earlier).
6. Existing local signed patches stay for small features: neck, navel, nipple, groin, linea alba.

Order of work: Male and Hulk first (muscle visible, fat thin, base good enough). Then Female and Thin_Female (breast pads). Fat and Fat_Female last, because their look is all pads and folds.

Open question for Virginie: WDI is stylised (the Male chest is 0.87 deep for 0.7 in a real thorax). The layers should respect anatomy at the attachment level, then scale to the WDI proportions; confirm that WDI proportions win where they disagree with the anatomy.

## 5. Horizontal cross sections (anatomy4sculptors, "Horizontal Cross Section of the Torso")

Source: [reference image](https://anatomy4sculptors.com/ref-images/638955316146433608.png), five male sections from shoulders to groin. The other album pages are JavaScript apps and could not be read, so only this image was studied.

It shows that the section of the torso is not an ellipse or a superellipse at any level. This is why `base3d.py` still reads as a pillow:

| Level | Section |
|---|---|
| Shoulder / clavicle | Wide cloud, front edge with a central dip at the sternal notch and a lobe each side (clavicle and upper pec); back edge nearly flat with a shallow dip at the spine. |
| Chest / pecs | Widest section. Front: two pec lobes with a midline dip over the sternum. Back: nearly flat, slightly lobed (scapulae), a dip at the spine. Flanks are rounded by the latissimus. |
| Waist | Smallest and roundest. Front slightly flat, a notch at the navel line; back a gentle spine dip. |
| Hip / iliac | Wider again. Front flat with a faint midline notch (linea alba); back wider than front with two rounded lobes (gluteus medius over the crest) and a midline cleft. |
| Groin / upper thigh | Four lobes: two rear (buttocks) and two front (thighs and pubic mound), with a notch at the front midline and a deep notch at the back midline (intergluteal cleft). |

Consequences for the model:
- Each ring is a closed curve built from a left lobe and a right lobe joined by a midline notch (front and back), not one smooth convex curve. A bilateral lobe pair, each lobe a super-ellipse, with a notch depth per level, is the minimal form.
- Notch depth is the bone-and-fat signal: deep where skin sits on bone or a fold (sternal notch, spine, cleft), shallow where fat fills (a fat body fills the notches, so its sections become rounder). The same parametrisation then covers all eight bodies.
- Lobe width, depth and notch depth are interpolated between the levels above, using the east landmark rows for placement, instead of one exponent per row.
- The `U=44` points per half-ring are enough to hold two lobes and a notch; no change to the mesh format.

### Female sections (same series, second image)

| Level | Section |
|---|---|
| Shoulder / upper chest | Cloud as the male one, front dip at the notch, shoulders slightly narrower. |
| Breast level | Not a pec plate: two separate, rounded breast lobes projecting from the front, a deep V cleavage between them (deeper than the male sternal dip), then the ribcage behind. Widest at the lateral breast edges. Back flat with two shallow scapular bulges and a spine dip. |
| Waist | Small, nearly round, front slightly pointed over the linea alba, back with two soft lobes. |
| Hip / iliac | Wide, oval, with a gentle front dip and a back dip; wider than the male hip relative to the chest. |
| Groin / upper thigh | Two wide rear lobes (buttocks) and a smaller front pair with a notch at the pubic midline. The rear lobes are rounder and larger than in the male section. |

Differences from the male series that the model must carry: the breast is a separate pair of lobes added at the chest ring, bounded by the cleavage notch and its own lateral edge, not a deepened pec; the hip ring is wider than the waist by a larger ratio; the rear lobes of the pelvis ring are bigger and rounder (posterior gluteal pad, section 3).

## 6. Muscle layer seen on a sculpt (anatomy4sculptors 3D viewer screenshot, male bust, half skin and half muscles)

The screenshot is one view of the viewer (T pose, right half of the torso shows the muscle layer under the skin of the left half). What it shows for the muscle layer:
- Each muscle is a smooth, closed, lens-shaped volume with rounded ends, separate from its neighbours. They butt against each other along clear seams; none is a band across the whole torso.
- Pectoralis major is a broad, thin fan: thick at the sternal edge and lower border, tapering onto the humerus, with a crisp lower margin. Deltoid is a cap over the shoulder joint, thick in the middle. Serratus anterior shows as short separate digitations on the side ribs. Rectus abdominis is a column of paired blocks, wider at the top.
- The skin on this lean body follows the muscle volumes closely (thin fat): surface creases are the seams between volumes. This is the male case for the layered model: skin = muscle offset by a few pixels, and the fat pads of section 3 add on top only at flank, lower abdomen and gluteal region.
- Use: the muscle volumes can be built as the same lobe-pair sections of section 5, clipped to their attachment ranges, then unioned with a smooth minimum so the seams stay as creases.

Limits: one screenshot, no scale, no side or back view. It confirms the shape of the muscle layer; it gives no measurements.

## 7. Muscles of the frontal torso, layer by layer (anatomy4sculptors, `muscles-of-torso-front`)

Source: [image](https://anatomy4sculptors.com/ref-images/638604511470685015.jpg), found in the pasted page DOM (`image-holder` background). Six panels, each adds one muscle over the rib cage and spine. The order is the build order of the muscle layer.

1. Skeleton: the rib cage leans forward and is open at the front; the sternum is the central floor; the clavicle runs out to the acromion. Ribs are separate hoops with gaps.
2. Serratus anterior: finger-like digitations on the side of ribs 1 to 8 or 9, from the rib faces to the medial border of the scapula. It is the first layer over the side ribs, and its lower fingers interlock with the external oblique.
3. Pectoralis major: a large fan of two heads. Clavicular head from the medial half of the clavicle, sternocostal head from the sternum and upper costal cartilages; both converge on the humerus (the sleeve at the armpit). Its lower border is oblique and ends at the armpit; below it the serratus shows.
4. Latissimus dorsi (seen from the front at the side): a thin sheet on the lower side of the ribs, from the iliac crest and lumbar fascia up to the humerus behind the armpit. It forms the lateral wall behind the serratus.
5. Trapezius and deltoid: trapezius leaves the occiput and the neck spine and drapes to the clavicle and the scapular spine (the neck-to-shoulder slope, the stylised WDI mass); deltoid caps the shoulder from clavicle, acromion and scapular spine to the humerus.
6. External oblique and rectus abdominis: the oblique is a broad sheet from the lower ribs running down and forward to the iliac crest and the linea alba; the rectus is a column of paired blocks on each side of the midline, wider at the top, with tendinous intersections. The external oblique interlocks with the serratus at the costal margin.

Use in the model: attachment anchors for each muscle (clavicle, sternum, costal margin, iliac crest, humerus root, scapular spine) can be derived from the landmark set (jugular notch, shoulder tips, armpits, under-breast fold, navel, hips). Each muscle is a finite volume between its anchors; the order above is the stacking order (serratus under pectoral, pectoral over serratus, oblique and rectus last on the abdomen).

How to feed more references: the viewer is a login-gated app, but the page DOM that you paste contains each image's static URL (`image-holder`, `background-image: url(".../ref-images/<id>.jpg")`). That URL is a public file and can be read directly. The neighbours of this asset are `torso-cross-section-female` (previous) and `the-pectoralis-major` (next); paste their DOM the same way.
