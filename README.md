# Reverse Desmos

A tool that flips the usual Desmos workflow: instead of typing a function to see its graph,
you draw points/a curve, pick a polynomial degree, and the app finds a function that fits it.

## Features

- Click on a canvas to place points
- Choose a polynomial degree (1–5)
- Fit a curve to your points using least-squares regression (`numpy.polyfit`)
- View the resulting equation and see it overlaid on your points

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

Early prototype — currently a desktop app (tkinter). Planned: web version, freehand curve drawing (not just points).
