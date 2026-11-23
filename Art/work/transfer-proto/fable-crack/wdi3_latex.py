"""Generic closed-mesh relaxation against arbitrary fixed triangle meshes.

There is deliberately no anatomy vocabulary here.  The solver receives a
closed deformable grid and any number of fixed triangulated objects.  Every
vertex contracts toward one global centre. Fixed objects provide only local
geometric tethers, so they can stretch that mesh; without any object, it
becomes a tiny sphere at the centre. Its edges retain mesh connectivity. No
thickness, pressure, volume, landmark, or source-body constraint is introduced.
"""
import argparse
import json
import math
from pathlib import Path


GRID_ROWS = 56
GRID_SIDES = 40
ITERATIONS = 36
CENTER_PULL = 0.075
EDGE_REST_SCALE = 0.28
OBJECT_TETHER = 0.16
MAX_TETHER_SAMPLES = 512
COLLISION_INTERVAL = 6
EPSILON = 1e-5  # numeric contact tolerance only, not a physical thickness


def _vertices(mesh):
    return list(zip(*[iter(mesh["v"])] * 3))


def _triangles(mesh):
    vertices = _vertices(mesh)
    indices = mesh.get("i", [])
    return [(vertices[a], vertices[b], vertices[c]) for a, b, c in zip(indices[0::3], indices[1::3], indices[2::3])]


def _reflect(mesh):
    """Return an object reflected around X=0, retaining its triangle surface."""
    reflected = dict(mesh)
    reflected["v"] = [coordinate for x, y, z in _vertices(mesh) for coordinate in (-x, y, z)]
    # Reflection reverses winding.  Ray containment itself is winding-free,
    # but retaining outward winding makes this a normal arbitrary surface.
    reflected["i"] = [index for a, b, c in zip(mesh["i"][0::3], mesh["i"][1::3], mesh["i"][2::3]) for index in (a, c, b)]
    return reflected


def _closest_on_triangle(point, a, b, c):
    """Closest point from Christer Ericson's region tests (stdlib only)."""
    px, py, pz = point
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    ap = (px - a[0], py - a[1], pz - a[2])
    dot = lambda u, v: u[0] * v[0] + u[1] * v[1] + u[2] * v[2]
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0: return a
    bp = (px - b[0], py - b[1], pz - b[2]); d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0 and d4 <= d3: return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1 - d3); return (a[0] + v * ab[0], a[1] + v * ab[1], a[2] + v * ab[2])
    cp = (px - c[0], py - c[1], pz - c[2]); d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0 and d5 <= d6: return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2 - d6); return (a[0] + w * ac[0], a[1] + w * ac[1], a[2] + w * ac[2])
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6)); return (b[0] + w * (c[0] - b[0]), b[1] + w * (c[1] - b[1]), b[2] + w * (c[2] - b[2]))
    denom = 1.0 / (va + vb + vc); v, w = vb * denom, vc * denom
    return (a[0] + ab[0] * v + ac[0] * w, a[1] + ab[1] * v + ac[1] * w, a[2] + ab[2] * v + ac[2] * w)


class FixedSurface:
    """Triangle object with a light ray index for collision queries."""
    def __init__(self, mesh, cell=8.0):
        self.triangles = _triangles(mesh)
        source_vertices = _vertices(mesh)
        self.center = tuple(sum(vertex[axis] for vertex in source_vertices) / len(source_vertices) for axis in range(3))
        self.cell = cell
        self.ray_bins, self.space_bins = {}, {}
        for index, triangle in enumerate(self.triangles):
            xs, ys, zs = zip(*triangle)
            for iy in range(math.floor(min(ys) / cell), math.floor(max(ys) / cell) + 1):
                for iz in range(math.floor(min(zs) / cell), math.floor(max(zs) / cell) + 1):
                    self.ray_bins.setdefault((iy, iz), []).append(index)
            for ix in range(math.floor(min(xs) / cell), math.floor(max(xs) / cell) + 1):
                for iy in range(math.floor(min(ys) / cell), math.floor(max(ys) / cell) + 1):
                    for iz in range(math.floor(min(zs) / cell), math.floor(max(zs) / cell) + 1):
                        self.space_bins.setdefault((ix, iy, iz), []).append(index)

    def contains(self, point):
        """Odd-even +X ray test, using only triangles in the local Y/Z bin."""
        x, y, z = point; hits = 0
        for index in self.ray_bins.get((math.floor(y / self.cell), math.floor(z / self.cell)), []):
            a, b, c = self.triangles[index]
            ay, az = a[1] - y, a[2] - z; by, bz = b[1] - y, b[2] - z; cy, cz = c[1] - y, c[2] - z
            det = (by * cz - bz * cy) - (ay * cz - az * cy) + (ay * bz - az * by)
            if abs(det) < 1e-10: continue
            u = (by * cz - bz * cy) / det; v = (az * cy - ay * cz) / det; w = 1.0 - u - v
            if u >= 0 and v >= 0 and w >= 0 and u * a[0] + v * b[0] + w * c[0] > x: hits += 1
        return hits % 2 == 1

    def closest_normal(self, point):
        cell = self.cell; ix, iy, iz = (math.floor(value / cell) for value in point)
        choices = set()
        for radius in range(7):
            for x in range(ix - radius, ix + radius + 1):
                for y in range(iy - radius, iy + radius + 1):
                    for z in range(iz - radius, iz + radius + 1): choices.update(self.space_bins.get((x, y, z), ()))
            if choices: break
        if not choices: choices = range(len(self.triangles))
        best, best_triangle, distance = None, None, float("inf")
        for index in choices:
            q = _closest_on_triangle(point, *self.triangles[index]); dx, dy, dz = point[0] - q[0], point[1] - q[1], point[2] - q[2]; d = dx * dx + dy * dy + dz * dz
            if d < distance: best, best_triangle, distance = q, self.triangles[index], d
        a, b, c = best_triangle
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        normal = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        if sum(normal[axis] * (best[axis] - self.center[axis]) for axis in range(3)) < 0: normal = tuple(-value for value in normal)
        length = math.sqrt(sum(value * value for value in normal)) or 1.0
        return best, tuple(value / length for value in normal)

    def closest(self, point):
        return self.closest_normal(point)[0]


