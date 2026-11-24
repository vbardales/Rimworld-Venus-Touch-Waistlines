"""Rebuild the 3D viewer with the latest mesh export.

Run ``uv run python body3d_build.py`` after ``wdi3d_export.py`` (the wdi3d model:
mesh, crease maps, frame). ``body3d_build.py legacy`` puts the older
``relief_export2.py`` mesh (out/relief3d-shade5.json) back in the first mode.
The relief and simple comparison modes remain from the existing viewer.

When ``out/stack3d-mesh.json`` exists (stack3d_export.py: skeleton, muscles,
fat, skin), each of its bodies takes the place of the wdi3d body of the same
name; the wdi3d one stays in the list as ``<Body> (wdi3d)``. ``nostack`` skips it.
"""
import json
import pathlib
import sys
import copy
import math
import ast
import struct
import zipfile
from wdi3_latex import rebuild_deformable_mesh
here = pathlib.Path(__file__).parent
out = here.parent.parent / "captures" / "2026-11-08_body3d.html"


def _gauss(value, center, radius):
    """A compact, smooth landmark envelope in normalized body coordinates."""
    return math.exp(-((value - center) / radius) ** 2)


def _bodyparts3d_clavicle_profile():
    """Read the front projection of the existing BodyParts3D clavicle.

    The WDI 2 build normally has no numeric dependency.  Reading the float32
    ``.npy`` member directly keeps that property while making the bone package
    (rather than an invented spline) the source of this collarbone's shape.
    """
    source = here / "out" / "bp3d" / "torso_muscles.npz"
    fallback = [(0.0, 205.0, 272.0), (0.5, 198.0, 252.0), (1.0, 193.0, 236.0)]
    if not source.exists():
        return fallback, 73.0
    try:
        with zipfile.ZipFile(source) as archive:
            raw = archive.read("v_bone_clavicle.npy")
        if raw[:6] != b"\x93NUMPY":
            raise ValueError("not an npy array")
        header_size, header_start = (struct.unpack_from("<H", raw, 8)[0], 10) if raw[6] == 1 else (struct.unpack_from("<I", raw, 8)[0], 12)
        header = ast.literal_eval(raw[header_start:header_start + header_size].decode("latin1"))
        if header["descr"] != "<f4" or header["shape"][1] != 3:
            raise ValueError("unexpected clavicle array")
        start = header_start + header_size
        values = struct.unpack_from("<%df" % (header["shape"][0] * 3), raw, start)
        vertices = [values[index:index + 3] for index in range(0, len(values), 3)]
    except (KeyError, OSError, SyntaxError, ValueError, struct.error, zipfile.BadZipFile):
        return fallback, 73.0
    x0, x1 = min(vertex[0] for vertex in vertices), max(vertex[0] for vertex in vertices)
    span = max(x1 - x0, 1.0)
    profile = []
    for index in range(13):
        fraction = index / 12
        target = x0 + span * fraction
        sample = [vertex for vertex in vertices if abs(vertex[0] - target) <= max(2.8, span / 17)]
        if not sample:
            sample = [min(vertices, key=lambda vertex: abs(vertex[0] - target))]
        ys, zs = sorted(vertex[1] for vertex in sample), sorted(vertex[2] for vertex in sample)
        profile.append((fraction, ys[len(ys) // 2], zs[len(zs) // 2]))
    return profile, span


def _bodyparts3d_bone_mesh(name):
    """Return a named bone mesh from BodyParts3D, without inventing a tube.

    The viewer mirrors this half mesh.  Keeping the faces from the package is
    important here: this control is meant to be the actual bone, not another
    interpretation of its front silhouette.
    """
    source = here / "out" / "bp3d" / "torso_muscles.npz"
    if not source.exists():
        return None

    def load_member(archive, member):
        raw = archive.read(member)
        if raw[:6] != b"\x93NUMPY":
            raise ValueError("not an npy array")
        header_size, header_start = (struct.unpack_from("<H", raw, 8)[0], 10) if raw[6] == 1 else (struct.unpack_from("<I", raw, 8)[0], 12)
        header = ast.literal_eval(raw[header_start:header_start + header_size].decode("latin1"))
        shape = header["shape"]
        if len(shape) != 2 or shape[1] != 3:
            raise ValueError("unexpected clavicle array")
        type_code = {"<f4": "f", "<i4": "i"}.get(header["descr"])
        if not type_code:
            raise ValueError("unsupported clavicle array")
        start = header_start + header_size
        values = struct.unpack_from("<%d%s" % (shape[0] * 3, type_code), raw, start)
        return [values[index:index + 3] for index in range(0, len(values), 3)]

    try:
        with zipfile.ZipFile(source) as archive:
            return load_member(archive, f"v_bone_{name}.npy"), load_member(archive, f"f_bone_{name}.npy")
    except (KeyError, OSError, SyntaxError, ValueError, struct.error, zipfile.BadZipFile):
        return None


def _bodyparts3d_clavicle_mesh():
    """The package's one-sided clavicle; the viewer mirrors it."""
    return _bodyparts3d_bone_mesh("clavicle")


def _ring_depth(row, sides, x, front=True):
    """Same ring intersection as the viewer's skinDepth(), in build space."""
    hits = []
    for index in range(sides):
        start = index * 3
        end = ((index + 1) % sides) * 3
        x0, z0 = row[start], row[start + 2]
        x1, z1 = row[end], row[end + 2]
        if abs(x1 - x0) < 1e-6:
            if abs(x - x0) < 1e-4:
                hits.extend((z0, z1))
        elif min(x0, x1) <= x <= max(x0, x1):
            fraction = (x - x0) / (x1 - x0)
            hits.append(z0 + (z1 - z0) * fraction)
    if hits:
        return max(hits) if front else min(hits)
    nearest = min(range(sides), key=lambda index: abs(x - row[index * 3])) * 3
    return row[nearest + 2]


def _skin_depth(rows, sides, x, y, front=True):
    for index in range(len(rows) - 1):
        y0, y1 = rows[index][1], rows[index + 1][1]
        if (y - y0) * (y - y1) <= 0:
            fraction = (y - y0) / (y1 - y0 or 1.0)
            a = _ring_depth(rows[index], sides, x, front)
            b = _ring_depth(rows[index + 1], sides, x, front)
            return a + (b - a) * fraction
    row = min(rows, key=lambda candidate: abs(y - candidate[1]))
    return _ring_depth(row, sides, x, front)


def _south_editor_scale(rows, sides):
    """Return the south-reference plane transform used by the viewer.

    The WDI guide is projected from its 512px editor plane onto the front
    shell.  It is not a unit-scale plane: perspective compensation scales it
    about the torso centre.  Fitting a bone to raw ``-pixel_y`` therefore
    leaves a visible parallel offset even if its source pixels are correct.
    Keep the build-side axis in that same projected coordinate frame.
    """
    points = [(row[index], row[index + 1], row[index + 2])
              for row in rows for index in range(0, len(row), 3)]
    min_x, max_x = min(point[0] for point in points), max(point[0] for point in points)
    min_y, max_y = min(point[1] for point in points), max(point[1] for point in points)
    min_z, max_z = min(point[2] for point in points), max(point[2] for point in points)
    centre_y, centre_z = (min_y + max_y) / 2, (min_z + max_z) / 2
    fov = math.radians(35.0)
    fit_distance = max(2 * max(max_y - centre_y, centre_y - min_y), (max_x - min_x) * .8)
    fit_distance = fit_distance * 1.25 / (2 * math.tan(fov / 2))
    # The viewer's working canvas is 3:2 (the same aspect as its capture).
    fit_distance = max(fit_distance, (max_x - min_x) * 1.15 / (2 * math.tan(fov / 2) * 1.5))
    front_world_z = max_z + .5 - centre_z
    return centre_y, (fit_distance - front_world_z) / fit_distance


def _fit_bodyparts3d_clavicle(body, sides, guide_reference, south_key):
    """Fit the package clavicle *under* the WDI2 south skin.

    Its two endpoints follow the editor's front-plan clavicular segment.  At
    each vertex the actual WDI surface is sampled, then the bone is offset
    6 units inward: it cannot become a decal or protrude through the skin.
    """
    source = _bodyparts3d_clavicle_mesh()
    if source is None:
        return None
    vertices, faces = source
    front_plan = guide_reference.get("_frontPlan", {}).get(south_key, {})
    points = front_plan.get("points", {})
    frame = body.get("frame", {}).get("s")
    if not frame or not all(label in points for label in ("sternumTop", "top")):
        return None
    plan_cy = front_plan["cy"]
    medial_canvas_y = plan_cy + points["sternumTop"]["y"]
    lateral_canvas_y = plan_cy + points["top"]["y"]
    lateral_x = abs(points["top"]["x"])
    source_x0, source_x1 = min(vertex[0] for vertex in vertices), max(vertex[0] for vertex in vertices)
    source_span = max(source_x1 - source_x0, 1.0)
    rows = body["rows"]
    centre_y, editor_scale = _south_editor_scale(rows, sides)

    # The guide fixes the visible front axis.  These medians preserve the
    # package bone's actual local cross-section and depth S path.
    center_z = []
    center_y = []
    for index in range(25):
        u = index / 24
        target_x = source_x0 + source_span * u
        nearby = [vertex for vertex in vertices if abs(vertex[0] - target_x) <= max(2.5, source_span / 28)]
        if not nearby:
            nearby = [min(vertices, key=lambda vertex: abs(vertex[0] - target_x))]
        ys, zs = sorted(vertex[1] for vertex in nearby), sorted(vertex[2] for vertex in nearby)
        center_y.append(ys[len(ys) // 2])
        center_z.append(zs[len(zs) // 2])

    def centre(values, u):
        scaled = max(0.0, min(24.0, u * 24.0))
        low = int(scaled)
        high = min(24, low + 1)
        return values[low] + (values[high] - values[low]) * (scaled - low)

    source_y_span = max(max(center_y) - min(center_y), 1.0)
    target_y_scale = abs(lateral_canvas_y - medial_canvas_y) / source_y_span
    out = []
    for source_x, source_y, source_z in vertices:
        u = (source_x - source_x0) / source_span
        target_x = lateral_x * u
        # The medial axis lies exactly on the violet front-plan segment; the
        # source mesh only adds its thickness around that constraint.
        # Match the exact screen-space WDI guide rather than its unscaled
        # pixels: setReferenceBox() scales that guide about the torso centre.
        medial_axis_y = centre_y * (1.0 - editor_scale) - editor_scale * medial_canvas_y
        guide_slope = -editor_scale * (lateral_canvas_y - medial_canvas_y)
        # The guide sits on the shell whereas the bone is 6 units underneath;
        # perspective otherwise shortens its visible V by roughly a third.
        # Compensate only the medial-to-lateral slope, never the sternum end.
        target_y = medial_axis_y + 1.45 * u * guide_slope + (source_y - centre(center_y, u)) * target_y_scale * editor_scale
        skin_z = _skin_depth(rows, sides, target_x, target_y, True)
        chord_z = center_z[0] + (center_z[-1] - center_z[0]) * u
        sweep_z = (centre(center_z, u) - chord_z) * 0.16
        local_z = (source_z - centre(center_z, u)) * 0.42
        out.extend((target_x, target_y, skin_z - 6.0 + sweep_z + local_z))
    return {"v": out, "i": [index for face in faces for index in face], "source": "BodyParts3D v_bone_clavicle, 6 units under WDI2 skin"}


def _fit_bodyparts3d_spine(body, sides, guide_reference, north_key):
    """Fit the BodyParts3D spine under the north WDI2 shell.

    The top and sacral ends are constrained by the saved north/back-plan
    guides.  The centreline is therefore not a generic tube: the package's
    vertebrae preserve their genuine profile curve and local thickness.
    """
    source = _bodyparts3d_bone_mesh("spine")
    if source is None:
        return None
    vertices, faces = source
    plan = guide_reference.get("_backPlan", {}).get(north_key, {})
    upper, lower = plan.get("upper", {}), plan.get("lower", {})
    if not all(key in upper.get("points", {}) for key in ("neckTop",)) or not all(key in lower.get("points", {}) for key in ("low",)):
        return None
    # The spine is controlled by the north editor only: its violet cervical
    # pin, the centre of the north waist trait, and the centre of its pelvic
    # trait.  Other views remain validation cues, never placement inputs.
    north_marks = guide_reference.get(north_key, {})
    required = ("chin", "waistL", "waistR", "pelvisL", "pelvisR")
    if all(name in north_marks for name in required):
        top_canvas_y = north_marks["chin"]["y"] + 5.0
        waist_canvas_y = (north_marks["waistL"]["y"] + north_marks["waistR"]["y"]) / 2
        bottom_canvas_y = (north_marks["pelvisL"]["y"] + north_marks["pelvisR"]["y"]) / 2
        north_cx = body["frame"]["cxn"]
        top_axis_x = north_cx - north_marks["chin"]["x"]
        waist_axis_x = north_cx - (north_marks["waistL"]["x"] + north_marks["waistR"]["x"]) / 2
        bottom_axis_x = north_cx - (north_marks["pelvisL"]["x"] + north_marks["pelvisR"]["x"]) / 2
    else:
        top_canvas_y = upper["cy"] + upper["points"]["neckTop"]["y"]
        waist_canvas_y = (top_canvas_y + lower["cy"] + lower["points"]["low"]["y"]) / 2
        bottom_canvas_y = lower["cy"] + lower["points"]["low"]["y"]
        top_axis_x = waist_axis_x = bottom_axis_x = 0.0
    # A saved editor column guide is a sagittal constraint.  When it exists,
    # its five anchors are authoritative for both height and front/back depth:
    # no profile curve is guessed from the north/back view.  The JSON supplied
    # for the current Male pass predates these controls, so this branch stays
    # deliberately dormant until the editor exports ``_spineGuide``.
    body_name = north_key.split(":", 1)[0]
    profile_guide = guide_reference.get("_spineGuide", {}).get(f"{body_name}:east", {})
    profile_anchor_names = ("deepBlue", "blueLower", "blueUpper", "pink", "green")
    profile_inflection_names = ("inflectBlueDeep", "inflectBlueBlue", "inflectPinkBlue", "inflectGreenPink")
    has_profile_guide = all(
        isinstance(profile_guide.get(name), dict)
        and "x" in profile_guide[name]
        and "y" in profile_guide[name]
        for name in (*profile_anchor_names, *profile_inflection_names)
    )
    if has_profile_guide:
        guide_nodes = [profile_guide[name] for name in profile_anchor_names]
        guide_controls = [profile_guide[name] for name in profile_inflection_names]
        # The five nodes follow the source asset from sacrum to cervical end.
        guide_u = (0.0, .25, .52, .78, 1.0)
        def profile_value(u, coordinate):
            """Evaluate the editor's four saved quadratic spine curves.

            ``drawSpineZones`` uses one quadratic Bézier per coloured zone.
            Its square inflection handles are therefore geometry, not merely
            UI decoration: omitting them reduces the profile to four straight
            segments and loses the user's kyphosis/lordosis.
            """
            for limit in range(1, len(guide_u)):
                if u <= guide_u[limit]:
                    lo, hi = guide_u[limit - 1], guide_u[limit]
                    t = (u - lo) / (hi - lo)
                    a, control, c = guide_nodes[limit - 1], guide_controls[limit - 1], guide_nodes[limit]
                    return (1 - t) ** 2 * a[coordinate] + 2 * (1 - t) * t * control[coordinate] + t ** 2 * c[coordinate]
            return guide_nodes[-1][coordinate]
    # Translate the complete profile until the sacral endpoint meets the
    # croup-side inner WDI boundary.  This is an anchor translation, not a
    # deformation: the five zone proportions and all Bézier curvatures stay
    # exactly as the editor recorded them.
    croup_guide = guide_reference.get("_spineCroup", {}).get(f"{body_name}:east")
    spine_drop = (
        croup_guide - profile_guide["deepBlue"]["y"]
        if has_profile_guide and isinstance(croup_guide, (int, float))
        else 0.0
    )

    source_y0, source_y1 = min(vertex[1] for vertex in vertices), max(vertex[1] for vertex in vertices)
    source_y_span = max(source_y1 - source_y0, 1.0)
    source_x0, source_x1 = min(vertex[0] for vertex in vertices), max(vertex[0] for vertex in vertices)
    source_x_center = (source_x0 + source_x1) / 2
    rows = body["rows"]
    out = []
    for source_x, source_y, source_z in vertices:
        u = (source_y - source_y0) / source_y_span  # sacrum -> cervical end
        # Keep the two source end caps a hair inside the closed membrane.
        # The guide anchors define the visible extrema; an exact cap-on-cap
        # fit can otherwise leave a couple of numerical boundary vertices.
        profile_u = max(.003, min(.997, u))
        # The lumbar transition of the package is at roughly one quarter of
        # the sacrum-to-cervical path.  Snap that locus to the north waist
        # trait, then interpolate the two remaining anatomical spans.
        canvas_y = (
            profile_value(profile_u, "y") if has_profile_guide else
            bottom_canvas_y + (waist_canvas_y - bottom_canvas_y) * (u / .25)
            if u <= .25 else
            waist_canvas_y + (top_canvas_y - waist_canvas_y) * ((u - .25) / .75)
        )
        axis_x = (
            bottom_axis_x + (waist_axis_x - bottom_axis_x) * (u / .25)
            if u <= .25 else
            waist_axis_x + (top_axis_x - waist_axis_x) * ((u - .25) / .75)
        )
        target_y = -canvas_y - spine_drop
        # Preserve the source bone's cross-section proportions.  The same
        # scale is applied across and through the profile: squashing Z alone
        # makes the vertebrae look like a flat ribbon in the East view.
        # Uniform fit scale: preserves the packaged bone's X:Z proportions
        # while remaining close enough for the current closed membrane.
        # Fat has the shallowest usable anterior/posterior corridor at the
        # rebalanced sacral transition.  Keep the bone's X:Z ratio intact,
        # but use the smallest uniform fit that remains inside its envelope.
        cross_section_scale = .18 if body_name == "Fat" else .20
        target_x = axis_x + (source_x - source_x_center) * cross_section_scale
        back_z = _skin_depth(rows, sides, target_x, target_y, False)
        front_z = _skin_depth(rows, sides, target_x, target_y, True)
        source_mid_z = 226.0 + 8.0 * math.sin(u * math.pi * .8)
        centre_z = (front_z + back_z) / 2
        # The spine is a core element: unlike a clavicle it must not be a
        # near-back decal.  Place it on the local anterior/posterior median,
        # while retaining the source vertebrae's shallow sagittal curve.
        if has_profile_guide:
            # This is the very same East projection as the 3D WDI guide:
            # screen X maps directly onto world Z about the profile's zmean.
            # Normalising it against the silhouette depth flattened the saved
            # cyphosis/lordosis into an almost straight vertical line.
            guide_z = profile_value(profile_u, "x") - body["frame"]["zmean"]
            target_z = guide_z + (source_z - source_mid_z) * cross_section_scale
            target_z = max(back_z + 2.0, min(front_z - 2.0, target_z))
        else:
            target_z = max(back_z + 2.0, min(front_z - 2.0, centre_z + (source_z - source_mid_z) * .16))
        out.extend((target_x, target_y, target_z))
    source_label = "BodyParts3D v_bone_spine, fitted to Male east spine guide" if has_profile_guide else "BodyParts3D v_bone_spine, centred in the WDI2 core"
    return {"v": out, "i": [index for face in faces for index in face], "source": source_label}


def _apply_spine_reference(base_reference, column_reference):
    """Overlay the approved spine guides without replacing other constructions.

    The landmark editor export is shared by every body type.  The current
    The earlier column pass was edited for Male only, so its regular landmark
    records remain a Male-only overlay.  The current ``_spineGuide`` has a
    complete 8 × 3 set; copy every one of those independent curves while
    preserving the approved cage, chest and construction layers.
    """
    merged = copy.deepcopy(base_reference)
    for view in ("south", "east", "north"):
        name = f"Male:{view}"
        if isinstance(column_reference.get(name), dict):
            merged[name] = copy.deepcopy(column_reference[name])
    if isinstance(column_reference.get("_spineGuide"), dict):
        merged["_spineGuide"] = copy.deepcopy(column_reference["_spineGuide"])
    croup_guides = {}
    for name in column_reference.get("_spineGuide", {}):
        landmarks = column_reference.get(name, {})
        pelvis_l, pelvis_r = landmarks.get("pelvisL"), landmarks.get("pelvisR")
        if isinstance(pelvis_l, dict) and isinstance(pelvis_r, dict):
            if isinstance(pelvis_l.get("y"), (int, float)) and isinstance(pelvis_r.get("y"), (int, float)):
                croup_guides[name] = (pelvis_l["y"] + pelvis_r["y"]) / 2
    merged["_spineCroup"] = croup_guides
    return merged


def add_wdi2_neck_and_shoulder_volumes(blob, anchors, volume_reference, guide_reference):
    """Give the independent WDI 2 envelope shallow upper-body landmarks.

    The original blob remains a literal WDI hull.  WDI 2 keeps that same
    silhouette and receives only signed depth changes: neck straps and
    clavicles on the front, a broad trapezius/cervical plane behind, plus
    cropped deltoid caps at the arm cut.  Coordinates are normalized per ring
    so the treatment follows every existing WDI body type without inventing
    arms outside its source silhouette.
    """
    sides = blob["A"]
    for name, body in blob["bodies"].items():
        rows = body["rows"]
        ring_count = len(rows)
        south = anchors[name]["south"]
        north = anchors[name]["north"]
        south_key = f"{name}:south"

        def point(points, *names):
            for label in names:
                if label in points:
                    return points[label]
            raise KeyError(f"{name}: missing anchor {names}")

        def normalized_y(points, p):
            top = point(points, "top", "top / jugular notch", "jugular notch")[1]
            bottom = point(points, "bottom")[1]
            return max(0.0, min(1.0, (p[1] - top) / (bottom - top)))

        shoulder_l = point(south, "shoulder tip L", "leftmost / shoulder tip L")
        shoulder_r = point(south, "shoulder tip R", "rightmost / shoulder tip R")
        neck_l = point(south, "neck base L")
        neck_r = point(south, "neck base R")
        notch = point(south, "jugular notch", "top / jugular notch")
        armpit_l = point(south, "armpit L")
        armpit_r = point(south, "armpit R")
        chest_l = point(south, "breast apex L")
        chest_r = point(south, "breast apex R")
        shoulder_mid_y = normalized_y(south, [(shoulder_l[0] + shoulder_r[0]) / 2, (shoulder_l[1] + shoulder_r[1]) / 2])
        armpit_y = normalized_y(south, [(armpit_l[0] + armpit_r[0]) / 2, (armpit_l[1] + armpit_r[1]) / 2])
        chest_y = normalized_y(south, [(chest_l[0] + chest_r[0]) / 2, (chest_l[1] + chest_r[1]) / 2])
        notch_y = normalized_y(south, notch)
        shoulder_half = max((shoulder_r[0] - shoulder_l[0]) / 2, 1)
        shoulder_center = (shoulder_l[0] + shoulder_r[0]) / 2
        neck_half = max((neck_r[0] - neck_l[0]) / 2, 1)
        neck_center = (neck_l[0] + neck_r[0]) / 2
        neck_x = abs((neck_r[0] - neck_center) / shoulder_half)
        deltoid_x = abs((shoulder_r[0] - shoulder_center) / shoulder_half)
        back_top_y = normalized_y(north, point(north, "top"))
        back_shoulder_l = point(north, "leftmost / shoulder tip L", "shoulder tip L")
        back_shoulder_r = point(north, "rightmost / shoulder tip R", "shoulder tip R")
        back_shoulder_y = normalized_y(north, [(back_shoulder_l[0] + back_shoulder_r[0]) / 2, (back_shoulder_l[1] + back_shoulder_r[1]) / 2])

        # The double-diamond/front-plan guide supplies the *placement* of the
        # collarbone: its upper segment is the visible clavicular line.  The
        # feature's relief still comes from the actual BodyParts3D bone mesh.
        # A shoulder-tip point is a contour datum, not a clavicle endpoint;
        # pinning the bone to it had left the feature on the very top rim.
        current = volume_reference.get(south_key, {})
        current_l, current_r = current.get("shoulderL", {}), current.get("shoulderR", {})
        if all(key in current_l for key in ("x", "y")) and all(key in current_r for key in ("x", "y")):
            editor_shoulder_y = (current_l["y"] + current_r["y"]) / 2
            editor_half_width = max(abs(current_r["x"] - current_l["x"]) / 2, 1)
        else:
            editor_shoulder_y, editor_half_width = (shoulder_l[1] + shoulder_r[1]) / 2, shoulder_half
        frame_s = body.get("frame", {}).get("s")
        if frame_s:
            frame_top, frame_bottom = frame_s
        else:
            frame_top, frame_bottom = 0.0, 1.0
        frame_span = max(frame_bottom - frame_top, 1)
        front_plan = guide_reference.get("_frontPlan", {}).get(south_key, {})
        front_points = front_plan.get("points", {})
        if all(name in front_points for name in ("sternumTop", "top")):
            plan_cy = front_plan["cy"]
            clavicle_medial_y = plan_cy + front_points["sternumTop"]["y"]
            clavicle_lateral_y = plan_cy + front_points["top"]["y"]
        else:
            clavicle_lateral_y = editor_shoulder_y
            clavicle_medial_y = editor_shoulder_y + editor_half_width / 6
        clavicle_profile, source_x_span = _bodyparts3d_clavicle_profile()
        source_y_medial, source_z_medial = clavicle_profile[0][1:]
        source_y_lateral, source_z_lateral = clavicle_profile[-1][1:]
        source_depth_scale = editor_half_width / source_x_span

        def clavicle_sample(u):
            u = max(0.0, min(1.0, u))
            for index in range(1, len(clavicle_profile)):
                a, b = clavicle_profile[index - 1], clavicle_profile[index]
                if u <= b[0]:
                    f = (u - a[0]) / max(b[0] - a[0], .001)
                    return tuple(a[part] + (b[part] - a[part]) * f for part in range(1, 3))
            return clavicle_profile[-1][1], clavicle_profile[-1][2]

        def clavicle_curve(u):
            # The violet front-plan segment constrains the median projected
            # axis; the real BodyParts3D S-curve remains in depth instead.
            canvas_y = clavicle_medial_y + max(0.0, min(1.0, u)) * (clavicle_lateral_y - clavicle_medial_y)
            return max(0.0, min(1.0, (canvas_y - frame_top) / frame_span))

        def clavicle_depth_curve(u):
            """Keep the real bone's top-view S-curve without moving its ends."""
            _, source_z = clavicle_sample(u)
            source_chord = source_z_medial + (source_z_lateral - source_z_medial) * u
            return (source_z - source_chord) * source_depth_scale
        sternal_t = clavicle_curve(0.0)
        for row_index, row in enumerate(rows):
            t = row_index / max(1, ring_count - 1)  # neck/top -> lower torso
            points = list(zip(row[0::3], row[1::3], row[2::3]))
            min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
            min_z, max_z = min(p[2] for p in points), max(p[2] for p in points)
            center_x = (min_x + max_x) / 2
            center_z = (min_z + max_z) / 2
            half_x = max((max_x - min_x) / 2, 1)
            half_z = max((max_z - min_z) / 2, 1)

            for side in range(sides):
                offset = side * 3
                x, _, z = row[offset : offset + 3]
                x_unit = (x - center_x) / half_x
                z_unit = (z - center_z) / half_z
                lateral = abs(x_unit)
                front = max(z_unit, 0) ** 4
                back = max(-z_unit, 0) ** 4

                # Upper trapezius stays broad and shallow: a sloping shoulder
                # plane, never a new arm volume beyond the WDI crop.
                trap = _gauss(t, (back_top_y + back_shoulder_y) / 2, max(.055, (back_shoulder_y - back_top_y) * .9)) * _gauss(lateral, 0.47, 0.48)
                # The front of the WDI crop needs the clavicles to read on
                # their own.  A frontal trapezius pad turns them into one
                # horizontal band, so the broad plane is now a back-only cue.
                depth = 4.5 * trap * back

                # No neck straps here: WDI 2 deliberately excludes the neck
                # volume.  Leaving sternocleidomastoids in this cropped shell
                # was the high, almost-horizontal band mistaken for clavicles.
                sternal_hollow = _gauss(t, sternal_t + .012, .014) * _gauss(lateral, 0.0, 0.080)
                depth -= 4.0 * sternal_hollow * front

                # This is the BodyParts3D clavicle's projected path, mirrored
                # across the sternum and fitted to WDI 2's canonical shoulders.
                clavicle_u = min(lateral, 1.0)
                clavicle_row = clavicle_curve(clavicle_u)
                # Separate the left and right bones at the manubrium and stop
                # before the cropped arm rim.  A single broad Gaussian turns
                # paired clavicles into a fake transverse band.
                clavicle_span = max(0.0, min(1.0, (lateral - 0.045) / 0.075)) * max(0.0, min(1.0, (0.88 - lateral) / 0.14))
                clavicle = (
                    _gauss(t, clavicle_row, 0.0055)
                    * _gauss(lateral, 0.42, 0.29)
                    * clavicle_span
                )
                # The clavicle runs into the front-facing shoulder cap.  The
                # generic ``front`` gate deliberately dies at that flank, so
                # it made a real collarbone vanish precisely at its acromial
                # end.  Keep this one bone on the whole visible front plane.
                clavicle_front = max(z_unit, 0) ** 1.25
                # South target: two fine subcutaneous crests from the jugular
                # notch, not a broad transverse shoulder band.
                depth += 7.5 * clavicle * clavicle_front
                # The first fit only used the face projection, so from above
                # it was a uniform transverse bar.  This signed offset is the
                # source bone's real depth deviation from its end-to-end chord;
                # it restores the visible S-angle while preserving its placed
                # manubrial and acromial endpoints.
                clavicle_plane = _gauss(t, clavicle_row, 0.010) * _gauss(lateral, 0.42, 0.29) * clavicle_span
                depth += .16 * clavicle_depth_curve(clavicle_u) * clavicle_plane * clavicle_front
                # A narrow paired hollow immediately below the crest sharpens
                # the light break.  It shares the exact two-bone mask above:
                # unlike the old broad band, it cannot cross the sternum.
                infraclavicular = _gauss(t, clavicle_row + 0.009, 0.0035) * _gauss(lateral, 0.42, 0.29) * clavicle_span
                depth -= 2.0 * infraclavicular * clavicle_front

                # Only the proximal deltoid dome is present: the arm remains
                # absent, as if held behind the back.
                deltoid = _gauss(t, (shoulder_mid_y + armpit_y) / 2, max(.040, (armpit_y - shoulder_mid_y) * .65)) * _gauss(lateral, deltoid_x, 0.20)
                depth += 6.0 * deltoid * (0.45 * front + 0.30 * back)

                # Back-only cues: a central cervical trough set into the
                # trapezius and two very soft scapular planes below it.
                cervical_groove = _gauss(t, (back_top_y + back_shoulder_y) / 2, max(.060, (back_shoulder_y - back_top_y))) * _gauss(lateral, 0.0, 0.055)
                depth -= 4.0 * cervical_groove * back
                scapula = _gauss(t, chest_y, .105) * _gauss(lateral, 0.50, 0.20)
                depth += 3.2 * scapula * back

                # Shift along the local depth radius, preserving front/back
                # symmetry and, critically, the WDI side silhouette.
                row[offset + 2] = z + depth * z_unit

        # The base blob's 60-pass normal filter intentionally erases all
        # surface detail.  This remains smooth but lets these broad landmarks
        # react to the movable lamps.
        # The WDI hull itself has row-scale pixel variation.  Keep nearly the
        # base normal filtering so those source rows never turn into horizontal
        # lighting bands; the deliberately broad landmarks still survive it.
        # Preserve enough normal detail for the new, deliberately shallow
        # clavicle ridge and its infraclavicular hollow to read under the
        # movable lamps.  The base WDI hull remains smoothed, but not until
        # the anatomy disappears.
        body["sn"] = 6
        body["anatomy"] = "neck-shoulders-bodyparts3d-clavicles-v10"
        body["anchor_source"] = "BodyParts3D v_bone_clavicle + landmark-editor-site/dist/assets/volume-reference.json"
    return blob


cur = out.read_text(encoding="utf-8").splitlines()
data_line = next(line for line in cur if line.startswith("const DATA="))
data = json.loads(data_line[len("const DATA="):].rstrip(";"))
source = "relief3d-shade5.json" if "legacy" in sys.argv[1:] else "wdi3d-mesh.json"
shade = json.loads((here / "out" / source).read_text(encoding="utf-8"))
shade["A"] = 2 * shade.pop("U")
refs = {name: {"wdi": entry.get("wdi"), "frame": entry.get("frame")} for name, entry in shade["bodies"].items()}

# The simple and relief meshes use the same source coordinate system.  Give every one the original WDI pixels and its
# frame so the comparison overlay is available in all three model families, not only in the stack export.
for mode, collection in data.items():
    if mode == "shade" or not isinstance(collection, dict):
        continue
    bodies = collection.get("bodies")
    if not isinstance(bodies, dict):
        continue
    for name, entry in list(bodies.items()):
        ref = refs.get(name.split(" (")[0])
        if not ref or not ref["wdi"]:
            continue
        if isinstance(entry, list):
            bodies[name] = {"rows": entry, "legs": None, "lm": None, "frame": ref["frame"], "wdi": ref["wdi"]}
        elif isinstance(entry, dict):
            entry.setdefault("frame", ref["frame"])
            entry.setdefault("wdi", ref["wdi"])
stack_path = here / "out" / "stack3d-mesh.json"
if stack_path.exists() and "nostack" not in sys.argv[1:] and "legacy" not in sys.argv[1:]:
    stack = json.loads(stack_path.read_text(encoding="utf-8"))["bodies"]
    bodies = {}
    for name, entry in shade["bodies"].items():
        if name in stack:
            bodies[name] = stack[name]
            bodies[f"{name} (wdi3d)"] = entry
        else:
            bodies[name] = entry
    shade["bodies"] = bodies
data["shade"] = shade
blob_path = here / "out" / "blob3d-mesh.json"
if blob_path.exists():
    anchors_path = here.parent.parent / "landmark-editor-site" / "dist" / "assets" / "anchors.json"
    anchors = json.loads(anchors_path.read_text(encoding="utf-8"))
    # `volume-reference.json` is the canonical set rendered by the current
    # landmark editor.  `anchors.json` is an older, more detailed atlas kept
    # below only for the WDI2 relief calculation while that calculation still
    # needs its neck/breast-specific anchors.
    volume_reference_path = here.parent.parent / "landmark-editor-site" / "dist" / "assets" / "volume-reference.json"
    volume_reference = json.loads(volume_reference_path.read_text(encoding="utf-8"))
    guide_path = here.parent.parent / "landmark-editor-site" / "dist" / "assets" / "reperes-anatomiquesGrandOblique.json"
    guide_reference = json.loads(guide_path.read_text(encoding="utf-8")) if guide_path.exists() else {}
    # The current column pass was authored only for Male.  It is an explicit
    # overlay, rather than a replacement for the approved all-body reference.
    column_path = here.parent.parent / "landmark-editor-site" / "dist" / "assets" / "reperes-anatomiquesColonne.json"
    if column_path.exists():
        guide_reference = _apply_spine_reference(
            guide_reference,
            json.loads(column_path.read_text(encoding="utf-8")),
        )
    data["blob"] = json.loads(blob_path.read_text(encoding="utf-8"))
    # Separate JSON tree: later experiments on blob WDI 2 never alter blob WDI.
    data["blob2"] = add_wdi2_neck_and_shoulder_volumes(copy.deepcopy(data["blob"]), anchors, volume_reference, guide_reference)
    # A single inspectable anatomical layer.  Unlike the optional coloured
    # muscle printing, this is the original BodyParts3D clavicle placed under
    # the WDI2 skin at its front-plan endpoints.
    for name, body in data["blob2"]["bodies"].items():
        body["clavicle_bone"] = _fit_bodyparts3d_clavicle(body, data["blob2"]["A"], guide_reference, f"{name}:south")
        body["spine_bone"] = _fit_bodyparts3d_spine(body, data["blob2"]["A"], guide_reference, f"{name}:north")
    # Reuse only the existing proximal muscle library for the optional colour
    # layer.  It deliberately excludes arm stumps, viscera and lower torso.
    if stack_path.exists():
        muscle_library = json.loads(stack_path.read_text(encoding="utf-8"))["bodies"]
        wanted = ("neck root", "trapezius", "pectoralis major", "deltoid", "serratus", "infraspinatus", "teres", "rhomboid")
        for name, body in data["blob2"]["bodies"].items():
            source_parts = muscle_library.get(name, {}).get("layers", {}).get("parts", [])
            body["muscle_zones"] = [part for part in source_parts if any(key in part["n"] for key in wanted)]
    # Keep the exact landmarks rendered by the 2D editor.  Do not substitute
    # the older detailed atlas here: its coordinates are visibly different.
    for name, body in data["blob2"]["bodies"].items():
        landmarks = {}
        for view in ("south", "east", "north"):
            # The active Male column pass is the source of truth for its
            # visible 2D landmark planes; every other body keeps the canonical
            # volume reference until it has its own approved edit.
            landmark_reference = guide_reference if name == "Male" else volume_reference
            points = {
                label: [point["x"], point["y"]]
                for label, point in landmark_reference.get(f"{name}:{view}", {}).items()
                if isinstance(point, dict) and "x" in point and "y" in point
            }
            # The editor adds these three points at runtime from pubis and leg
            # points.  Persist the same calculation here: a 15-point JSON
            # record is an 18-point editor model, not a smaller landmark set.
            if all(label in points for label in ("pubis", "legL", "legR")):
                leg_centre = [(points["legL"][0] + points["legR"][0]) / 2, (points["legL"][1] + points["legR"][1]) / 2]
                vertical = leg_centre[1] - points["pubis"][1]
                span = max(18, abs(points["legR"][0] - points["legL"][0]))
                groin_y = points["pubis"][1] + vertical * 0.56
                offset = max(7, span * 0.32)
                points.setdefault("groinL", [leg_centre[0] - offset, groin_y])
                points.setdefault("groinR", [leg_centre[0] + offset, groin_y])
                points.setdefault("crotch", leg_centre)
            landmarks[view] = points
        body["landmarks"] = landmarks
        # The editable shoulder construction (box rotation and head scale) is
        # stored alongside the canonical landmarks.  Keep the original values
        # so the 3D guide uses the exact same construction as the 2D editor.
        body["construction"] = {
            view: volume_reference.get("_geometry", {}).get(f"{name}:{view}")
            for view in ("south", "east", "north")
        }
        # The remaining editable construction layers live in the editor's
        # bundled export.  They are retained verbatim when present; the viewer
        # can derive its documented seed when a body/view has none yet.
        body["guide_layers"] = {
            layer: {
                view: guide_reference.get(reference_key, {}).get(f"{name}:{view}")
                for view in ("south", "east", "north")
            }
            for layer, reference_key in {
                "frontPlan": "_frontPlan",
                "profileEllipse": "_profileEllipse",
                "backPlan": "_backPlan",
                "thoracicCage": "_thoracicCage",
                "chestPlan": "_chestPlan",
                "profileChest": "_profileChest",
            }.items()
        }
        body["landmark_source"] = "landmark-editor-site/dist/assets/volume-reference.json"
    # WDI 3 begins as a deep copy of the approved WDI 2 study.  Its WDI box,
    # guides and bones remain inspectable.  The current active membrane is
    # constrained by the spinal mesh only; clavicles remain display references
    # while their 2D fit is still being refined.
data["blob3"] = rebuild_deformable_mesh(copy.deepcopy(data["blob2"]))
tpl = (here / "body3d_template.html").read_text(encoding="utf-8")
marker = "const DATA=globalThis.__DATA__;"
if marker not in tpl:
    raise ValueError(f"viewer template marker missing: {marker}")
out.write_text(
    tpl.replace(marker, f"const DATA={json.dumps(data, separators=(',', ':'))};", 1),
    encoding="utf-8",
)
print("ok", out)
