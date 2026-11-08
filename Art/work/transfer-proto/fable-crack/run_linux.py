"""Linux launcher for the crack scripts: translates the Windows paths hard-coded in crack.py and neck.py.
Usage: uv run --with numpy --with pillow --with scipy --with scikit-image python run_linux.py crack6.py [args]
"""
import builtins, os, sys, runpy
S = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
MAP = [(r"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines", os.path.join(S)),
       (r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike", os.path.join(os.path.dirname(S), "ws"))]
def tr(p):
    if isinstance(p, str) and ("\\" in p):
        for a, b in MAP:
            if p.startswith(a): p = b + p[len(a):]
        p = p.replace("\\", "/")
    return p
_open = builtins.open
builtins.open = lambda f, *a, **k: _open(tr(f), *a, **k)
for name in ("exists", "isfile", "isdir", "getmtime"):
    fn = getattr(os.path, name); setattr(os.path, name, (lambda fn: lambda p: fn(tr(p)))(fn))
_mk = os.makedirs; os.makedirs = lambda p, *a, **k: _mk(tr(p), *a, **k)
_ls = os.listdir; os.listdir = lambda p=".": _ls(tr(p))
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
runpy.run_path(sys.argv[0], run_name="__main__")
