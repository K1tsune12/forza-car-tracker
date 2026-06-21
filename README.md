# Forza Horizon 6 Car Collection Tracker

A simple desktop app to track which Forza Horizon 6 cars you own, with smart
search, advanced filters, light/dark themes and TXT export. Built with Python +
Tkinter (no runtime dependencies) and packaged into a single Windows `.exe`.

![Version](https://img.shields.io/badge/version-1.1-blue)

## Features

- ☑️ **Check off the cars you own**: click the *Have* box, double-click a row,
  or press **Space**. Progress is saved automatically.
- 🔍 **Smart search** across every field (multi-term, e.g. `acura 2022 supercar`).
- ⚙️ **Advanced search panel**: filter by **Make, Collection, Country,
  Car Type, Car Class, Add-Ons** and a **Year** range. All filters combine.
- 🎨 **Light & dark themes** (remembers your choice).
- 📐 **Smart resizing**: columns fluidly fill the window with a minimum width;
  the horizontal scrollbar kicks in when it gets narrow.
- ⌨️ **Keyboard & multi-select**: arrows, Shift/Ctrl+click, Ctrl+A, plus
  *Select all / Check / Uncheck* bulk actions.
- ⤓ **Export to TXT**: export the current search results or just the selected
  cars to a readable text file.
- 🪟 **Remembers** window size, position and maximized state.
- 📊 Footer progress bar with the owned counter.

## Run from source

```bash
python forza_car_tracker.py
```

Requires Python 3.x (uses only the standard library + Tkinter).

## Build the executable

Run `build.bat` (Windows). It installs PyInstaller and produces
`dist/Forza Car Tracker.exe`, a single self-contained file with the car list,
logo and icon bundled in.

## Files

| File | What it is |
|------|------------|
| `forza_car_tracker.py` | The application |
| `cars.json` | The car list (Forza Horizon 6) |
| `image.png` | Forza Horizon logo (header) |
| `icon.png` / `icon.ico` | App icon |
| `build.bat` | Builds the `.exe` with PyInstaller |

Your progress is stored in `owned_cars.json` and your preferences in
`settings.json`, both created next to the app on first run.

## Disclaimer

This is an unofficial fan-made tool. *Forza Horizon*, its logo and the car
list are property of Microsoft / Playground Games. Not affiliated with or
endorsed by them.
