import tkinter as tk
import numpy as np

# --- Graph settings ---
WIDTH, HEIGHT = 600, 400
ORIGIN_X, ORIGIN_Y = WIDTH // 2, HEIGHT // 2
SCALE = 40  # pixels per 1 graph unit
NUM_CONTROL_POINTS = 12
DOT_RADIUS = 5

raw_points = []        # pixel coords while actively drawing
control_points = []    # list of dicts: {"canvas_id", "px", "py"}
drawing = False
mode = "draw"          # "draw" or "edit"
dragging_index = None

def pixel_to_graph(px, py):
    x = (px - ORIGIN_X) / SCALE
    y = (ORIGIN_Y - py) / SCALE
    return x, y

def draw_grid():
    canvas.delete("grid")
    x = ORIGIN_X % SCALE
    while x < WIDTH:
        canvas.create_line(x, 0, x, HEIGHT, fill="#e0e0e0", tags="grid")
        x += SCALE
    y = ORIGIN_Y % SCALE
    while y < HEIGHT:
        canvas.create_line(0, y, WIDTH, y, fill="#e0e0e0", tags="grid")
        y += SCALE
    canvas.create_line(0, ORIGIN_Y, WIDTH, ORIGIN_Y, fill="black", width=2, tags="grid")
    canvas.create_line(ORIGIN_X, 0, ORIGIN_X, HEIGHT, fill="black", width=2, tags="grid")
    for i in range(-ORIGIN_X // SCALE, (WIDTH - ORIGIN_X) // SCALE + 1):
        if i == 0:
            continue
        px = ORIGIN_X + i * SCALE
        canvas.create_text(px, ORIGIN_Y + 10, text=str(i), font=("Arial", 8), tags="grid")
    for i in range(-ORIGIN_Y // SCALE, (HEIGHT - ORIGIN_Y) // SCALE + 1):
        if i == 0:
            continue
        py = ORIGIN_Y - i * SCALE
        canvas.create_text(ORIGIN_X - 12, py, text=str(i), font=("Arial", 8), tags="grid")
    canvas.tag_lower("grid")

# --- Drawing mode ---
def start_draw(event):
    global drawing
    if mode != "draw":
        return
    drawing = True
    raw_points.clear()
    canvas.delete("stroke")
    add_point(event)

def add_point(event):
    if not drawing or mode != "draw":
        return
    x, y = event.x, event.y
    raw_points.append((x, y))
    if len(raw_points) > 1:
        x0, y0 = raw_points[-2]
        canvas.create_line(x0, y0, x, y, fill="blue", width=2, tags="stroke")

def stop_draw(event):
    global drawing
    drawing = False

# --- Finish drawing -> generate editable control points ---
def finish_drawing():
    global mode, control_points
    if len(raw_points) < 2:
        result_label.config(text="Draw a line first")
        return

    mode = "edit"

    # fade the original stroke instead of deleting it
    canvas.itemconfig("stroke", fill="#c9c9f5")

    indices = np.linspace(0, len(raw_points) - 1, NUM_CONTROL_POINTS).astype(int)
    sampled = [raw_points[i] for i in indices]

    control_points = []
    for (px, py) in sampled:
        dot_id = canvas.create_oval(
            px - DOT_RADIUS, py - DOT_RADIUS, px + DOT_RADIUS, py + DOT_RADIUS,
            fill="orange", outline="black", width=1, tags="control"
        )
        control_points.append({"id": dot_id, "px": px, "py": py})

    canvas.tag_raise("control")  # make sure dots stay clickable/on top
    result_label.config(text=f"{len(control_points)} points ready — drag to adjust, then Fit")

def on_dot_press(event):
    global dragging_index
    if mode != "edit":
        return
    clicked = canvas.find_closest(event.x, event.y)
    for i, cp in enumerate(control_points):
        if cp["id"] == clicked[0]:
            dragging_index = i
            return

def on_dot_drag(event):
    if mode != "edit" or dragging_index is None:
        return
    cp = control_points[dragging_index]
    cp["px"], cp["py"] = event.x, event.y
    canvas.coords(cp["id"], event.x - DOT_RADIUS, event.y - DOT_RADIUS,
                             event.x + DOT_RADIUS, event.y + DOT_RADIUS)

def on_dot_release(event):
    global dragging_index
    dragging_index = None

# --- Fit using current control point positions ---
def fit_curve():
    if mode != "edit" or len(control_points) < 2:
        result_label.config(text="Finish drawing first, then Fit")
        return

    degree = int(degree_var.get())
    graph_pts = [pixel_to_graph(cp["px"], cp["py"]) for cp in control_points]
    xs = np.array([p[0] for p in graph_pts])
    ys = np.array([p[1] for p in graph_pts])

    if degree >= len(control_points):
        result_label.config(text=f"Need more points for degree {degree}")
        return

    coeffs = np.polyfit(xs, ys, degree)

    terms = []
    n = len(coeffs)
    for i, c in enumerate(coeffs):
        power = n - i - 1
        c_rounded = round(c, 3)
        if power == 0:
            terms.append(f"{c_rounded}")
        elif power == 1:
            terms.append(f"{c_rounded}x")
        else:
            terms.append(f"{c_rounded}x^{power}")
    equation = "y = " + " + ".join(terms)
    result_label.config(text=equation)

    canvas.delete("curve")
    canvas.tag_raise("control")
    poly = np.poly1d(coeffs)
    x_graph_range = np.linspace(min(xs), max(xs), 200)
    y_graph_range = poly(x_graph_range)
    prev = None
    for gx, gy in zip(x_graph_range, y_graph_range):
        px = ORIGIN_X + gx * SCALE
        py = ORIGIN_Y - gy * SCALE
        if prev:
            canvas.create_line(prev[0], prev[1], px, py, fill="red", width=2, tags="curve")
        prev = (px, py)

def clear_canvas():
    global mode, control_points, raw_points
    mode = "draw"
    control_points = []
    raw_points = []
    canvas.delete("stroke")
    canvas.delete("curve")
    canvas.delete("control")
    result_label.config(text="")

root = tk.Tk()
root.title("Reverse Desmos")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="white")
canvas.pack()
draw_grid()

canvas.bind("<Button-1>", start_draw)
canvas.bind("<B1-Motion>", add_point)
canvas.bind("<ButtonRelease-1>", stop_draw)

canvas.tag_bind("control", "<Button-1>", on_dot_press)
canvas.tag_bind("control", "<B1-Motion>", on_dot_drag)
canvas.tag_bind("control", "<ButtonRelease-1>", on_dot_release)

controls = tk.Frame(root)
controls.pack(pady=10)

tk.Label(controls, text="Degree:").pack(side=tk.LEFT)
degree_var = tk.StringVar(value="2")
degree_menu = tk.OptionMenu(controls, degree_var, "1", "2", "3", "4", "5")
degree_menu.pack(side=tk.LEFT, padx=5)

finish_button = tk.Button(controls, text="Finish Drawing", command=finish_drawing)
finish_button.pack(side=tk.LEFT, padx=5)

fit_button = tk.Button(controls, text="Fit", command=fit_curve)
fit_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(controls, text="Clear", command=clear_canvas)
clear_button.pack(side=tk.LEFT, padx=5)

result_label = tk.Label(root, text="", font=("Arial", 12))
result_label.pack(pady=5)

root.mainloop()