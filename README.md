# Reverse Desmos

A tool that flips the usual Desmos workflow: instead of typing a function to see its graph,
you draw a curve freehand, adjust the key points, and the app finds a polynomial function
that fits it.

## Features

- **Freehand drawing** on a coordinate grid with labeled x/y axes
- **Editable control points** — after finishing your drawing, points are placed along
  your stroke as draggable dots, so you can fine-tune the shape before fitting (rather than
  the app just guessing off your raw hand-drawn line)
- **Points slider** — pick how many control points to place (4–30, default 12)
- Choose a polynomial degree (1–5) to fit
- Fit a curve to your control points using least-squares regression (`numpy.polyfit`)
- View the resulting equation, with the fitted curve drawn in red over your (faded) original
  stroke

## How it works

1. Click and drag on the canvas to draw a curve
2. Set the **Points** slider, then click **Finish Drawing** — your stroke fades, and draggable orange control points appear
   along it
3. Drag any point to adjust it
4. Pick a degree and click **Fit** — the equation appears below the canvas
5. Click **Clear** to start over

## Setup

```bash
git clone https://github.com/AbhiBhandari01/Reverse-Desmos.git
cd Reverse-Desmos
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
pip install -r requirements.txt
```

## Run

```bash
python src/app.py
```

## Status

Working prototype (desktop app, tkinter). Planned:

- Zoom/pan on the grid
- Web version
