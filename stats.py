"""stats.py — Metric tracking and matplotlib visualisation."""

from __future__ import annotations


class Statistics:
    """Records per-step economy metrics and generates charts."""

    def __init__(self) -> None:
        self.steps:          list[int]   = []
        self.gdp:            list[float] = []
        self.inflation:      list[float] = []
        self.unemployment:   list[float] = []
        self.avg_price:      list[float] = []
        self.avg_wage:       list[float] = []
        self.total_spending: list[float] = []
        self.tax_revenue:    list[float] = []
        self.gov_debt:       list[float] = []
        self.total_savings:  list[float] = []

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(self, economy) -> None:
        m = economy.get_metrics()
        self.steps.append(m["step"])
        self.gdp.append(m["gdp"])
        self.inflation.append(m["inflation"])
        self.unemployment.append(m["unemployment_rate"])
        self.avg_price.append(m["avg_price"])
        self.avg_wage.append(m["avg_wage"])
        self.total_spending.append(m["total_spending"])
        self.tax_revenue.append(m["tax_revenue"])
        self.gov_debt.append(m["gov_debt"])
        self.total_savings.append(m["total_savings"])

    # ------------------------------------------------------------------
    # Console output
    # ------------------------------------------------------------------

    def print_summary(self, step: int) -> None:
        if not self.gdp:
            return
        bar = "=" * 58
        print(f"\n{bar}")
        print(f"  ECONOMIC REPORT — Step {step:>4d}")
        print(bar)
        print(f"  GDP               : ${self.gdp[-1]:>14,.2f}")
        print(f"  Avg Market Price  : ${self.avg_price[-1]:>14.4f}")
        print(f"  Avg Wage          : ${self.avg_wage[-1]:>14.2f}")
        print(f"  Unemployment      : {self.unemployment[-1]:>13.2f}%")
        print(f"  Inflation (ann.)  : {self.inflation[-1]:>13.2f}%")
        print(f"  Consumer Spending : ${self.total_spending[-1]:>14,.2f}")
        print(f"  Tax Revenue       : ${self.tax_revenue[-1]:>14,.2f}")
        print(f"  Gov. Debt (cum.)  : ${self.gov_debt[-1]:>14,.2f}")
        print(f"  Worker Savings    : ${self.total_savings[-1]:>14,.2f}")
        print(bar)

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    def generate_plots(self, save_path: str = "economic_simulation.png",
                       show: bool = True) -> None:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        fig = plt.figure(figsize=(18, 12))
        fig.suptitle(
            "Economic Simulation World Engine — Results",
            fontsize=16, fontweight="bold", y=0.98,
        )
        gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.52, wspace=0.38)

        # (gridspec cell, x data, y data, title, xlabel, ylabel, colour, fill?)
        panels = [
            (gs[0, :2], self.steps, self.gdp,           "GDP Over Time",             "Step", "GDP ($)",      "steelblue",   True),
            (gs[0,  2], self.steps, self.unemployment,   "Unemployment Rate",         "Step", "Rate (%)",     "crimson",     True),
            (gs[1,  0], self.steps, self.inflation,      "Inflation Rate (ann. %)",   "Step", "Rate (%)",     "darkorange",  False),
            (gs[1,  1], self.steps, self.avg_price,      "Average Price Level",       "Step", "Price ($)",    "purple",      False),
            (gs[1,  2], self.steps, self.avg_wage,       "Average Wage",              "Step", "Wage ($)",     "forestgreen", False),
            (gs[2,  0], self.steps, self.total_spending, "Consumer Spending",         "Step", "Spending ($)", "teal",        True),
            (gs[2,  1], self.steps, self.total_savings,  "Total Worker Savings",      "Step", "Savings ($)",  "goldenrod",   True),
        ]

        for spec, xs, ys, title, xlabel, ylabel, color, fill in panels:
            ax = fig.add_subplot(spec)
            ax.plot(xs, ys, color=color, linewidth=2)
            ax.set_title(title, fontsize=10, fontweight="bold")
            ax.set_xlabel(xlabel, fontsize=8)
            ax.set_ylabel(ylabel, fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(True, alpha=0.30)
            if fill:
                ax.fill_between(xs, ys, alpha=0.12, color=color)
            if "Inflation" in title:
                ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)

        # Government finance — dual-line panel
        ax_gov = fig.add_subplot(gs[2, 2])
        ax_gov.plot(self.steps, self.tax_revenue, color="navy",
                    linewidth=2, label="Tax Revenue")
        ax_gov.plot(self.steps, self.gov_debt, color="red",
                    linewidth=1.5, linestyle="--", label="Cumul. Debt")
        ax_gov.set_title("Government Finance", fontsize=10, fontweight="bold")
        ax_gov.set_xlabel("Step", fontsize=8)
        ax_gov.set_ylabel("Amount ($)", fontsize=8)
        ax_gov.tick_params(labelsize=7)
        ax_gov.legend(fontsize=8)
        ax_gov.grid(True, alpha=0.30)

        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"\nChart saved -> {save_path}")
        if show:
            plt.show()