def _project_out_of_union(vertex, surfaces):
    """Project through the exterior of the union, including overlap regions."""
    for _ in range(12):
        active = [surface for surface in surfaces if surface.contains(vertex)]
        if not active: return
        candidates = []
        for surface in active:
            point, normal = surface.closest_normal(vertex)
            # A closest point can be on the *internal* boundary of two
            # overlapping objects.  Walk only along the candidate outward
            # normal until it reaches the exterior of their union.  This is
            # a numerical escape search, not an added physical clearance.
            for distance in (EPSILON, .01, .1, 1., 4., 16., 64., 256.):
                candidate = [point[axis] + normal[axis] * distance for axis in range(3)]
                intersections = sum(other.contains(candidate) for other in surfaces)
                candidates.append((intersections, candidate))
                if intersections == 0: break
        # Prefer a boundary point that lies outside the greatest number of
        # overlapping fixed objects; this is the boundary of their union, not
        # merely the boundary of whichever object was queried first.
        vertex[:] = min(candidates, key=lambda item: item[0])[1]


def _neutral_grid(objects, rows=GRID_ROWS, sides=GRID_SIDES):
    points = [vertex for mesh in objects for vertex in _vertices(mesh)]
    min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
    min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
    min_z, max_z = min(p[2] for p in points), max(p[2] for p in points)
    cx, cz = (min_x + max_x) / 2, (min_z + max_z) / 2
    margin = max(12.0, .09 * max(max_x - min_x, max_y - min_y, max_z - min_z))
    rx, rz = (max_x - min_x) / 2 + margin, (max_z - min_z) / 2 + margin
    height = max_y - min_y + 2 * margin
    vertices = []
    for row in range(rows):
        t = row / (rows - 1); y = max_y + margin - t * height
        # Smoothly close the two ends while leaving a full, generic cage in the middle.
        cap = min(1.0, min(t, 1 - t) * 8.0)
        for side in range(sides):
            a = math.tau * side / sides
            vertices.append([cx + math.cos(a) * rx * cap, y, cz + math.sin(a) * rz * cap])
    return vertices


def _centre(objects):
    points = [vertex for mesh in objects for vertex in _vertices(mesh)]
    return tuple((min(p[axis] for p in points) + max(p[axis] for p in points)) / 2 for axis in range(3))


def _row_bounds(rows):
    vertices = [row[index:index + 3] for row in rows for index in range(0, len(row), 3)]
    return {
        "min": [min(vertex[axis] for vertex in vertices) for axis in range(3)],
        "max": [max(vertex[axis] for vertex in vertices) for axis in range(3)],
    }


def _edges(rows, sides, vertices):
    edges = set()
    for row in range(rows):
        for side in range(sides):
            here = row * sides + side
            edges.add(tuple(sorted((here, row * sides + (side + 1) % sides))))
            if row + 1 < rows: edges.add((here, (row + 1) * sides + side))
    result = []
    for a, b in edges:
        dx = vertices[b][0] - vertices[a][0]; dy = vertices[b][1] - vertices[a][1]; dz = vertices[b][2] - vertices[a][2]
        result.append((a, b, math.sqrt(dx * dx + dy * dy + dz * dz) * EDGE_REST_SCALE))
    return result


