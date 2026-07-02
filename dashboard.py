"""dashboard.py — Advanced live-analytics GUI for the Economic Simulation World Engine."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random

from economy import Economy, DEFAULT_CONFIG

# ═══════════════════════════════════════════════════════════════════════════════
# PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

BG       = "#060b14"
PANEL    = "#0d1929"
BORDER   = "#1c2f45"
TEXT     = "#dde5f0"
DIM      = "#4d6680"
ACCENT   = "#2563eb"
GREEN    = "#10d68e"
RED      = "#ef4444"
YELLOW   = "#f59e0b"
PURPLE   = "#8b5cf6"
ORANGE   = "#f97316"
TEAL     = "#06b6d4"
BLUE     = "#38bdf8"
CHART_BG = "#08111e"


# ═══════════════════════════════════════════════════════════════════════════════
# SPARKLINE  (tiny 96×22 px canvas line chart)
# ═══════════════════════════════════════════════════════════════════════════════

class Sparkline(tk.Canvas):
    W, H = 96, 22

    def __init__(self, parent, color: str = ACCENT, **kw):
        super().__init__(parent, width=self.W, height=self.H,
                         bg=PANEL, highlightthickness=0, **kw)
        self._c = color
        self._data: list[float] = []

    def push(self, v: float) -> None:
        self._data.append(v)
        if len(self._data) > 60:
            self._data.pop(0)
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        d = self._data
        n = len(d)
        if n < 2:
            return
        lo, hi = min(d), max(d)
        span = hi - lo or 1.0
        m = 2
        pts = []
        for i, v in enumerate(d):
            x = m + i / (n - 1) * (self.W - 2 * m)
            y = (self.H - m) - (v - lo) / span * (self.H - 2 * m)
            pts += [x, y]
        self.create_line(*pts, fill=self._c, width=1.5, smooth=True)
        self.create_oval(pts[-2] - 2.5, pts[-1] - 2.5,
                         pts[-2] + 2.5, pts[-1] + 2.5,
                         fill=self._c, outline="")


# ═══════════════════════════════════════════════════════════════════════════════
# STAT CARD
# ═══════════════════════════════════════════════════════════════════════════════

class StatCard(tk.Frame):
    def __init__(self, parent, label: str, description: str,
                 spark_color: str = ACCENT, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=BORDER, highlightthickness=1, **kw)
        self._prev: float | None = None

        top = tk.Frame(self, bg=PANEL)
        top.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(top, text=label, font=("Segoe UI", 7, "bold"),
                 bg=PANEL, fg=DIM).pack(side="left")
        self._trend = tk.Label(top, text="", font=("Segoe UI", 8, "bold"),
                                bg=PANEL, fg=DIM)
        self._trend.pack(side="right")

        self._v = tk.StringVar(value="—")
        self._vlbl = tk.Label(self, textvariable=self._v,
                               font=("Segoe UI", 19, "bold"), bg=PANEL, fg=TEXT)
        self._vlbl.pack(anchor="w", padx=10, pady=(1, 0))

        row = tk.Frame(self, bg=PANEL)
        row.pack(fill="x", padx=10, pady=(4, 0))
        self._spark = Sparkline(row, color=spark_color)
        self._spark.pack(side="left")

        tk.Label(self, text=description, font=("Segoe UI", 7),
                 bg=PANEL, fg=DIM, wraplength=220, justify="left"
                 ).pack(anchor="w", padx=10, pady=(4, 8))

    def update(self, formatted: str, raw: float, color: str = TEXT) -> None:
        self._v.set(formatted)
        self._vlbl.config(fg=color)
        self._spark.push(raw)
        if self._prev is not None and self._prev != 0:
            pct = (raw - self._prev) / abs(self._prev) * 100
            sym = "▲" if pct >= 0 else "▼"
            col = GREEN if pct >= 0 else RED
            self._trend.config(text=f"{sym} {abs(pct):.1f}%", fg=col)
        self._prev = raw


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT LOG
# ═══════════════════════════════════════════════════════════════════════════════

class EventLog(tk.Frame):
    _KINDS = {
        "good":    ("▲", GREEN),
        "bad":     ("▼", RED),
        "shock":   ("⚡", YELLOW),
        "report":  ("◈", BLUE),
        "neutral": ("·", DIM),
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=BORDER, highlightthickness=1, **kw)
        tk.Label(self, text="EVENT LOG", font=("Segoe UI", 7, "bold"),
                 bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(6, 2))
        self._box = tk.Frame(self, bg=PANEL)
        self._box.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        self._rows: list[tk.Frame] = []

    def add(self, month: int, text: str, kind: str = "neutral") -> None:
        sym, col = self._KINDS.get(kind, self._KINDS["neutral"])
        r = tk.Frame(self._box, bg=PANEL)
        r.pack(fill="x", pady=1, anchor="w")
        tk.Label(r, text=sym, font=("Segoe UI", 9),
                 bg=PANEL, fg=col, width=2).pack(side="left")
        tk.Label(r, text=f"M{month:02d}", font=("Courier New", 8, "bold"),
                 bg=PANEL, fg=DIM).pack(side="left", padx=(0, 5))
        tk.Label(r, text=text, font=("Segoe UI", 8),
                 bg=PANEL, fg=TEXT, anchor="w").pack(side="left")
        self._rows.append(r)
        if len(self._rows) > 6:
            self._rows[0].destroy()
            self._rows.pop(0)

    def clear(self) -> None:
        for r in self._rows:
            r.destroy()
        self._rows.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 30-MONTH REPORT WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class ReportWindow:
    _BADGE_COLORS = {
        "BOOMING":    (GREEN,  "#010409"),
        "GROWING":    (TEAL,   "#010409"),
        "STABLE":     (YELLOW, "#010409"),
        "STRUGGLING": (ORANGE, "#010409"),
        "CRISIS":     (RED,    "#ffffff"),
    }

    def __init__(self, root: tk.Tk, step: int, economy: Economy,
                 milestones: list[dict], on_close) -> None:
        self._root      = root
        self._step      = step
        self._economy   = economy
        self._milestones = milestones
        self._on_close  = on_close
        self._build()

    # ── construction ──────────────────────────────────────────────────────────

    def _build(self) -> None:
        win = tk.Toplevel(self._root)
        win.title(f"Month {self._step} — Economic Analysis Report")
        win.configure(bg=BG)
        win.resizable(False, False)

        W, H = 1000, 700
        self._root.update_idletasks()
        rx = self._root.winfo_x() + (self._root.winfo_width()  - W) // 2
        ry = self._root.winfo_y() + (self._root.winfo_height() - H) // 2
        win.geometry(f"{W}x{H}+{max(0, rx)}+{max(0, ry)}")
        win.grab_set()
        win.protocol("WM_DELETE_WINDOW", self._make_close(win))

        self._build_header(win)
        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        left = tk.Frame(body, bg=BG, width=320)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right, win)

    def _build_header(self, win: tk.Toplevel) -> None:
        hdr = tk.Frame(win, bg=ACCENT, pady=13)
        hdr.pack(fill="x")
        period = (f"Months {self._step - 29}–{self._step}"
                  if len(self._milestones) > 1 else f"Months 1–{self._step}")
        tk.Label(hdr, text=f"  MONTH {self._step}  ·  ECONOMIC ANALYSIS REPORT",
                 font=("Segoe UI", 14, "bold"), bg=ACCENT, fg="white"
                 ).pack(side="left", padx=16)
        tk.Label(hdr, text=period + "  ",
                 font=("Segoe UI", 10), bg=ACCENT, fg="#bfdbfe"
                 ).pack(side="right")

    def _build_left(self, parent: tk.Frame) -> None:
        m    = self._milestones[-1]
        prev = self._milestones[-2] if len(self._milestones) >= 2 else None

        badge, (bg_col, fg_col) = self._health_badge(m, prev)
        bf = tk.Frame(parent, bg=bg_col, padx=14, pady=8)
        bf.pack(fill="x", pady=(0, 10))
        tk.Label(bf, text="ECONOMY STATUS", font=("Segoe UI", 8),
                 bg=bg_col, fg=fg_col).pack(anchor="w")
        tk.Label(bf, text=badge, font=("Segoe UI", 20, "bold"),
                 bg=bg_col, fg=fg_col).pack(anchor="w")

        self._divider(parent, "KEY METRICS")

        rows_def = [
            ("Total Output (GDP)",    "gdp",              True,  True),
            ("Unemployment Rate",     "unemployment_rate", False, False),
            ("Inflation Rate",        "inflation",         False, False),
            ("Average Worker Wage",   "avg_wage",          True,  True),
            ("Average Price Level",   "avg_price",         True,  False),
            ("Consumer Spending",     "total_spending",    True,  True),
            ("Worker Savings",        "total_savings",     True,  True),
        ]
        for label, key, is_dollar, higher_better in rows_def:
            v = m.get(key, 0)
            vf = f"${v:,.0f}" if is_dollar else f"{v:.2f}%"
            dt, dc = self._delta_text(key, m, prev, higher_better, is_dollar)

            row = tk.Frame(parent, bg=PANEL,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, font=("Segoe UI", 8),
                     bg=PANEL, fg=TEXT, width=22, anchor="w", padx=6
                     ).pack(side="left")
            tk.Label(row, text=vf, font=("Segoe UI", 8, "bold"),
                     bg=PANEL, fg=TEXT, padx=4).pack(side="left")
            if dt:
                tk.Label(row, text=dt, font=("Segoe UI", 8),
                         bg=PANEL, fg=dc, padx=2).pack(side="left")

    def _build_right(self, parent: tk.Frame, win: tk.Toplevel) -> None:
        stats = self._economy.stats
        start = max(0, len(stats.steps) - 30)
        xs    = stats.steps[start:]

        fig = Figure(figsize=(6.0, 3.2), facecolor=CHART_BG)
        fig.subplots_adjust(hspace=0.65, wspace=0.42,
                            left=0.10, right=0.97, top=0.93, bottom=0.13)
        mini_panels = [
            (2, 3, 1, xs, stats.gdp[start:],           "GDP",          BLUE),
            (2, 3, 2, xs, stats.unemployment[start:],   "Unemployment", RED),
            (2, 3, 3, xs, stats.inflation[start:],      "Inflation",    ORANGE),
            (2, 3, 4, xs, stats.total_spending[start:], "Spending",     GREEN),
            (2, 3, 5, xs, stats.avg_wage[start:],       "Avg Wage",     TEAL),
            (2, 3, 6, xs, stats.gov_debt[start:],       "Gov Debt",     PURPLE),
        ]
        for r, c, pos, x, y, title, col in mini_panels:
            ax = fig.add_subplot(r, c, pos)
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values():
                sp.set_color(BORDER)
            ax.tick_params(colors=DIM, labelsize=6)
            if x and y:
                ax.plot(x, y, color=col, linewidth=1.4)
                ax.fill_between(x, y, alpha=0.10, color=col)
            ax.set_title(title, color=TEXT, fontsize=7, fontweight="bold", pad=3)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="x")
        canvas.draw()

        self._divider(parent, "WHAT HAPPENED THIS PERIOD")
        summary = self._write_summary()
        tk.Label(parent, text=summary, font=("Segoe UI", 9),
                 bg=BG, fg=TEXT, wraplength=620, justify="left"
                 ).pack(anchor="w", pady=(2, 6))

        self._divider(parent, "WHAT TO WATCH NEXT")
        for item in self._write_watches():
            r = tk.Frame(parent, bg=BG)
            r.pack(fill="x", pady=1, anchor="w")
            tk.Label(r, text="→", font=("Segoe UI", 9, "bold"),
                     bg=BG, fg=ACCENT).pack(side="left")
            tk.Label(r, text=item, font=("Segoe UI", 9),
                     bg=BG, fg=TEXT).pack(side="left", padx=6)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=10)
        tk.Button(parent, text="Close  &  Continue Simulation",
                  font=("Segoe UI", 11, "bold"),
                  bg=ACCENT, fg="white", activebackground="#1d4ed8",
                  relief="flat", padx=22, pady=9, cursor="hand2",
                  command=self._make_close(win)
                  ).pack()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _divider(self, parent: tk.Frame, title: str) -> None:
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(8, 3))
        tk.Label(parent, text=title, font=("Segoe UI", 8, "bold"),
                 bg=BG, fg=DIM).pack(anchor="w")

    def _make_close(self, win: tk.Toplevel):
        def _fn():
            win.grab_release()
            win.destroy()
            self._on_close()
        return _fn

    def _health_badge(self, m: dict, prev: dict | None) -> tuple[str, tuple]:
        gdp_pct = 0.0
        if prev:
            gdp_pct = (m["gdp"] - prev["gdp"]) / max(prev["gdp"], 1) * 100
        u = m["unemployment_rate"]
        if gdp_pct > 5 and u < 8:       badge = "BOOMING"
        elif gdp_pct >= 0 and u < 15:   badge = "GROWING"
        elif gdp_pct > -5 and u < 25:   badge = "STABLE"
        elif u > 35 or gdp_pct < -10:   badge = "CRISIS"
        else:                            badge = "STRUGGLING"
        return badge, self._BADGE_COLORS[badge]

    def _delta_text(self, key, m, prev, higher_better, is_dollar):
        if prev is None:
            return "", DIM
        diff = m.get(key, 0) - prev.get(key, 0)
        if abs(diff) < 1e-6:
            return "—", DIM
        went_up = diff > 0
        good = went_up if higher_better else not went_up
        col  = GREEN if good else RED
        sign = "+" if diff >= 0 else ""
        if is_dollar:
            return f"({sign}${abs(diff):,.0f})", col
        return f"({sign}{diff:.1f}%)", col

    def _write_summary(self) -> str:
        m    = self._milestones[-1]
        prev = self._milestones[-2] if len(self._milestones) >= 2 else None
        parts = []
        if prev:
            gdp_pct = (m["gdp"] - prev["gdp"]) / max(prev["gdp"], 1) * 100
            u, up   = m["unemployment_rate"], prev["unemployment_rate"]
            if gdp_pct > 8:
                parts.append(f"Exceptional growth: output surged {gdp_pct:.1f}% over the past 30 months, driven by strong consumer demand and business expansion.")
            elif gdp_pct > 2:
                parts.append(f"Steady expansion: total output rose {gdp_pct:.1f}% during this window.")
            elif gdp_pct > -2:
                parts.append(f"Output was broadly flat, changing only {gdp_pct:+.1f}% — the economy held its ground.")
            else:
                parts.append(f"The economy contracted {abs(gdp_pct):.1f}% — a recessionary period.")
            if u < up - 3:
                parts.append(f"Businesses hired aggressively, pulling unemployment from {up:.0f}% to {u:.0f}%.")
            elif u > up + 3:
                parts.append(f"Unemployment jumped from {up:.0f}% to {u:.0f}% as firms shed headcount.")
            else:
                parts.append(f"Employment was stable around {u:.0f}% unemployment.")
        else:
            parts.append(f"The simulation opened at {m['unemployment_rate']:.0f}% unemployment as the economy found its initial equilibrium.")
        infl = m["inflation"]
        if infl > 6:    parts.append(f"Inflation ran hot at {infl:.1f}%, squeezing real purchasing power.")
        elif infl > 1:  parts.append(f"Prices rose at a healthy {infl:.1f}% — within the normal range.")
        elif infl < -1: parts.append(f"Deflationary pressure ({infl:.1f}%) indicated weak aggregate demand.")
        else:           parts.append("Prices were essentially stable throughout the period.")
        return "  ".join(parts)

    def _write_watches(self) -> list[str]:
        m    = self._milestones[-1]
        prev = self._milestones[-2] if len(self._milestones) >= 2 else None
        out  = []
        u, infl = m["unemployment_rate"], m["inflation"]
        if u < 5:    out.append("Near full employment — expect wage pressure and potential inflation pick-up next period.")
        elif u > 20: out.append("High unemployment may suppress demand; watch for a deflationary spiral.")
        if infl > 5: out.append("Inflation above 5% — businesses may struggle to maintain margins without raising prices further.")
        elif infl < -1: out.append("Deflation risk — weak demand could trigger a wage-price downward spiral.")
        if prev:
            debt_delta = m.get("gov_debt", 0) - prev.get("gov_debt", 0)
            if debt_delta > 50_000:
                out.append("Government debt growing quickly — watch for fiscal drag on the economy.")
            if (m["gdp"] - prev["gdp"]) / max(prev["gdp"], 1) < -0.02:
                out.append("GDP contracted this period — monitor whether this becomes a sustained downturn.")
        if not out:
            out.append("Economy appears broadly healthy. Monitor for signs of overheating or a demand slowdown.")
        return out


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

class Dashboard:
    SHOCK_OPTIONS = {
        "Recession — demand collapses, layoffs surge":  "recession",
        "Boom — savings surge, spending rises":         "boom",
        "Inflation Spike — prices jump sharply":        "inflation_spike",
        "Stimulus — government cash transfer to all":   "stimulus",
    }
    SPEEDS = [("Slow", 600), ("Normal", 180), ("Fast", 45), ("Max", 5)]

    def __init__(self, root: tk.Tk) -> None:
        self.root         = root
        self.root.title("Economic Simulation World Engine")
        self.root.configure(bg=BG)
        self.root.minsize(1200, 720)

        self.economy: Economy | None = None
        self.running      = False
        self._after_id    = None
        self.speed_ms     = 180
        self.total_steps  = DEFAULT_CONFIG["simulation_steps"]
        self._milestones: list[dict] = []
        self._report_open = False

        self._build_ui()
        self._init_economy()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_titlebar()
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=BG, width=290)
        left.pack(side="left", fill="y", padx=(8, 4), pady=6)
        left.pack_propagate(False)
        self._build_left(left)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=6)
        self._build_right(right)

    def _build_titlebar(self) -> None:
        bar = tk.Frame(self.root, bg="#03070e", pady=10)
        bar.pack(fill="x")

        tk.Label(bar, text="◈  ECONOMIC SIMULATION WORLD ENGINE",
                 font=("Segoe UI", 12, "bold"), bg="#03070e", fg=BLUE
                 ).pack(side="left", padx=14)

        self._step_var = tk.StringVar(value="Month  0 / 120")
        tk.Label(bar, textvariable=self._step_var,
                 font=("Segoe UI", 10), bg="#03070e", fg=DIM
                 ).pack(side="left", padx=16)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Sim.Horizontal.TProgressbar",
                        troughcolor=PANEL, background=ACCENT, thickness=6)
        self._progress = ttk.Progressbar(bar, style="Sim.Horizontal.TProgressbar",
                                          maximum=self.total_steps,
                                          mode="determinate", length=260)
        self._progress.pack(side="left", padx=4)

        btns = tk.Frame(bar, bg="#03070e")
        btns.pack(side="right", padx=14)

        self._start_btn = tk.Button(
            btns, text="▶  Start", font=("Segoe UI", 10, "bold"),
            bg=GREEN, fg="#010409", activebackground="#0ea572",
            relief="flat", padx=14, pady=5, cursor="hand2",
            command=self._toggle_run)
        self._start_btn.pack(side="left", padx=4)

        tk.Button(btns, text="↺  Reset", font=("Segoe UI", 10),
                  bg=PANEL, fg=TEXT, activebackground=BORDER,
                  relief="flat", padx=12, pady=5, cursor="hand2",
                  command=self._reset
                  ).pack(side="left", padx=4)

    def _build_left(self, parent: tk.Frame) -> None:
        self._cards: dict[str, StatCard] = {}
        card_defs = [
            ("gdp",       "TOTAL OUTPUT (GDP)",
             "Total dollar value of all goods produced this month.", BLUE),
            ("unemp",     "UNEMPLOYMENT",
             "Share of workers without a job  (green < 6 %, red > 15 %).", RED),
            ("inflation", "INFLATION  (ann.)",
             "Annualised price-change rate  (healthy range: 0 – 3 %).", ORANGE),
            ("wage",      "AVERAGE WAGE",
             "What the typical employed worker earns per month.", GREEN),
            ("spending",  "CONSUMER SPENDING",
             "Dollars flowing from households into the market this month.", TEAL),
            ("savings",   "TOTAL WORKER SAVINGS",
             "Aggregate savings pool held across all workers.", PURPLE),
        ]
        for key, label, desc, col in card_defs:
            c = StatCard(parent, label, desc, spark_color=col)
            c.pack(fill="x", pady=2)
            self._cards[key] = c

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)

        tk.Label(parent, text="SIMULATION SPEED", font=("Segoe UI", 7, "bold"),
                 bg=BG, fg=DIM).pack(anchor="w")
        self._speed_var = tk.StringVar(value="Normal")
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=2)
        for lbl, ms in self.SPEEDS:
            tk.Radiobutton(row, text=lbl, variable=self._speed_var, value=lbl,
                           bg=BG, fg=TEXT, selectcolor=PANEL,
                           activebackground=BG, activeforeground=TEXT,
                           font=("Segoe UI", 9),
                           command=lambda m=ms: self._set_speed(m)
                           ).pack(side="left", padx=3)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)

        tk.Label(parent, text="INJECT ECONOMIC SHOCK",
                 font=("Segoe UI", 7, "bold"), bg=BG, fg=DIM).pack(anchor="w")
        self._shock_var = tk.StringVar(value=list(self.SHOCK_OPTIONS.keys())[0])
        om = tk.OptionMenu(parent, self._shock_var, *self.SHOCK_OPTIONS.keys())
        om.config(bg=PANEL, fg=TEXT, activebackground=BORDER, activeforeground=TEXT,
                  relief="flat", font=("Segoe UI", 8), highlightthickness=0,
                  anchor="w", width=34)
        om["menu"].config(bg=PANEL, fg=TEXT, activebackground=BORDER, font=("Segoe UI", 8))
        om.pack(fill="x", pady=2)

        tk.Button(parent, text="⚡  Apply Shock Now",
                  font=("Segoe UI", 9, "bold"), bg=RED, fg="white",
                  activebackground="#dc2626", relief="flat",
                  padx=10, pady=4, cursor="hand2",
                  command=self._apply_shock
                  ).pack(fill="x", pady=2)

    def _build_right(self, parent: tk.Frame) -> None:
        # ── 6-chart live grid ─────────────────────────────────────────────────
        chart_frame = tk.Frame(parent, bg=BG)
        chart_frame.pack(fill="both", expand=True)

        self._fig = Figure(figsize=(9, 5.5), facecolor=CHART_BG)
        self._fig.subplots_adjust(hspace=0.55, wspace=0.40,
                                   left=0.08, right=0.97,
                                   top=0.95, bottom=0.09)
        self._axes = {
            "gdp":      self._fig.add_subplot(2, 3, 1),
            "unemp":    self._fig.add_subplot(2, 3, 2),
            "inflation":self._fig.add_subplot(2, 3, 3),
            "spending": self._fig.add_subplot(2, 3, 4),
            "wages":    self._fig.add_subplot(2, 3, 5),
            "govfin":   self._fig.add_subplot(2, 3, 6),
        }
        self._style_axes()

        self._canvas = FigureCanvasTkAgg(self._fig, master=chart_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._draw_placeholders()

        # ── Bottom strip: AI analysis + event log ─────────────────────────────
        bottom = tk.Frame(parent, bg=BG, height=128)
        bottom.pack(fill="x", pady=(4, 0))
        bottom.pack_propagate(False)

        narr = tk.Frame(bottom, bg=PANEL,
                        highlightbackground=BORDER, highlightthickness=1)
        narr.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(narr, text="AI ANALYSIS", font=("Segoe UI", 7, "bold"),
                 bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(6, 0))
        self._narr_var = tk.StringVar(value="Press  ▶ Start  to begin the simulation.")
        tk.Label(narr, textvariable=self._narr_var,
                 font=("Segoe UI", 10), bg=PANEL, fg=TEXT,
                 wraplength=560, justify="left", pady=6, padx=10
                 ).pack(anchor="w")

        self._event_log = EventLog(bottom, width=300)
        self._event_log.pack(side="left", fill="y")

    def _style_axes(self) -> None:
        titles = {
            "gdp":      "Total Output (GDP)",
            "unemp":    "Unemployment %",
            "inflation":"Inflation % (ann.)",
            "spending": "Consumer Spending",
            "wages":    "Wages & Prices",
            "govfin":   "Government Finance",
        }
        for key, ax in self._axes.items():
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values():
                sp.set_color(BORDER)
            ax.tick_params(colors=DIM, labelsize=6)
            ax.set_title(titles[key], color=TEXT, fontsize=8,
                         fontweight="bold", pad=4)
            ax.set_xlabel("Month", color=DIM, fontsize=6)

    def _draw_placeholders(self) -> None:
        for ax in self._axes.values():
            ax.text(0.5, 0.5, "awaiting data…",
                    transform=ax.transAxes, ha="center", va="center",
                    color=DIM, fontsize=8)
        self._canvas.draw_idle()

    # ── Simulation control ────────────────────────────────────────────────────

    def _init_economy(self) -> None:
        random.seed()
        wage  = random.uniform(60, 180)
        config = {
            **DEFAULT_CONFIG,
            "num_workers":      random.randint(50, 200),
            "num_businesses":   random.randint(5, 20),
            "initial_wage":     wage,
            "initial_price":    wage * random.uniform(0.14, 0.28),
            "tax_rate":         random.uniform(0.10, 0.38),
            "unemployment_benefit_rate": random.uniform(0.20, 0.45),
            "investment_rate":  random.uniform(0.01, 0.05),
            "hiring_profit_threshold": random.uniform(0.01, 0.06),
        }
        self.economy   = Economy(config)
        self._milestones = []
        self._update_display()

    def _reset(self) -> None:
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.running      = False
        self._report_open = False
        self._start_btn.config(text="▶  Start", bg=GREEN, fg="#010409", state="normal")
        self._narr_var.set("Press  ▶ Start  to begin the simulation.")
        self._progress["value"] = 0
        self._step_var.set("Month  0 / 120")
        for ax in self._axes.values():
            ax.clear()
        self._style_axes()
        self._draw_placeholders()
        self._event_log.clear()
        self._init_economy()

    def _toggle_run(self) -> None:
        if self.running:
            self.running = False
            if self._after_id:
                self.root.after_cancel(self._after_id)
                self._after_id = None
            self._start_btn.config(text="▶  Resume", bg=GREEN, fg="#010409")
        else:
            if self.economy.time_step >= self.total_steps:
                return
            self.running = True
            self._start_btn.config(text="⏸  Pause", bg=YELLOW, fg="#010409")
            self._tick()

    def _tick(self) -> None:
        if not self.running or self._report_open:
            return
        self.economy.step()
        self._update_display()
        if self.economy.time_step >= self.total_steps:
            self.running = False
            self._start_btn.config(text="✓  Finished", bg=PANEL, fg=DIM,
                                    state="disabled")
            self._narr_var.set(
                f"Simulation complete after {self.total_steps} months.  "
                f"Final GDP: ${self.economy.stats.gdp[-1]:,.0f}.  "
                "Press  ↺ Reset  to run again."
            )
            return
        self._after_id = self.root.after(self.speed_ms, self._tick)

    def _set_speed(self, ms: int) -> None:
        self.speed_ms = ms

    def _apply_shock(self) -> None:
        if not self.economy:
            return
        label = self._shock_var.get()
        key   = self.SHOCK_OPTIONS.get(label, "recession")
        self.economy.apply_shock(key)
        step  = self.economy.time_step
        short = label.split("—")[0].strip()
        self._narr_var.set(f"SHOCK APPLIED at month {step}:  {label}")
        self._event_log.add(step, short, "shock")

    # ── Display refresh ───────────────────────────────────────────────────────

    def _update_display(self) -> None:
        if not self.economy:
            return
        m    = self.economy.get_metrics()
        step = m["step"]

        self._step_var.set(f"Month  {step} / {self.total_steps}")
        self._progress["value"] = step

        u    = m["unemployment_rate"]
        infl = m["inflation"]
        uc   = GREEN if u < 6 else (YELLOW if u < 15 else RED)
        ic   = RED if infl < -2 else (GREEN if infl < 4 else (YELLOW if infl < 8 else RED))

        self._cards["gdp"].update(f"${m['gdp']:>10,.0f}",        m["gdp"])
        self._cards["unemp"].update(f"{u:.1f}%",                 u,       uc)
        self._cards["inflation"].update(f"{infl:.1f}%",          infl,    ic)
        self._cards["wage"].update(f"${m['avg_wage']:.2f}",      m["avg_wage"])
        self._cards["spending"].update(f"${m['total_spending']:>10,.0f}", m["total_spending"])
        self._cards["savings"].update(f"${m['total_savings']:>10,.0f}",  m["total_savings"])

        if step > 0:
            self._narr_var.set(self._narrate(m))
            self._log_events(step, m)
            self._check_milestone(step, m)

        self._update_charts()

    def _narrate(self, m: dict) -> str:
        u, infl = m["unemployment_rate"], m["inflation"]
        sent    = m.get("consumer_sentiment", 1.0)
        stats   = self.economy.stats
        growing = len(stats.gdp) >= 4 and stats.gdp[-1] > stats.gdp[-4]

        trend = "Growing ▲" if growing else "Contracting ▼"
        job   = ("near full employment" if u < 3 else
                 f"low unemployment {u:.0f}%" if u < 8 else
                 f"{u:.0f}% unemployed — firms cautious" if u < 20 else
                 f"high unemployment {u:.0f}%")
        price = ("prices rising sharply" if infl > 6 else
                 "prices rising gently" if infl > 1 else
                 "prices stable" if infl > -1 else
                 "prices falling — deflation risk")
        mood  = ("confidence high, spending freely" if sent >= 1.2 else
                 "consumer mood positive" if sent >= 1.0 else
                 "households cautious, saving more" if sent >= 0.8 else
                 "low confidence — spending suppressed")

        return f"{trend}  ·  {job}  ·  {price}  ·  {mood}"

    def _log_events(self, step: int, m: dict) -> None:
        if step % 6 != 0:
            return
        stats = self.economy.stats
        if len(stats.gdp) >= 7:
            pct = (stats.gdp[-1] - stats.gdp[-7]) / max(stats.gdp[-7], 1) * 100
            if pct > 12:
                self._event_log.add(step, f"GDP surged +{pct:.0f}% in 6 months", "good")
            elif pct < -8:
                self._event_log.add(step, f"GDP fell {pct:.0f}% in 6 months", "bad")
        if len(stats.unemployment) >= 7:
            du = stats.unemployment[-1] - stats.unemployment[-7]
            if du > 5:
                self._event_log.add(step, f"Mass layoffs — unemp +{du:.0f}pp", "bad")
            elif du < -5:
                self._event_log.add(step, f"Hiring surge — unemp {du:.0f}pp", "good")
        infl = m["inflation"]
        if infl > 8:
            self._event_log.add(step, f"High inflation: {infl:.1f}%", "bad")
        elif infl < -2:
            self._event_log.add(step, f"Deflation: {infl:.1f}%", "bad")

    def _check_milestone(self, step: int, m: dict) -> None:
        if step % 30 != 0:
            return
        self._milestones.append(m.copy())
        self._event_log.add(step, f"Month {step} report generated", "report")

        was_running  = self.running
        self.running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._report_open = True
        self._start_btn.config(text="▶  Resume", bg=GREEN, fg="#010409")

        def on_close():
            self._report_open = False
            if was_running and self.economy.time_step < self.total_steps:
                self.running = True
                self._start_btn.config(text="⏸  Pause", bg=YELLOW, fg="#010409")
                self._tick()

        ReportWindow(self.root, step, self.economy, self._milestones, on_close)

    # ── Chart refresh ─────────────────────────────────────────────────────────

    def _update_charts(self) -> None:
        s  = self.economy.stats
        xs = s.steps
        if not xs:
            return

        def _draw(key, ys, title, color, fill=True, hline=None):
            ax = self._axes[key]
            ax.clear()
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values():
                sp.set_color(BORDER)
            ax.tick_params(colors=DIM, labelsize=6)
            ax.plot(xs, ys, color=color, linewidth=1.6)
            if fill and len(xs) >= 2:
                ax.fill_between(xs, ys, alpha=0.12, color=color)
            if hline is not None:
                ax.axhline(y=hline, color=DIM, linewidth=0.7,
                           linestyle="--", alpha=0.6)
            ax.set_title(title, color=TEXT, fontsize=8, fontweight="bold", pad=4)
            ax.set_xlabel("Month", color=DIM, fontsize=6)

        _draw("gdp",       s.gdp,          "Total Output (GDP)",   BLUE)
        _draw("unemp",     s.unemployment, "Unemployment %",       RED)
        _draw("inflation", s.inflation,    "Inflation % (ann.)",   ORANGE, fill=False, hline=0.0)
        _draw("spending",  s.total_spending,"Consumer Spending",   GREEN)

        ax = self._axes["wages"]
        ax.clear()
        ax.set_facecolor(PANEL)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        ax.tick_params(colors=DIM, labelsize=6)
        ax.plot(xs, s.avg_wage,  color=GREEN,  linewidth=1.6, label="Wage")
        ax.plot(xs, s.avg_price, color=ORANGE, linewidth=1.6, label="Price")
        if len(xs) >= 2:
            ax.fill_between(xs, s.avg_wage,  alpha=0.08, color=GREEN)
            ax.fill_between(xs, s.avg_price, alpha=0.08, color=ORANGE)
        ax.set_title("Wages & Prices", color=TEXT, fontsize=8, fontweight="bold", pad=4)
        ax.set_xlabel("Month", color=DIM, fontsize=6)
        ax.legend(fontsize=6, framealpha=0.2, facecolor=PANEL, labelcolor=TEXT, loc="upper left")

        ax = self._axes["govfin"]
        ax.clear()
        ax.set_facecolor(PANEL)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        ax.tick_params(colors=DIM, labelsize=6)
        ax.plot(xs, s.tax_revenue, color=TEAL,   linewidth=1.6, label="Tax Revenue")
        ax.plot(xs, s.gov_debt,    color=PURPLE,  linewidth=1.4, linestyle="--", label="Gov Debt")
        ax.set_title("Government Finance", color=TEXT, fontsize=8, fontweight="bold", pad=4)
        ax.set_xlabel("Month", color=DIM, fontsize=6)
        ax.legend(fontsize=6, framealpha=0.2, facecolor=PANEL, labelcolor=TEXT, loc="upper left")

        self._canvas.draw_idle()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    root = tk.Tk()
    root.geometry("1440x860")
    Dashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
