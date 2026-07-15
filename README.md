# Forza Horizon Car Collection Tracker

A simple desktop app to track which Forza Horizon cars you own, with smart
search, advanced filters, light/dark themes and TXT export. Built with Python +
Tkinter (no runtime dependencies) and packaged into a single Windows `.exe`.

![Version](https://img.shields.io/badge/version-1.3-blue)

## Features

- 🎮 **Two games in tabs**: switch between **Forza Horizon 6** (627 cars) and
  **Forza Horizon 5** (902 cars) from the tabs at the top. The two lists are
  fully independent — your owned/progress for each game is tracked separately
  and never mixed. FH6 loads by default.
- ☑️ **Check off the cars you own**: click the *Have* box, double-click a row,
  or press **Space**. Progress is saved automatically (per game).
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
python src/forza_car_tracker.py
```

Requires Python 3.x (uses only the standard library + Tkinter).

## Build the executable

Run `packaging/build.bat` (Windows). It installs PyInstaller and produces
`dist/Forza Car Tracker.exe`, a single self-contained file with the car list,
logo and icon bundled in.

## Project layout

```
forza-car-tracker/
  src/forza_car_tracker.py    The application
  data/cars.json              The car list (Forza Horizon 6)
  data/cars_fh5.json          The car list (Forza Horizon 5)
  assets/image.png            Forza Horizon logo (header)
  assets/icon.png, icon.ico   App icon
  packaging/build.bat         Builds the .exe with PyInstaller
```

Your progress is stored per game in `owned_fh6.json` and `owned_fh5.json`, and
your preferences (theme, window, last game) in `settings.json` — all created
next to the app on first run (next to the `.exe` when built, or in the project
root when running from source). An older single-file `owned_cars.json` is
migrated automatically to the FH6 progress the first time you run this version.

## Disclaimer

This is an unofficial fan-made tool. *Forza Horizon*, its logo and the car
list are property of Microsoft / Playground Games. Not affiliated with or
endorsed by them.