def _object_targets(vertices, objects, centre, rows=GRID_ROWS, sides=GRID_SIDES):
    """Build the radial support envelope of arbitrary fixed triangle meshes.

    Every sampled fixed-surface point contributes its distance from the shared
    centre to the nearest cage direction.  Consequently an elongated object
    such as a column is constrained along its whole length, not only at a few
    closest contact points.
    """
    samples = []
    for mesh in objects:
        points = _vertices(mesh)
        stride = max(1, math.ceil(len(points) / MAX_TETHER_SAMPLES))
        samples.extend(points[::stride])
    directions, supports = [], [0.0] * len(vertices)
    for vertex in vertices:
        delta = [vertex[axis] - centre[axis] for axis in range(3)]
        length = math.sqrt(sum(value * value for value in delta))
        directions.append(tuple(value / length for value in delta) if length > 1e-8 else None)
    for point in samples:
        delta = [point[axis] - centre[axis] for axis in range(3)]
        radius = math.sqrt(sum(value * value for value in delta))
        if radius < 1e-8: continue
        direction = tuple(value / radius for value in delta)
        index = max((i for i, candidate in enumerate(directions) if candidate is not None), key=lambda i: sum(direction[a] * directions[i][a] for a in range(3)))
        supports[index] = max(supports[index], radius)
    # Fill unused cage directions from adjacent radial support, without adding
    # any physical offset to the fixed surfaces.
    for _ in range(6):
        next_supports = supports[:]
        for row in range(rows):
            for side in range(sides):
                index = row * sides + side
                if supports[index] > 0: continue
                neighbours = [row * sides + (side - 1) % sides, row * sides + (side + 1) % sides]
                if row: neighbours.append((row - 1) * sides + side)
                if row + 1 < rows: neighbours.append((row + 1) * sides + side)
                next_supports[index] = max((supports[i] for i in neighbours), default=0.0)
        supports = next_supports
    return [
        [centre[axis] + direction[axis] * supports[index] for axis in range(3)] if direction is not None and supports[index] else list(centre)
        for index, direction in enumerate(directions)
    ]


def _contract_to_centre(vertices, edges, surfaces, targets, centre, iterations=ITERATIONS):
    for _ in range(iterations):
        for vertex, target in zip(vertices, targets):
            for axis in range(3): vertex[axis] += (centre[axis] - vertex[axis]) * CENTER_PULL
            for axis in range(3): vertex[axis] += (target[axis] - vertex[axis]) * OBJECT_TETHER
        # Mesh continuity only: it resists both collapse and arbitrarily long
        # cone edges between two tethers. This adds neither volume nor thickness.
        for a, b, rest in edges:
            dx = vertices[b][0] - vertices[a][0]; dy = vertices[b][1] - vertices[a][1]; dz = vertices[b][2] - vertices[a][2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            if abs(length - rest) < 1e-9 or length < 1e-9: continue
            correction = (length - rest) / (2 * length)
            vertices[a][0] += dx * correction; vertices[a][1] += dy * correction; vertices[a][2] += dz * correction
            vertices[b][0] -= dx * correction; vertices[b][1] -= dy * correction; vertices[b][2] -= dz * correction
        if _ % COLLISION_INTERVAL == COLLISION_INTERVAL - 1:
            for vertex in vertices: _project_out_of_union(vertex, surfaces)
    for vertex in vertices: _project_out_of_union(vertex, surfaces)
    return vertices


def rebuild_deformable_mesh(blob, **_ignored):
    """Build WDI3 as a generic closed mesh around its fixed triangle inputs."""
    result = json.loads(json.dumps(blob))
    for body in result["bodies"].values():
        reference_bounds = _row_bounds(body["rows"])
        objects = [body["spine_bone"], body["clavicle_bone"], _reflect(body["clavicle_bone"])]
        vertices = _neutral_grid(objects)
        centre = _centre(objects)
        surfaces = [FixedSurface(mesh) for mesh in objects]
        vertices = _contract_to_centre(vertices, _edges(GRID_ROWS, GRID_SIDES, vertices), surfaces, _object_targets(vertices, objects, centre), centre)
        # The source adapter names its fixed inputs after their legacy
        # provenance.  They are deliberately absent from WDI3: its deliverable
        # is only the closed mesh plus generic solver metadata.
        body.pop("spine_bone", None)
        body.pop("clavicle_bone", None)
        body.pop("anatomy", None)
        body["fixed_objects"] = objects
        body["reference_bounds"] = reference_bounds
        body["rows"] = [[coordinate for side in range(GRID_SIDES) for coordinate in vertices[row * GRID_SIDES + side]] for row in range(GRID_ROWS)]
        body["sn"] = 4
        body["deformable_mesh"] = {"objects": 3, "centre": centre, "centre_pull": CENTER_PULL, "object_tether": OBJECT_TETHER, "edge_rest_scale": EDGE_REST_SCALE, "iterations": ITERATIONS, "collision": "triangle containment, zero offset", "volume": False, "pressure": False}
    result["A"] = GRID_SIDES
    return result


# Kept only so older local scripts can import the previous entry point.
rebuild_latex = rebuild_deformable_mesh


def main():
    parser = argparse.ArgumentParser(description="Relax a generic closed mesh against fixed triangle objects.")
    parser.add_argument("input", type=Path); parser.add_argument("output", type=Path)
    args = parser.parse_args(); payload = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(rebuild_deformable_mesh(payload), separators=(",", ":")), encoding="utf-8")
    print(f"ok {args.output}")


if __name__ == "__main__": main()
