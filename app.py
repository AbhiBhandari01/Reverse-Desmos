import tkinter as tk
import numpy as np

points = []

def on_click(event):
    x, y = event.x, event.y
    points.append((x, y))
    radius = 3
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="blue")

def fit_curve():
    if len(points) < 2:
        result_label.config(text="Add at least 2 points first")
        return

    degree = int(degree_var.get())

    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])

    if degree >= len(points):
        result_label.config(text=f"Need at least {degree + 1} points for degree {degree}")
        return

    # fit polynomial: ys = f(xs)
    coeffs = np.polyfit(xs, ys, degree)

    # build a readable equation string
    terms = []
    n = len(coeffs)
    for i, c in enumerate(coeffs):
        power = n - i - 1
        c_rounded = round(c, 4)
        if power == 0:
            terms.append(f"{c_rounded}")
        elif power == 1:
            terms.append(f"{c_rounded}x")
        else:
            terms.append(f"{c_rounded}x^{power}")
    equation = "y = " + " + ".join(terms)

    result_label.config(text=equation)

    # draw the fitted curve
    canvas.delete("curve")
    poly = np.poly1d(coeffs)
    x_range = np.linspace(min(xs), max(xs), 200)
    y_range = poly(x_range)
    for i in range(len(x_range) - 1):
        canvas.create_line(x_range[i], y_range[i], x_range[i+1], y_range[i+1],
                            fill="red", width=2, tags="curve")

def clear_canvas():
    global points
    points = []
    canvas.delete("all")
    result_label.config(text="")

root = tk.Tk()
root.title("Reverse Desmos")

canvas = tk.Canvas(root, width=600, height=400, bg="white")
canvas.pack()
canvas.bind("<Button-1>", on_click)

controls = tk.Frame(root)
controls.pack(pady=10)

tk.Label(controls, text="Degree:").pack(side=tk.LEFT)
degree_var = tk.StringVar(value="1")
degree_menu = tk.OptionMenu(controls, degree_var, "1", "2", "3", "4", "5")
degree_menu.pack(side=tk.LEFT, padx=5)

fit_button = tk.Button(controls, text="Fit", command=fit_curve)
fit_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(controls, text="Clear", command=clear_canvas)
clear_button.pack(side=tk.LEFT, padx=5)

result_label = tk.Label(root, text="", font=("Arial", 12))
result_label.pack(pady=5)

root.mainloop()