# 2026-10-12 vanilla wardrobe (ticket 20261012-103115-134-3e81, 374b720, wsl-deps.app-wdi.map)

5/5 scenarios passed, 39 captures, and the captures do not show what the run was for.

- Undyed `Apparel_BasicShirt` and `Apparel_Pants` (the four defs that carry Venus' APP masks) are not drawn
  at all, on every profile and every facing: "T-shirt", "pants" and "T-shirt and pants" show bare bodies.
  Collar shirt, jacket, duster, parka and tribalwear draw normally. 10-facings, which shows them, dyes them
  (`wears "..." dyed rgb (...)`); this feature does not. Suspected cause: the masked pattern with no dye colour.
- The child close-ups are not close: the camera stays at map scale and the child is a few pixels high
  (`the camera is centered on ... at root size 11` passes without zooming).
