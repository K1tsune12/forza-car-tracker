"""
Forza Horizon 6 - Car Collection Tracker
----------------------------------------
A simple desktop app to track which cars you own, with smart search
across every field and light / dark themes.

Run:      python forza_car_tracker.py
Build exe: see build.bat  (PyInstaller)
"""

import os
import re
import sys
import json
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Collection tags and Car Class categories, in a sensible display order.
COLLECTION_TAGS = ["Autoshow", "Wheelspin", "Seasonal", "Collection Journal",
                   "Autoshow DLC", "Loyalty", "Aftermarket"]
CLASS_CATEGORIES = ["D", "C", "B", "A", "S1", "S2", "R"]


# ----------------------------------------------------------------------------
# Paths / data loading
# ----------------------------------------------------------------------------
def resource_path(relative):
    """Path to a bundled resource, works in dev and inside a PyInstaller exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def app_dir():
    """Folder where the running program lives (next to the .exe when frozen)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


OWNED_FILE = os.path.join(app_dir(), "owned_cars.json")
SETTINGS_FILE = os.path.join(app_dir(), "settings.json")


def load_cars():
    """Load the bundled car list; returns (headers, list-of-car-dicts)."""
    with open(resource_path("cars.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["headers"], data["cars"]


def load_owned():
    """Return the set of owned car ids saved on disk (empty if none yet)."""
    try:
        with open(OWNED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_owned(owned):
    """Persist the set of owned car ids to disk."""
    with open(OWNED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(owned), f, ensure_ascii=False, indent=1)


def load_settings():
    """Return the saved settings dict (empty if none saved yet)."""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_settings(settings):
    """Persist the settings dict (e.g. the chosen theme) to disk."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=1)


# ----------------------------------------------------------------------------
# Themes
# ----------------------------------------------------------------------------
THEMES = {
    "dark": {
        "bg": "#1e1f26",
        "panel": "#2a2c36",
        "fg": "#e6e6e6",
        "muted": "#9aa0ad",
        "accent": "#4f8cff",
        "field_bg": "#2a2c36",
        "field_fg": "#ffffff",
        "tree_bg": "#23252e",
        "tree_fg": "#e6e6e6",
        "tree_alt": "#272a34",
        "sel_bg": "#3a5b9a",
        "sel_fg": "#ffffff",
        "heading_bg": "#2f323d",
        "heading_fg": "#cfd3dc",
        "owned_fg": "#5ad17a",
        "border": "#3a3d49",
        "header_bg": "#121319",
        "bar_trough": "#2b3a57",
    },
    "light": {
        "bg": "#f3f4f7",
        "panel": "#ffffff",
        "fg": "#1c1e24",
        "muted": "#5d6470",
        "accent": "#2563eb",
        "field_bg": "#ffffff",
        "field_fg": "#1c1e24",
        "tree_bg": "#ffffff",
        "tree_fg": "#1c1e24",
        "tree_alt": "#f0f2f6",
        "sel_bg": "#cfe0ff",
        "sel_fg": "#0b1f44",
        "heading_bg": "#e7eaf0",
        "heading_fg": "#2a2e38",
        "owned_fg": "#1a9e4b",
        "border": "#d4d8e0",
        "header_bg": "#1b1d24",
        "bar_trough": "#cfe0ff",
    },
}

APP_VERSION = "1.2"

CHECK_ON = "☑"   # ☑
CHECK_OFF = "☐"  # ☐


# ----------------------------------------------------------------------------
# App
# ----------------------------------------------------------------------------
class CarTracker(tk.Tk):
    """Main application window: the car table, search, themes and bulk actions."""

    def __init__(self):
        super().__init__()
        # Hide the window until it is fully built, themed and positioned, so the
        # user never sees the empty white window appear and then jump into place.
        self.withdraw()
        self.configure(bg=THEMES.get("dark", {}).get("bg", "#1e1f26"))
        self.title(f"Forza Horizon 6 - Car Collection Tracker  v{APP_VERSION}")
        self.minsize(900, 500)

        # Window / taskbar icon
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except (tk.TclError, OSError):
            try:
                self._icon_img = tk.PhotoImage(file=resource_path("icon.png"))
                self.iconphoto(True, self._icon_img)
            except (tk.TclError, OSError):
                pass

        self.headers, self.cars = load_cars()
        # give every car a stable id (Make + Car Name should be unique enough)
        # and pull the model year out of the leading digits of the name.
        for i, c in enumerate(self.cars):
            c["_id"] = c.get("Car Name", "") + " | " + c.get("Make", "") or str(i)
            ym = re.match(r"\s*(\d{4})\b", c.get("Car Name", ""))
            c["_year"] = int(ym.group(1)) if ym else None

        self.owned = load_owned()
        self.settings = load_settings()
        self.theme_name = self.settings.get("theme", "dark")
        self._restore_geometry()

        # distinct values for the advanced-filter dropdowns
        self.makes = sorted({c.get("Make", "") for c in self.cars if c.get("Make")})
        self.countries = sorted({c.get("Country", "") for c in self.cars
                                 if c.get("Country")})
        self.car_types = sorted({c.get("Car Type", "") for c in self.cars
                                 if c.get("Car Type")})
        self.add_ons = sorted({c.get("Add-Ons", "") for c in self.cars
                               if c.get("Add-Ons")})
        self.years = sorted({c["_year"] for c in self.cars if c["_year"]})
        self.car_by_id = {c["_id"]: c for c in self.cars}

        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")
        # advanced-filter variables (one per field), default "All"
        self.adv_vars = {f: tk.StringVar(value="All") for f in
                         ("Make", "Collection", "Country", "Car Type",
                          "Car Class", "Add-Ons")}
        self.year_from_var = tk.StringVar(value="All")
        self.year_to_var = tk.StringVar(value="All")
        self.adv_open = False
        self.sort_col = None
        self.sort_reverse = False

        self.style = ttk.Style(self)
        self._build_ui()
        self._build_advanced_panel()
        self.apply_theme(self.theme_name)
        self.refresh_table()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Everything is built, themed and positioned: now reveal the window in
        # one go (no white ghost, no visible jump to the saved position).
        self.update_idletasks()
        self.deiconify()
        if self.settings.get("maximized"):
            self.state("zoomed")

    def _virtual_desktop(self):
        """(x, y, w, h) of the whole virtual desktop spanning every monitor.

        winfo_screenwidth/height only describe the primary monitor, so on a
        multi-monitor setup we ask Windows for the full virtual screen instead.
        """
        if sys.platform == "win32":
            try:
                user32 = ctypes.windll.user32
                # SM_XVIRTUALSCREEN=76 Y=77 CXVIRTUALSCREEN=78 CY=79
                x = user32.GetSystemMetrics(76)
                y = user32.GetSystemMetrics(77)
                w = user32.GetSystemMetrics(78)
                h = user32.GetSystemMetrics(79)
                if w > 0 and h > 0:
                    return x, y, w, h
            except (OSError, AttributeError, ValueError):
                pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def _center_on_primary(self, w, h):
        """Place a w x h window roughly centered on the primary monitor."""
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 3)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _restore_geometry(self):
        """Restore saved size/position, validated against ALL monitors.

        The window is only restored where it was if a usable strip of it (incl.
        the title bar) still falls inside the virtual desktop. If the monitor it
        lived on is gone or its layout changed, we re-center on the primary one.
        """
        geom = self.settings.get("geometry")
        m = re.fullmatch(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geom or "")
        if not m:
            self._center_on_primary(1180, 720)
            return
        w, h, x, y = (int(m.group(1)), int(m.group(2)),
                      int(m.group(3)), int(m.group(4)))
        vx, vy, vw, vh = self._virtual_desktop()
        w = max(900, min(w, vw))
        h = max(500, min(h, vh))
        margin = 120  # how much of the window must stay reachable
        reachable = (x + w > vx + margin and x < vx + vw - margin
                     and vy <= y < vy + vh - 40)
        if reachable:
            self.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self._center_on_primary(w, h)

    # ---- UI construction ----
    def _build_ui(self):
        # Header banner with the (white) logo on a dark strip so it shows in
        # both light and dark themes.
        self.logo_img = None
        try:
            self.logo_img = tk.PhotoImage(file=resource_path("image.png"))
        except (tk.TclError, OSError):
            self.logo_img = None

        self.header = tk.Frame(self)
        self.header.pack(side="top", fill="x")
        if self.logo_img is not None:
            self.logo_label = tk.Label(self.header, image=self.logo_img, borderwidth=0)
        else:
            self.logo_label = tk.Label(self.header, text="FORZA HORIZON 6",
                                       font=("Segoe UI", 18, "bold"), fg="#ffffff")
        self.logo_label.pack(side="left", padx=18, pady=12)

        self.version_label = tk.Label(self.header, text=f"v{APP_VERSION}",
                                      font=("Segoe UI", 10))
        self.version_label.pack(side="right", padx=18)

        # Top toolbar
        self.toolbar = tk.Frame(self)
        self.toolbar.pack(side="top", fill="x", padx=12, pady=(12, 6))

        self.search_label = tk.Label(self.toolbar, text="Search:")
        self.search_label.pack(side="left")

        self.search_entry = tk.Entry(
            self.toolbar, textvariable=self.search_var, width=40,
            relief="flat", highlightthickness=1,
        )
        self.search_entry.pack(side="left", padx=(6, 4), ipady=4)
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        self.search_entry.bind("<Escape>", lambda e: self.search_var.set(""))

        self.clear_btn = tk.Button(
            self.toolbar, text="Clear", relief="flat", cursor="hand2",
            command=lambda: self.search_var.set(""),
        )
        self.clear_btn.pack(side="left", padx=(0, 12))

        self.filter_label = tk.Label(self.toolbar, text="Show:")
        self.filter_label.pack(side="left")
        self.filter_combo = ttk.Combobox(
            self.toolbar, textvariable=self.filter_var, state="readonly", width=12,
            values=["All", "Owned", "Not owned"],
        )
        self.filter_combo.pack(side="left", padx=(6, 12))
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        self.adv_btn = tk.Button(
            self.toolbar, text="⚙ Advanced search ▾", relief="flat",
            cursor="hand2", command=self.toggle_advanced,
        )
        self.adv_btn.pack(side="left")

        self.theme_btn = tk.Button(
            self.toolbar, text="Theme", relief="flat", cursor="hand2",
            command=self.toggle_theme,
        )
        self.theme_btn.pack(side="right")

        # Selection / bulk-action bar
        self.actions = tk.Frame(self)
        self.actions.pack(side="top", fill="x", padx=12, pady=(0, 6))

        self.action_btns = []

        def add_action(text, cmd):
            b = tk.Button(self.actions, text=text, relief="flat", cursor="hand2",
                          command=cmd, padx=10)
            b.pack(side="left", padx=(0, 6))
            self.action_btns.append(b)
            return b

        add_action("Select all (visible)", self.select_all_visible)
        add_action("Select none", self.select_none)
        self.check_btn = add_action("✓ Check selected", self.check_selected)
        self.uncheck_btn = add_action("✗ Uncheck selected", self.uncheck_selected)
        add_action("⤓ Export results", self.export_results)
        add_action("⤓ Export selected", self.export_selected)

        self.sel_label = tk.Label(self.actions, text="0 selected", anchor="e")
        self.sel_label.pack(side="right")

        # Info row (tip + how many are showing) - grid so the hint can shrink
        self.progress_frame = tk.Frame(self)
        self.progress_frame.pack(side="top", fill="x", padx=12, pady=(0, 6))
        self.progress_frame.columnconfigure(1, weight=1)
        self.shown_label = tk.Label(self.progress_frame, text="", anchor="w")
        self.shown_label.grid(row=0, column=0, sticky="w")
        self.hint_label = tk.Label(
            self.progress_frame,
            text=("Tip: ↑/↓ move · Shift/Ctrl+click multi-select · "
                  "Ctrl+A all · Space toggles selection"),
            anchor="e",
        )
        self.hint_label.grid(row=0, column=1, sticky="e", padx=(12, 0))

        # Footer / status bar (owned counter) - stays pinned to the bottom.
        # grid with a weighted middle column lets the progress bar stretch and
        # shrink with the window while the labels stay glued to the edges.
        self.footer = tk.Frame(self)
        self.footer.pack(side="bottom", fill="x")
        self.footer_inner = tk.Frame(self.footer)
        self.footer_inner.pack(fill="x", padx=12, pady=8)
        self.footer_inner.columnconfigure(1, weight=1)

        self.count_label = tk.Label(
            self.footer_inner, text="", anchor="w",
            font=("Segoe UI", 11, "bold"),
        )
        self.count_label.grid(row=0, column=0, sticky="w")

        self.progressbar = ttk.Progressbar(
            self.footer_inner, orient="horizontal", mode="determinate",
            maximum=100,
        )
        self.progressbar.grid(row=0, column=1, sticky="ew", padx=12)

        self.pct_label = tk.Label(self.footer_inner, text="", anchor="e", width=12)
        self.pct_label.grid(row=0, column=2, sticky="e")

        # Table
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ["owned"] + self.headers
        self.tree = ttk.Treeview(
            self.table_frame, columns=columns, show="headings", selectmode="extended",
        )

        self.tree.heading("owned", text="Have", command=lambda: self.sort_by("owned"))
        self.tree.column("owned", width=55, minwidth=55, anchor="center", stretch=False)

        # (preferred width, minimum width) per column.
        # stretch=True -> columns fluidly share spare space when the window is wide
        # (the "smart" resize), while minwidth stops them from squashing and
        # clipping text. Below the sum of minwidths the horizontal bar takes over.
        widths = {
            "Make":       (130, 90),
            "Car Name":   (300, 190),
            "Car Type":   (150, 105),
            "Car Class":  (90, 65),
            "Country":    (110, 75),
            "Collection": (190, 125),
            "Add-Ons":    (160, 95),
        }
        for h in self.headers:
            w, mw = widths.get(h, (120, 80))
            self.tree.heading(h, text=h, command=lambda c=h: self.sort_by(c))
            self.tree.column(h, width=w, minwidth=mw, anchor="w", stretch=True)

        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.table_frame.rowconfigure(0, weight=1)
        self.table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Button-1>", self.on_click)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<space>", self.on_space)
        self.tree.bind("<Return>", self.on_space)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.update_sel_count())
        # Ctrl+A selects every visible row; Ctrl+D clears selection
        self.bind_all("<Control-a>", lambda e: (self.select_all_visible(), "break")[1])
        self.bind_all("<Control-A>", lambda e: (self.select_all_visible(), "break")[1])
        self.bind_all("<Control-d>", lambda e: (self.select_none(), "break")[1])
        # ↑/↓ arrows already move the selection natively (extended mode);
        # Shift+↑/↓ extends it, Ctrl/Shift+click builds a custom selection.

    def _build_advanced_panel(self):
        """Build the collapsible advanced-filter panel (one dropdown per field)."""
        self.adv_panel = tk.Frame(self)  # packed/unpacked by toggle_advanced
        self.adv_labels = []
        self.adv_combos = {}

        field_values = {
            "Make": ["All"] + self.makes,
            "Collection": ["All"] + COLLECTION_TAGS,
            "Country": ["All"] + self.countries,
            "Car Type": ["All"] + self.car_types,
            "Car Class": ["All"] + CLASS_CATEGORIES,
            "Add-Ons": ["All"] + self.add_ons,
        }
        # lay fields out in a 3-column grid of (label, dropdown) pairs
        for i, (field, values) in enumerate(field_values.items()):
            r, c = divmod(i, 3)
            lbl = tk.Label(self.adv_panel, text=field + ":", anchor="w")
            lbl.grid(row=r, column=c * 2, sticky="w", padx=(0, 6), pady=4)
            self.adv_labels.append(lbl)
            combo = ttk.Combobox(self.adv_panel, textvariable=self.adv_vars[field],
                                 state="readonly", values=values, width=22)
            combo.grid(row=r, column=c * 2 + 1, sticky="w", padx=(0, 18), pady=4)
            combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
            self.adv_combos[field] = combo

        # Year range: two dropdowns (from / to) on their own row
        year_values = ["All"] + [str(y) for y in self.years]
        ylbl = tk.Label(self.adv_panel, text="Year:", anchor="w")
        ylbl.grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        self.adv_labels.append(ylbl)
        self.year_from_combo = ttk.Combobox(
            self.adv_panel, textvariable=self.year_from_var, state="readonly",
            values=year_values, width=9)
        self.year_from_combo.grid(row=2, column=1, sticky="w", padx=(0, 6), pady=4)
        tolbl = tk.Label(self.adv_panel, text="to", anchor="w")
        tolbl.grid(row=2, column=2, sticky="w", padx=(0, 6), pady=4)
        self.adv_labels.append(tolbl)
        self.year_to_combo = ttk.Combobox(
            self.adv_panel, textvariable=self.year_to_var, state="readonly",
            values=year_values, width=9)
        self.year_to_combo.grid(row=2, column=3, sticky="w", padx=(0, 18), pady=4)
        for combo in (self.year_from_combo, self.year_to_combo):
            combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        self.adv_clear_btn = tk.Button(
            self.adv_panel, text="Clear filters", relief="flat", cursor="hand2",
            command=self.clear_filters, padx=10,
        )
        self.adv_clear_btn.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))

    def toggle_advanced(self):
        """Show or hide the advanced-filter panel."""
        self.adv_open = not self.adv_open
        if self.adv_open:
            self.adv_panel.pack(after=self.toolbar, fill="x", padx=12, pady=(0, 6))
            self.adv_btn.configure(text="⚙ Advanced search ▴")
        else:
            self.adv_panel.pack_forget()
            self.adv_btn.configure(text="⚙ Advanced search ▾")

    def clear_filters(self):
        """Reset every advanced dropdown (incl. year range) back to 'All'."""
        for var in self.adv_vars.values():
            var.set("All")
        self.year_from_var.set("All")
        self.year_to_var.set("All")
        self.refresh_table()

    # ---- Export ----
    def export_cars_txt(self, cars, suggested, title):
        """Save a list of cars to a readable plain-text (.txt) file."""
        if not cars:
            messagebox.showinfo("Export", "There is nothing to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export cars to TXT", defaultextension=".txt",
            initialfile=suggested,
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                heading = f"Forza Horizon 6 - {title} ({len(cars)})"
                f.write(heading + "\n")
                f.write("=" * len(heading) + "\n\n")
                for i, c in enumerate(cars, 1):
                    mark = "[x]" if c["_id"] in self.owned else "[ ]"
                    parts = [c.get("Car Type", ""), c.get("Car Class", ""),
                             c.get("Country", ""), c.get("Collection", "")]
                    details = " - ".join(p for p in parts if p)
                    f.write(f"{i:>3}. {mark} {c.get('Car Name', '')}\n")
                    if details:
                        f.write(f"      {details}\n")
        except OSError as exc:
            messagebox.showerror("Export error", str(exc))
            return
        messagebox.showinfo("Export",
                            f"Exported {len(cars)} cars to:\n{path}")

    def export_results(self):
        """Export every car currently shown (after search + filters) as TXT."""
        self.export_cars_txt(self.visible_cars(),
                             "forza_cars_results.txt", "Search results")

    def export_selected(self):
        """Export only the currently selected rows as a TXT list."""
        cars = [self.car_by_id[i] for i in self.tree.selection()
                if i in self.car_by_id]
        self.export_cars_txt(cars, "forza_cars_selected.txt", "Selected cars")

    # ---- Theming ----
    def toggle_theme(self):
        """Switch between the light and dark themes."""
        self.apply_theme("light" if self.theme_name == "dark" else "dark")
        self.refresh_table()

    def apply_theme(self, name):
        """Apply the named theme ('light'/'dark') to every widget."""
        self.theme_name = name
        t = THEMES[name]

        # Pick the ttk base theme FIRST. theme_use() resets every style to its
        # defaults, so any style.configure() must come after it - otherwise the
        # progress bar (and others) snap back to clam's gray.
        self.style.theme_use("clam")

        self.configure(bg=t["bg"])
        for frame in (self.toolbar, self.actions, self.adv_panel,
                      self.progress_frame, self.table_frame):
            frame.configure(bg=t["bg"])
        for frame in (self.footer, self.footer_inner):
            frame.configure(bg=t["panel"])
        self.header.configure(bg=t["header_bg"])
        self.logo_label.configure(bg=t["header_bg"])

        for lbl in (self.search_label, self.filter_label,
                    self.shown_label, self.hint_label, self.sel_label,
                    *self.adv_labels):
            lbl.configure(bg=t["bg"], fg=t["fg"])
        self.hint_label.configure(fg=t["muted"])
        self.shown_label.configure(fg=t["muted"])
        self.sel_label.configure(fg=t["muted"])

        self.count_label.configure(bg=t["panel"], fg=t["fg"])
        self.pct_label.configure(bg=t["panel"], fg=t["muted"])
        self.version_label.configure(bg=t["header_bg"], fg=t["muted"])
        # clam uses the orientation-specific style name, so configure that one
        # (plus the base) or the filled bar stays the default gray.
        for st in ("TProgressbar", "Horizontal.TProgressbar"):
            self.style.configure(
                st, background=t["accent"], troughcolor=t["bar_trough"],
                bordercolor=t["bar_trough"], lightcolor=t["accent"],
                darkcolor=t["accent"], borderwidth=0, thickness=16,
            )

        self.search_entry.configure(
            bg=t["field_bg"], fg=t["field_fg"], insertbackground=t["field_fg"],
            highlightbackground=t["border"], highlightcolor=t["accent"],
        )
        for btn in (self.clear_btn, self.theme_btn, self.adv_btn,
                    self.adv_clear_btn, *self.action_btns):
            btn.configure(bg=t["panel"], fg=t["fg"],
                          activebackground=t["accent"], activeforeground="#ffffff")
        # accent the two main bulk-action buttons
        self.check_btn.configure(fg=t["owned_fg"])
        self.theme_btn.configure(
            text=("Light mode ☀" if name == "dark" else "Dark mode ☽")
        )

        # ttk widgets
        self.style.configure(
            "Treeview",
            background=t["tree_bg"], fieldbackground=t["tree_bg"],
            foreground=t["tree_fg"], rowheight=26, borderwidth=0,
        )
        self.style.map(
            "Treeview",
            background=[("selected", t["sel_bg"])],
            foreground=[("selected", t["sel_fg"])],
        )
        self.style.configure(
            "Treeview.Heading",
            background=t["heading_bg"], foreground=t["heading_fg"],
            relief="flat", padding=6,
        )
        self.style.map("Treeview.Heading",
                       background=[("active", t["accent"])],
                       foreground=[("active", "#ffffff")])
        # Combobox: field, arrow button and the focus/selection states
        self.style.configure(
            "TCombobox",
            fieldbackground=t["field_bg"], background=t["panel"],
            foreground=t["field_fg"], arrowcolor=t["fg"],
            bordercolor=t["border"], lightcolor=t["panel"],
            darkcolor=t["panel"], relief="flat", padding=4,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["field_bg"]), ("disabled", t["panel"])],
            foreground=[("readonly", t["field_fg"])],
            background=[("active", t["panel"]), ("pressed", t["panel"])],
            arrowcolor=[("active", t["accent"])],
            selectbackground=[("readonly", t["field_bg"])],
            selectforeground=[("readonly", t["field_fg"])],
        )
        # Combobox drop-down list (a Tk Listbox under the hood -> option database)
        self.option_add("*TCombobox*Listbox.background", t["field_bg"])
        self.option_add("*TCombobox*Listbox.foreground", t["field_fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.borderWidth", 0)
        # Re-style the already-built drop-down so theme toggles take effect now
        try:
            popdown = self.tk.call("ttk::combobox::PopdownWindow", self.filter_combo)
            self.tk.call(popdown + ".f.l", "configure",
                         "-background", t["field_bg"],
                         "-foreground", t["field_fg"],
                         "-selectbackground", t["accent"],
                         "-selectforeground", "#ffffff")
        except tk.TclError:
            pass

        # Scrollbars (both orientations)
        for orient in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            self.style.configure(
                orient,
                background=t["heading_bg"], troughcolor=t["bg"],
                bordercolor=t["bg"], arrowcolor=t["muted"],
                relief="flat", borderwidth=0,
            )
            self.style.map(
                orient,
                background=[("active", t["accent"]), ("pressed", t["accent"])],
                arrowcolor=[("active", "#ffffff")],
            )

        self.tree.tag_configure("odd", background=t["tree_bg"], foreground=t["tree_fg"])
        self.tree.tag_configure("even", background=t["tree_alt"], foreground=t["tree_fg"])
        self.tree.tag_configure("owned", foreground=t["owned_fg"])

        self.settings["theme"] = name
        save_settings(self.settings)

    # ---- Filtering / smart search ----
    def matches(self, car, terms):
        """Smart search: every whitespace-separated term must appear in some field."""
        haystack = " ".join(str(car.get(h, "")) for h in self.headers).lower()
        return all(term in haystack for term in terms)

    def adv_match(self, car):
        """True if a car satisfies every active advanced-filter dropdown."""
        for field, var in self.adv_vars.items():
            sel = var.get()
            if sel == "All":
                continue
            if field == "Collection":
                tags = [t.strip() for t in car.get("Collection", "").split(",")]
                if sel not in tags:
                    return False
            elif field == "Car Class":
                parts = car.get("Car Class", "").split()
                if not parts or parts[-1] != sel:
                    return False
            elif car.get(field, "") != sel:
                return False

        # year range (from / to dropdowns)
        year = car.get("_year")
        yf, yt = self.year_from_var.get(), self.year_to_var.get()
        if yf != "All" and (year is None or year < int(yf)):
            return False
        if yt != "All" and (year is None or year > int(yt)):
            return False
        return True

    def visible_cars(self):
        """Return cars passing the search text, the Show filter and advanced filters."""
        terms = [w for w in self.search_var.get().lower().split() if w]
        flt = self.filter_var.get()
        out = []
        for c in self.cars:
            owned = c["_id"] in self.owned
            if flt == "Owned" and not owned:
                continue
            if flt == "Not owned" and owned:
                continue
            if terms and not self.matches(c, terms):
                continue
            if not self.adv_match(c):
                continue
            out.append(c)
        return out

    def sort_by(self, col):
        """Sort by a column; clicking the same column again reverses order."""
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
        self.refresh_table()

    def refresh_table(self, keep_selection=None):
        """Rebuild the table from the current filter/sort and update counters."""
        if keep_selection is None:
            keep_selection = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        cars = self.visible_cars()

        if self.sort_col:
            if self.sort_col == "owned":
                cars.sort(key=lambda c: c["_id"] in self.owned, reverse=self.sort_reverse)
            else:
                cars.sort(key=lambda c: str(c.get(self.sort_col, "")).lower(),
                          reverse=self.sort_reverse)

        for i, c in enumerate(cars):
            owned = c["_id"] in self.owned
            values = [CHECK_ON if owned else CHECK_OFF] + \
                     [c.get(h, "") for h in self.headers]
            tags = ["even" if i % 2 else "odd"]
            if owned:
                tags.append("owned")
            self.tree.insert("", "end", iid=c["_id"], values=values, tags=tags)

        total = len(self.cars)
        owned_n = len(self.owned)
        shown = len(cars)
        pct = (owned_n / total * 100) if total else 0
        self.shown_label.configure(text=f"Showing {shown} of {total} cars")
        self.count_label.configure(
            text=f"\U0001F697  Cars owned: {owned_n} / {total}"
        )
        self.pct_label.configure(text=f"{pct:.1f}% complete")
        self.progressbar["value"] = pct

        # restore selection on rows that still exist after filtering
        restore = [i for i in keep_selection if self.tree.exists(i)]
        if restore:
            self.tree.selection_set(restore)
            self.tree.see(restore[0])
        self.update_sel_count()

    def update_sel_count(self):
        """Refresh the 'N selected' label in the action bar."""
        n = len(self.tree.selection())
        self.sel_label.configure(text=f"{n} selected")

    # ---- Toggling ownership ----
    def set_owned_for(self, iids, value):
        """Mark every id in `iids` as owned (value=True) or not (False)."""
        changed = False
        for iid in iids:
            if value and iid not in self.owned:
                self.owned.add(iid)
                changed = True
            elif not value and iid in self.owned:
                self.owned.discard(iid)
                changed = True
        if changed:
            save_owned(self.owned)
            self.refresh_table(keep_selection=list(iids))

    def toggle(self, iid):
        """Flip a single car (used by click / double-click on one row)."""
        if not iid:
            return
        self.set_owned_for([iid], iid not in self.owned)

    # ---- Bulk actions ----
    def check_selected(self):
        """Mark every selected car as owned."""
        sel = self.tree.selection()
        if sel:
            self.set_owned_for(sel, True)

    def uncheck_selected(self):
        """Mark every selected car as not owned."""
        sel = self.tree.selection()
        if sel:
            self.set_owned_for(sel, False)

    def toggle_selected(self):
        """Smart toggle: if every selected car is owned -> uncheck all,
        otherwise -> check all. Great with Space after a multi-select."""
        sel = self.tree.selection()
        if not sel:
            return
        all_owned = all(i in self.owned for i in sel)
        self.set_owned_for(sel, not all_owned)

    def select_all_visible(self):
        """Select every row currently visible (respects search/filter)."""
        items = self.tree.get_children()
        if items:
            self.tree.selection_set(items)
            self.tree.focus_set()
            self.tree.focus(items[0])
            self.tree.see(items[0])
        self.update_sel_count()

    def select_none(self):
        """Clear the current selection."""
        self.tree.selection_remove(*self.tree.selection())
        self.update_sel_count()

    def on_click(self, event):
        """Toggle a single car when its 'Have' checkbox cell is clicked."""
        if self.tree.identify_region(event.x, event.y) != "cell":
            return None
        col = self.tree.identify_column(event.x)
        if col == "#1":  # the "Have" checkbox column -> toggle just that row
            iid = self.tree.identify_row(event.y)
            self.toggle(iid)
            return "break"
        return None

    def on_double_click(self, event):
        """Toggle the double-clicked car."""
        if self.tree.identify_region(event.x, event.y) != "cell":
            return None
        iid = self.tree.identify_row(event.y)
        self.toggle(iid)
        return "break"

    def on_space(self, event):
        """Space key -> smart-toggle the current selection."""
        self.toggle_selected()
        return "break"

    def on_close(self):
        """Save progress, theme and window geometry, then close the window."""
        save_owned(self.owned)
        self.settings["theme"] = self.theme_name
        # store a normal-state geometry (not the zoomed/maximized size)
        if self.state() == "zoomed":
            self.settings["maximized"] = True
        else:
            self.settings["maximized"] = False
            self.settings["geometry"] = self.geometry()
        save_settings(self.settings)
        self.destroy()


if __name__ == "__main__":
    try:
        app = CarTracker()
        app.mainloop()
    # Intentionally broad: this is the top-level safety net so any startup
    # failure is shown to the user instead of the window vanishing silently.
    except Exception as exc:  # pylint: disable=broad-exception-caught
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Forza Car Tracker - Error", str(exc))
        except tk.TclError:
            print("Error:", exc)
        raise
