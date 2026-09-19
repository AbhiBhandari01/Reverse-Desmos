import tkinter as tk

points = []

def on_click(event):
    x, y = event.x, event.y
    points.append((x, y))
    # draw a small dot where clicked
    radius = 3
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="blue")
    print(f"Point added: ({x}, {y})")

root = tk.Tk()
root.title("Reverse Desmos")

canvas = tk.Canvas(root, width=600, height=400, bg="white")
canvas.pack()

canvas.bind("<Button-1>", on_click)  # left mouse click

root.mainloop()