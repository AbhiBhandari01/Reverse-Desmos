import tkinter as tk   # tkinter is Python's built-in GUI toolkit — gives us windows, canvases, buttons, etc.
import numpy as np     # numpy gives us fast array math and the polyfit function for curve fitting

# ============================================================
# GRAPH / CANVAS SETTINGS
# ============================================================
# These constants control the size of the window and how pixel
# coordinates map to "real" graph coordinates (like x=2, y=-3).

WIDTH, HEIGHT = 600, 400
# The canvas is 600 pixels wide, 400 pixels tall.

ORIGIN_X, ORIGIN_Y = WIDTH // 2, HEIGHT // 2
# We want (0,0) on the graph to sit in the CENTER of the canvas,
# not the top-left corner (which is where pixel (0,0) normally is
# in most GUI systems). So we calculate the pixel coordinates of
# the center once, and treat that as our graph's origin.

SCALE = 40
# How many pixels represent "1 unit" on the graph.
# e.g. the point (1, 0) on the graph is drawn 40 pixels to the
# right of the origin. Increasing this zooms in, decreasing zooms out.

NUM_CONTROL_POINTS = 12
# After the user finishes drawing, we don't keep every single
# pixel they dragged through (that could be hundreds of points).
# Instead we pick 12 evenly spaced points along their stroke to
# turn into draggable "control points."

DOT_RADIUS = 5
# Radius (in pixels) of each draggable orange control point circle.

# ============================================================
# GLOBAL STATE
# ============================================================
# These variables track what's currently happening in the app.
# Using globals is fine for a small tkinter app like this — in a
# larger app you'd wrap this in a class instead.

raw_points = []
# Stores every (pixel_x, pixel_y) point captured WHILE the user is
# actively dragging their mouse to draw. Cleared each time a new
# stroke starts.

control_points = []
# After "Finish Drawing" is clicked, this holds the editable dots.
# Each entry is a dictionary: {"id": <canvas item id>, "px": x, "py": y}
# We store the canvas id so we can move/update that specific dot
# later, and px/py are its current pixel position (updated live as
# the user drags it).

drawing = False
# True only while the mouse button is held down during the initial
# freehand draw. Prevents drawing from continuing accidentally.

mode = "draw"
# The app has two modes:
#   "draw" -> user is sketching their initial curve
#   "edit" -> curve has been converted to draggable control points
# Several functions check this so that, e.g., clicking on the canvas
# doesn't start a new drawing while you're trying to drag a dot.

dragging_index = None
# When the user clicks down on a specific control point, we store
# WHICH one they grabbed (its index in control_points) here, so
# subsequent mouse-move events know which dot to update.
# None means "nothing currently being dragged."


# ============================================================
# COORDINATE CONVERSION
# ============================================================

def pixel_to_graph(px, py):
    """
    Converts a pixel position on the canvas into a "graph" (x, y)
    coordinate — the kind you'd see on real graph paper.
    """
    x = (px - ORIGIN_X) / SCALE
    # Shift so the origin is 0, then divide by SCALE to convert
    # "pixels away from center" into "graph units away from center".

    y = (ORIGIN_Y - py) / SCALE
    # Same idea for y, BUT: on a computer screen, pixel y increases
    # DOWNWARD (top of screen = 0, bottom = larger numbers).
    # On a normal graph, y increases UPWARD. So we flip it by doing
    # (ORIGIN_Y - py) instead of (py - ORIGIN_Y) — this is what makes
    # "up" on screen correspond to positive y like a real graph.

    return x, y


# ============================================================
# DRAWING THE GRID AND AXES
# ============================================================

