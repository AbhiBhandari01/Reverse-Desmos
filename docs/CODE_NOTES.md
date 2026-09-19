# Code notes — how app.py works

Detailed walkthrough of each section in `src/app.py`, for reference.

## Settings & state

- `ORIGIN_X, ORIGIN_Y`: canvas center, treated as graph (0,0) — this is not
  the canvas's actual top-left pixel origin, so we compute it once here.
- `SCALE`: pixels per 1 graph unit. Increase to zoom in, decrease to zoom out.
- `control_points`: list of dicts `{"id", "px", "py"}` — `id` is the tkinter
  canvas item id (needed to move/reference that exact dot later), `px`/`py`
  is its live pixel position.
- `mode`: `"draw"` while sketching, `"edit"` once control points exist.
  Prevents drawing a new stroke while trying to drag a dot.

## pixel_to_graph(px, py)

Converts screen pixels into real graph coordinates. Flips y because pixel-y
increases downward on screen, but graph-y should increase upward.

## draw_grid()

Draws gridlines every 1 unit and bold axes through the origin, using
`ORIGIN_X % SCALE` to make sure lines always align exactly through (0,0)
regardless of canvas size. Labels are placed via `create_text`.

## Freehand drawing (start_draw / add_point / stop_draw)

`<B1-Motion>` fires on every mouse-move-while-held-down event. Each point is
appended to `raw_points` and connected to the previous one with a short line
segment — many tiny segments in a row look like one smooth stroke.

## finish_drawing()

Converts the raw stroke into a small number of draggable dots.
`num_points = points_var.get()` reads the slider's current value.
`np.linspace(0, len(raw_points)-1, num_points)` picks evenly spaced INDEX
positions along the whole stroke (not spatially even — even by position in
the sequence of points recorded), so the dots represent the stroke's shape
fairly regardless of drawing speed.
The original stroke is faded (`itemconfig("stroke", fill=...)`) rather than
deleted, so it stays visible as a reference while editing.

## Dragging (on_dot_press / on_dot_drag / on_dot_release)

`tag_bind("control", ...)` — as opposed to `canvas.bind` — only fires for
clicks that land on a canvas item tagged `"control"`, so dragging a dot
doesn't get confused with starting a new stroke.
`canvas.find_closest()` identifies which control point was actually clicked.
`canvas.coords()` moves an existing shape by giving it a new bounding box —
this is what actually redraws the dot at its new position.

## fit_curve() — the math

1. Convert every control point's pixel position to graph coordinates.
2. `np.polyfit(xs, ys, degree)` solves the least-squares problem: find
   polynomial coefficients minimizing the total squared vertical distance
   between the curve and every point. Solved directly via linear algebra
   (SVD-based), not by iterative guessing.
3. Coefficients come back highest-power-first; the loop below builds a
   readable `"y = ..."` string from them.
4. `np.poly1d(coeffs)` wraps the coefficients into a callable function.
   200 evenly spaced x-values are plugged in, converted back to pixel
   coordinates, and connected with line segments to draw the smooth red curve.

## clear_canvas()

Resets all state and wipes the canvas back to a blank slate, ready to draw again.