def draw_grid():
    """
    Draws light gridlines every 1 unit, plus bold x/y axes through
    the origin, plus number labels. Called once at startup.
    """
    canvas.delete("grid")
    # Remove any existing grid lines first (useful if we ever redraw).
    # "grid" is a tkinter TAG — a label we attach to canvas items so
    # we can select/delete/reorder groups of them later without
    # tracking individual IDs ourselves.

    # --- Vertical gridlines ---
    x = ORIGIN_X % SCALE
    # Start at the leftmost vertical line position. Using modulo here
    # ensures the gridlines line up with the origin regardless of
    # canvas size (so a line always passes exactly through x=0).
    while x < WIDTH:
        canvas.create_line(x, 0, x, HEIGHT, fill="#e0e0e0", tags="grid")
        # Draw a light gray vertical line from top to bottom of canvas.
        x += SCALE
        # Move to the next gridline, one graph-unit's worth of pixels over.

    # --- Horizontal gridlines (same idea, other axis) ---
    y = ORIGIN_Y % SCALE
    while y < HEIGHT:
        canvas.create_line(0, y, WIDTH, y, fill="#e0e0e0", tags="grid")
        y += SCALE

    # --- The main x and y axes, drawn bolder/darker than the grid ---
    canvas.create_line(0, ORIGIN_Y, WIDTH, ORIGIN_Y, fill="black", width=2, tags="grid")
    # Horizontal line through the origin = the x-axis.
    canvas.create_line(ORIGIN_X, 0, ORIGIN_X, HEIGHT, fill="black", width=2, tags="grid")
    # Vertical line through the origin = the y-axis.

    # --- Number labels along the x-axis ---
    for i in range(-ORIGIN_X // SCALE, (WIDTH - ORIGIN_X) // SCALE + 1):
        # i ranges over every whole graph-unit that fits on screen,
        # from the leftmost visible number to the rightmost.
        if i == 0:
            continue  # skip labeling the origin itself, it'd overlap the axes
        px = ORIGIN_X + i * SCALE
        # Convert the graph unit i back into a pixel x-position.
        canvas.create_text(px, ORIGIN_Y + 10, text=str(i), font=("Arial", 8), tags="grid")
        # Draw the number just below the x-axis line.

    # --- Number labels along the y-axis (mirrored logic) ---
    for i in range(-ORIGIN_Y // SCALE, (HEIGHT - ORIGIN_Y) // SCALE + 1):
        if i == 0:
            continue
        py = ORIGIN_Y - i * SCALE
        # Subtracting here (not adding) because positive graph y
        # should appear ABOVE the origin, which is a SMALLER pixel y.
        canvas.create_text(ORIGIN_X - 12, py, text=str(i), font=("Arial", 8), tags="grid")

    canvas.tag_lower("grid")
    # Push everything tagged "grid" behind other canvas items (like
    # the user's drawing or control points), so the grid never
    # visually covers the actual content.


# ============================================================
# FREEHAND DRAWING (MODE = "draw")
# ============================================================

def start_draw(event):
    """
    Runs the moment the user PRESSES the mouse button down on the canvas.
    `event` is a tkinter object containing info about the click,
    including event.x and event.y (pixel coordinates of the click).
    """
    global drawing
    if mode != "draw":
        return  # ignore clicks entirely if we're in "edit" mode
    drawing = True
    raw_points.clear()
    # Start fresh — forget any previous stroke's points.
    canvas.delete("stroke")
    # Remove any previously drawn line from the canvas.
    add_point(event)
    # Immediately record this first click as the first point,
    # otherwise a very quick click-and-release with no drag would
    # produce zero points.

def add_point(event):
    """
    Runs continuously WHILE the mouse is being dragged with the
    button held down (a "motion" event). Adds the current mouse
    position to raw_points and draws a line segment connecting it
    to the previous point, creating the appearance of a continuous
    freehand stroke.
    """
    if not drawing or mode != "draw":
        return
    x, y = event.x, event.y
    raw_points.append((x, y))
    if len(raw_points) > 1:
        # Only draw a connecting line if we have at least 2 points
        # (can't draw a line from a single point).
        x0, y0 = raw_points[-2]
        # raw_points[-2] is the previous point (second-to-last),
        # raw_points[-1] would be the one we just added.
        canvas.create_line(x0, y0, x, y, fill="blue", width=2, tags="stroke")
        # Draw a short segment from the previous point to this one.
        # Doing this for every tiny mouse movement is what makes the
        # whole stroke look like one smooth continuous line.

def stop_draw(event):
    """
    Runs when the mouse button is released, ending the current stroke.
    """
    global drawing
    drawing = False


# ============================================================
# TRANSITION FROM DRAWING TO EDITABLE CONTROL POINTS
# ============================================================

def finish_drawing():
    """
    Called when the "Finish Drawing" button is clicked.
    Converts the raw freehand stroke into a small number of
    draggable control points, while keeping the original stroke
    visible (faded) as a visual reference.
    """
    global mode, control_points
    if len(raw_points) < 2:
        result_label.config(text="Draw a line first")
        return  # nothing meaningful was drawn yet, so don't proceed

    mode = "edit"
    # Switch modes so future clicks on the canvas are interpreted as
    # "trying to drag a dot" instead of "starting a new drawing."

    canvas.itemconfig("stroke", fill="#c9c9f5")
    # Instead of deleting the original stroke, we just recolor it to
    # a pale lavender — this keeps it visible as a faint guide for
    # how far the user has adjusted their points, without it
    # competing visually with the bold orange dots and red fit curve.

    indices = np.linspace(0, len(raw_points) - 1, NUM_CONTROL_POINTS).astype(int)
    # np.linspace picks NUM_CONTROL_POINTS evenly spaced INDEX
    # positions across the whole stroke — e.g. if raw_points has 300
    # points and we want 12 control points, this picks indices like
    # 0, 27, 54, 82, ... 299. .astype(int) rounds them to whole
    # numbers since list indices can't be fractional.

    sampled = [raw_points[i] for i in indices]
    # Actually pull out the (x, y) pixel positions at those indices.

    control_points = []
    # Reset the list — any previous control points (from an earlier
    # draw/edit cycle) are discarded.

    for (px, py) in sampled:
        dot_id = canvas.create_oval(
            px - DOT_RADIUS, py - DOT_RADIUS, px + DOT_RADIUS, py + DOT_RADIUS,
            fill="orange", outline="black", width=1, tags="control"
        )
        # create_oval draws a circle by specifying its BOUNDING BOX
        # (top-left corner and bottom-right corner) — not a center +
        # radius directly, so we compute the box manually here.

        control_points.append({"id": dot_id, "px": px, "py": py})
        # Remember this dot's canvas ID (so we can move it later) and
        # its current pixel position.

    canvas.tag_raise("control")
    # Make sure all control point dots are drawn ON TOP of everything
    # else (the faded stroke, the grid), so they're always visible
    # and clickable.

    result_label.config(text=f"{len(control_points)} points ready — drag to adjust, then Fit")


# ============================================================
# DRAGGING CONTROL POINTS (MODE = "edit")
# ============================================================

def on_dot_press(event):
    """
    Runs when the user clicks down specifically on a control point
    (this function is bound only to canvas items tagged "control",
    not the whole canvas — see the tag_bind calls near the bottom).
    """
    global dragging_index
    if mode != "edit":
        return
    clicked = canvas.find_closest(event.x, event.y)
    # find_closest returns the canvas item nearest to the click
    # position — since this handler only fires for clicks that
    # landed on a "control" tagged item, this reliably finds the
    # dot that was actually clicked.

    for i, cp in enumerate(control_points):
        if cp["id"] == clicked[0]:
            dragging_index = i
            # Remember WHICH dot (by its index in the list) is being
            # dragged, so on_dot_drag knows what to move.
            return

def on_dot_drag(event):
    """
    Runs continuously while a control point is being dragged
    (mouse moving with button held down, over a control point).
    """
    if mode != "edit" or dragging_index is None:
        return
    cp = control_points[dragging_index]
    cp["px"], cp["py"] = event.x, event.y
    # Update our stored record of this dot's position to match
    # wherever the mouse currently is.

    canvas.coords(cp["id"], event.x - DOT_RADIUS, event.y - DOT_RADIUS,
                             event.x + DOT_RADIUS, event.y + DOT_RADIUS)
    # canvas.coords() moves an existing shape by giving it a new
    # bounding box — this actually redraws the dot at the new mouse
    # position on screen. Without this line, our internal data would
    # update but the dot would look frozen in its old spot.

def on_dot_release(event):
    """
    Runs when the mouse button is released after dragging a dot.
    """
    global dragging_index
    dragging_index = None
    # Clear the "currently dragging" state so on_dot_drag stops
    # doing anything until the next drag begins.


# ============================================================
# CURVE FITTING (THE MATH)
# ============================================================

def fit_curve():
    """
    Runs when "Fit" is clicked. Takes the CURRENT positions of all
    control points (wherever the user has dragged them), converts
    them to graph coordinates, and finds the best-fit polynomial of
    the chosen degree using least-squares regression.
    """
    if mode != "edit" or len(control_points) < 2:
        result_label.config(text="Finish drawing first, then Fit")
        return

    degree = int(degree_var.get())
    # degree_var is the tkinter variable tied to the dropdown menu;
    # .get() reads its current value as a string, so we convert it
    # to an integer (e.g. "3" -> 3).

    graph_pts = [pixel_to_graph(cp["px"], cp["py"]) for cp in control_points]
    # Convert every control point's pixel position into a real graph
    # (x, y) coordinate — this is what actually gets fitted, not raw
    # pixel numbers, so the resulting equation makes mathematical sense.

    xs = np.array([p[0] for p in graph_pts])
    ys = np.array([p[1] for p in graph_pts])
    # Split the list of (x, y) tuples into two separate numpy arrays,
    # since that's the format np.polyfit expects.

    if degree >= len(control_points):
        # You mathematically need at least (degree + 1) points to
        # uniquely determine a polynomial of that degree — e.g. you
        # need at least 3 points to fit a degree-2 (quadratic) curve.
        result_label.config(text=f"Need more points for degree {degree}")
        return

    coeffs = np.polyfit(xs, ys, degree)
    # THE ACTUAL MATH: this single call sets up the least-squares
    # problem (minimizing total squared vertical distance between
    # the curve and every point) and solves it using linear algebra
    # under the hood. Returns the coefficients from highest power to
    # lowest, e.g. for degree 2 it returns [a, b, c] meaning
    # y = a*x^2 + b*x + c.

    # --- Build a human-readable equation string from the coefficients ---
    terms = []
    n = len(coeffs)
    for i, c in enumerate(coeffs):
        power = n - i - 1
        # coeffs[0] corresponds to the HIGHEST power, and it counts
        # down from there, so we compute which power each coefficient
        # belongs to based on its position in the list.
        c_rounded = round(c, 3)
        if power == 0:
            terms.append(f"{c_rounded}")           # constant term, no x
        elif power == 1:
            terms.append(f"{c_rounded}x")           # just "x", not "x^1"
        else:
            terms.append(f"{c_rounded}x^{power}")   # "x^2", "x^3", etc.
    equation = "y = " + " + ".join(terms)
    result_label.config(text=equation)

    # --- Draw the fitted curve on the canvas ---
    canvas.delete("curve")
    # Remove any previously drawn fit line before drawing the new one.

    poly = np.poly1d(coeffs)
    # np.poly1d wraps the coefficients into a callable object — so
    # instead of manually computing a*x^2 + b*x + c, we can just call
    # poly(some_x) and get the corresponding y-value back.

    x_graph_range = np.linspace(min(xs), max(xs), 200)
    # 200 evenly spaced x-values spanning from the leftmost to
    # rightmost control point, in GRAPH units. More points here =
    # smoother-looking curve when we connect them with line segments.

    y_graph_range = poly(x_graph_range)
    # Plug every one of those x-values into our fitted polynomial to
    # get the corresponding y-values.

    prev = None
    for gx, gy in zip(x_graph_range, y_graph_range):
        px = ORIGIN_X + gx * SCALE
        py = ORIGIN_Y - gy * SCALE
        # Convert back from graph coordinates to pixel coordinates so
        # we can actually draw this on the canvas (reverse of
        # pixel_to_graph, same flipped-y logic as before).
        if prev:
            canvas.create_line(prev[0], prev[1], px, py, fill="red", width=2, tags="curve")
            # Connect this point to the previous one with a short red
            # line segment — 200 tiny segments in a row look like one
            # smooth curve.
        prev = (px, py)

    canvas.tag_raise("control")
    # Re-raise the control point dots above the curve we just drew,
    # so they stay visible and easy to grab even after fitting.


# ============================================================
# RESET
# ============================================================

def clear_canvas():
    """
    Wipes everything and returns the app to its initial state,
    ready for a new drawing.
    """
    global mode, control_points, raw_points
    mode = "draw"
    control_points = []
    raw_points = []
    canvas.delete("stroke")
    canvas.delete("curve")
    canvas.delete("control")
    result_label.config(text="")


# ============================================================
# BUILDING THE WINDOW (UI SETUP)
# ============================================================

root = tk.Tk()
# Creates the main application window. Everything else attaches to this.

root.title("Reverse Desmos")
# Sets the text shown in the window's title bar.

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="white")
# The drawable area itself — a blank white rectangle we can draw
# shapes and lines onto using the canvas.create_* methods.

canvas.pack()
# .pack() is tkinter's simplest layout manager — it just places the
# widget into the window, stacking things top-to-bottom by default.

draw_grid()
# Draw the coordinate grid once, immediately, before the user does
# anything.

# --- Connect mouse events on the CANVAS ITSELF to our functions ---
canvas.bind("<Button-1>", start_draw)
# "<Button-1>" = left mouse button pressed down.
canvas.bind("<B1-Motion>", add_point)
# "<B1-Motion>" = mouse moved WHILE the left button is held down.
canvas.bind("<ButtonRelease-1>", stop_draw)
# Left mouse button released.

# --- Connect mouse events to control points SPECIFICALLY ---
# tag_bind (as opposed to canvas.bind) only fires when the event
# happens on a canvas item that has this specific tag — so these
# only trigger when interacting with an orange dot, not blank canvas.
canvas.tag_bind("control", "<Button-1>", on_dot_press)
canvas.tag_bind("control", "<B1-Motion>", on_dot_drag)
canvas.tag_bind("control", "<ButtonRelease-1>", on_dot_release)

# --- Build the row of controls below the canvas (degree, buttons) ---
controls = tk.Frame(root)
# A Frame is an invisible container used to group widgets together
# so they can be laid out as a unit (here, all in one horizontal row).
controls.pack(pady=10)
# pady adds 10 pixels of vertical padding above/below this frame.

tk.Label(controls, text="Degree:").pack(side=tk.LEFT)
# A plain text label, placed at the left side of the controls row.

degree_var = tk.StringVar(value="2")
# A special tkinter variable that automatically stays in sync with
# whatever the dropdown menu currently shows. Starts at "2".

degree_menu = tk.OptionMenu(controls, degree_var, "1", "2", "3", "4", "5")
# A dropdown letting the user pick a degree from 1 to 5, tied to
# degree_var.
degree_menu.pack(side=tk.LEFT, padx=5)
# padx adds horizontal spacing between this and neighboring widgets.

finish_button = tk.Button(controls, text="Finish Drawing", command=finish_drawing)
# command=finish_drawing means this function runs when the button
# is clicked (note: no parentheses — we're passing the FUNCTION
# ITSELF, not calling it right now).
finish_button.pack(side=tk.LEFT, padx=5)

fit_button = tk.Button(controls, text="Fit", command=fit_curve)
fit_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(controls, text="Clear", command=clear_canvas)
clear_button.pack(side=tk.LEFT, padx=5)

result_label = tk.Label(root, text="", font=("Arial", 12))
# This label starts empty and gets updated by our functions (e.g.
# showing the equation, or error messages like "Draw a line first").
result_label.pack(pady=5)

root.mainloop()
# Starts tkinter's event loop — this is what actually keeps the
# window open and responsive, continuously listening for clicks,
# drags, and button presses, and calling our bound functions in
# response. Nothing after this line runs until the window is closed.