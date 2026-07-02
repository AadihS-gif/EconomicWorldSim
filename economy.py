"""economy.py — Core orchestration: Economy and Government classes."""

import random

from agents import Worker, Business
from market import Market
from stats import Statistics

# ──────────────────────────────────────────────────────────────────────
# Default configuration
# ──────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG: dict = {
    # Agents
    "num_workers": 100,
    "num_businesses": 10,
    # Prices / wages
    "initial_wage": 100.0,
    "initial_price": 22.0,
    # Government
    "tax_rate": 0.20,
    "unemployment_benefit_rate": 0.30,   # fraction of avg wage paid as benefit
    # Investment: fraction of total worker savings injected as market demand each step.
    # Represents household investment (mutual funds, equity, etc.) closing the
    # savings-leakage gap so the circular flow stays balanced.
    "investment_rate": 0.025,
    # Labour market thresholds
    "hiring_profit_threshold": 0.02,     # profit margin that triggers hiring
    "fire_after_n_losses": 8,            # consecutive loss periods before firing
    # Simulation
    "simulation_steps": 120,
    # seed=None means a different random run every time.
    # Set to an integer (e.g. 42) to reproduce a specific run exactly.
    "seed": None,
}


# ======================================================================
# Government
# ======================================================================

class Government:
    """Collects income taxes, pays unemployment benefits, and acts as an
    automatic stabiliser by adjusting the tax rate to the business cycle."""

    def __init__(self, tax_rate: float = 0.20, benefit_rate: float = 0.30) -> None:
        self.tax_rate = tax_rate
        self.benefit_rate = benefit_rate
        self.tax_revenue = 0.0
        self.benefit_spending = 0.0
        self.cumulative_debt = 0.0

    def collect_taxes(self, workers: list[Worker]) -> None:
        self.tax_revenue = sum(
            w.wage * self.tax_rate for w in workers if w.is_employed
        )

    def pay_workers(self, workers: list[Worker]) -> None:
        """Credit each employed worker with their after-tax wage."""
        for w in workers:
            if w.is_employed:
                w.receive_income(w.wage * (1.0 - self.tax_rate))

    def pay_benefits(self, workers: list[Worker], avg_wage: float) -> float:
        """Pay a flat unemployment benefit; track fiscal deficit."""
        benefit = avg_wage * self.benefit_rate
        unemployed = [w for w in workers if not w.is_employed]
        self.benefit_spending = len(unemployed) * benefit
        for w in unemployed:
            w.receive_income(benefit)
        self.cumulative_debt += max(0.0, self.benefit_spending - self.tax_revenue)
        return benefit

    def adjust_tax_rate(self, unemployment_rate: float) -> None:
        """Automatic stabiliser: ease taxes in a slump, raise in a boom."""
        if unemployment_rate > 15.0:
            self.tax_rate = max(0.10, self.tax_rate - 0.005)
        elif unemployment_rate < 5.0:
            self.tax_rate = min(0.35, self.tax_rate + 0.002)

    def apply_stimulus(self, workers: list[Worker], amount_per_worker: float) -> None:
        """Emergency one-off transfer to all workers."""
        for w in workers:
            w.savings += amount_per_worker
        self.cumulative_debt += amount_per_worker * len(workers)


# ======================================================================
# Economy
# ======================================================================

class Economy:
    """
    Top-level simulation object.  Each call to `step()` advances the
    economy by one discrete time period (think: one month).

    Simulation sequence per step
    ─────────────────────────────
    1.  Businesses produce goods.
    2.  Market computes weighted-average price.
    3.  Government collects taxes → pays net wages → pays benefits.
    4.  Market aggregates supply; workers decide spending (demand).
    5.  Market clears (goods trade hands).
    6.  Businesses compute revenue, wage costs, and profit.
    7.  Market adjusts prices based on demand/supply ratio.
    8.  Businesses nudge wages up/down based on margins.
    9.  Labour market: profitable firms hire; loss-making firms fire.
    10. Statistics recorded.
    """

    _INDUSTRIES = ["food", "tech", "housing", "services"]

    def __init__(self, config: dict | None = None) -> None:
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.time_step = 0
        self.workers: list[Worker] = []
        self.businesses: list[Business] = []
        self.market = Market()
        self.government = Government(
            tax_rate=self.config["tax_rate"],
            benefit_rate=self.config["unemployment_benefit_rate"],
        )
        self.stats = Statistics()
        self._setup()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _setup(self) -> None:
        n_w = self.config["num_workers"]
        n_b = self.config["num_businesses"]
        wage = self.config["initial_wage"]
        price = self.config["initial_price"]

        for i in range(n_b):
            industry = self._INDUSTRIES[i % len(self._INDUSTRIES)]
            b = Business(business_id=i, industry=industry, initial_price=price)
            b.base_wage = wage
            self.businesses.append(b)

        for i in range(n_w):
            w = Worker(
                worker_id=i,
                initial_wage=wage * random.uniform(0.85, 1.15),
                initial_savings=wage * random.uniform(2.0, 6.0),
            )
            self.workers.append(w)

            # Start with ~80 % employment so businesses are profitable from step 1
            # and the economy has a clear upward growth signal.
            if i < int(n_w * 0.80):
                self.businesses[i % n_b].hire(w)

        # Prime initial inventory so the market has something to clear on step 1
        for b in self.businesses:
            b.produce()

        self.market.compute_average_price(self.businesses)

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> None:
        self.time_step += 1

        # 1. Production
        for b in self.businesses:
            b.produce()

        # 2. Price reference for demand conversion
        self.market.compute_average_price(self.businesses)

        # 3. Fiscal flows
        self.government.collect_taxes(self.workers)
        self.government.pay_workers(self.workers)
        self.government.pay_benefits(self.workers, self._avg_wage())
        self.government.adjust_tax_rate(self._unemployment_rate())

        # 4. Aggregate supply & demand
        #    Sentiment adjusts how freely workers spend based on recent trends.
        self.market.aggregate_supply(self.businesses)
        sentiment = self._consumer_sentiment()
        self.market.collect_demand(self.workers, sentiment)

        # 4b. Inject government spending + worker investment to close savings leakage
        self._inject_additional_demand()

        # 5. Market clearing
        self.market.clear(self.businesses)

        # 6. Business financials
        for b in self.businesses:
            b.pay_wages()
            b.calculate_profit()

        # 7. Price adjustment
        self.market.adjust_prices(self.businesses)
        self.market.compute_average_price(self.businesses)

        # 8. Wage dynamics
        for b in self.businesses:
            b.adjust_wages()

        # 8b. Productivity growth — tiny monthly efficiency gain (technological progress)
        for b in self.businesses:
            b.production_per_worker *= 1.0002   # ~0.24 % per year

        # 9. Labour market
        self._labour_market()

        # 10. Record metrics
        self.stats.record(self)

    # ------------------------------------------------------------------
    # Consumer sentiment  (trend-awareness for households)
    # ------------------------------------------------------------------

    def _consumer_sentiment(self) -> float:
        """
        Composite confidence index in range [0.5, 1.5].
        Scales each worker's effective MPC this period.

        Sources of optimism (+):  GDP growing, unemployment falling
        Sources of pessimism (−): GDP shrinking, unemployment rising,
                                  high inflation (real income squeezed),
                                  deflation (fear of worse times ahead)
        """
        stats = self.stats
        sentiment = 1.0

        # GDP trend: recent 6 steps vs prior 6 steps
        if len(stats.gdp) >= 12:
            recent_avg = sum(stats.gdp[-6:]) / 6
            prior_avg  = sum(stats.gdp[-12:-6]) / 6
            gdp_trend  = (recent_avg - prior_avg) / max(prior_avg, 1.0)
            sentiment += gdp_trend * 0.8        # dampened: was 1.5

        # Unemployment trajectory: rising = households get nervous
        if len(stats.unemployment) >= 6:
            u_delta = stats.unemployment[-1] - stats.unemployment[-6]
            sentiment -= u_delta * 0.02         # dampened: was 0.04

        # Inflation: high inflation erodes real income
        if stats.inflation:
            infl = stats.inflation[-1]
            if infl > 4:
                sentiment -= (infl - 4) * 0.015
            elif infl < -2:
                sentiment -= abs(infl + 2) * 0.010

        return max(0.5, min(1.5, sentiment))

    # ------------------------------------------------------------------
    # Demand injection — closes the Keynesian savings-leakage gap
    # ------------------------------------------------------------------

    def _inject_additional_demand(self) -> None:
        """
        Two real-world flows that the simple spending model omits:

        1. Government spending — the government recycles its tax revenue
           by purchasing goods and services from businesses.
        2. Investment demand — households channel a fraction of their
           savings back into the economy through equity / capital markets.
           This models I = S so the circular flow stays closed.

        Both are added to the market's running demand totals after
        consumer spending has already been collected.
        """
        price = max(self.market.average_price, 0.01)

        # 1. Government recycles 100 % of tax revenue as purchases
        gov_dollars = self.government.tax_revenue

        # 2. Workers invest a fraction of savings; deduct it from their balances
        invest_rate = self.config.get("investment_rate", 0.025)
        total_savings = sum(w.savings for w in self.workers)
        invest_dollars = total_savings * invest_rate
        if total_savings > 0:
            for w in self.workers:
                deduction = w.savings * invest_rate
                w.savings = max(0.0, w.savings - deduction)

        extra_dollars = gov_dollars + invest_dollars
        self.market.total_spending += extra_dollars
        self.market.total_demand_units += extra_dollars / price

    # ------------------------------------------------------------------
    # Labour market
    # ------------------------------------------------------------------

    def _labour_market(self) -> None:
        unemployed = [w for w in self.workers if not w.is_employed]
        random.shuffle(unemployed)

        supply = max(self.market.total_supply_units, 1e-9)
        demand_ratio = self.market.total_demand_units / supply

        for b in self.businesses:
            # Dead business restarts when market is tight
            if b.num_workers == 0 and demand_ratio > 1.05 and unemployed:
                b.hire(unemployed.pop())
                continue

            # Anticipatory hiring: if sales have grown three periods in a row,
            # hire now rather than waiting for profits to peak.
            sales_trending_up = (
                len(b.sales_history) >= 6 and
                sum(b.sales_history[-3:]) / 3 > sum(b.sales_history[-6:-3]) / 3
            )
            should_hire = (
                b.profit_margin > self.config["hiring_profit_threshold"] or
                (sales_trending_up and b.profit_margin > 0)
            )

            if should_hire and unemployed:
                b.hire(unemployed.pop())
            elif b.consecutive_losses >= self.config["fire_after_n_losses"]:
                b.fire()

    # ------------------------------------------------------------------
    # Economic shocks
    # ------------------------------------------------------------------

    def apply_shock(self, shock_type: str, magnitude: float = 0.5) -> None:
        """
        Inject a one-off structural shock.

        shock_type options
        ──────────────────
        recession       — demand collapse + sudden layoffs
        boom            — savings surge + heightened propensity to consume
        inflation_spike — cost-push price jump across all businesses
        stimulus        — government transfer payment to all workers
        """
        shock_type = shock_type.lower()

        if shock_type == "recession":
            for w in self.workers:
                w.mpc = max(0.30, w.mpc * (1 - 0.30 * magnitude))
            n_victims = max(1, len(self.businesses) // 3)
            for b in random.sample(self.businesses, k=n_victims):
                n_fire = max(1, b.num_workers // 3)
                for _ in range(n_fire):
                    b.fire()

        elif shock_type == "boom":
            for w in self.workers:
                w.savings *= (1 + 0.50 * magnitude)
                w.mpc = min(0.95, w.mpc * (1 + 0.10 * magnitude))

        elif shock_type == "inflation_spike":
            for b in self.businesses:
                b.price *= (1 + 0.30 * magnitude)

        elif shock_type == "stimulus":
            amount = self.config["initial_wage"] * magnitude
            self.government.apply_stimulus(self.workers, amount)

        else:
            raise ValueError(f"Unknown shock type: {shock_type!r}")

    # ------------------------------------------------------------------
    # Helpers & metrics
    # ------------------------------------------------------------------

    def _avg_wage(self) -> float:
        employed = [w for w in self.workers if w.is_employed]
        return sum(w.wage for w in employed) / len(employed) if employed else 0.0

    def _unemployment_rate(self) -> float:
        if not self.workers:
            return 0.0
        return sum(1 for w in self.workers if not w.is_employed) / len(self.workers) * 100.0

    def get_metrics(self) -> dict:
        return {
            "step":               self.time_step,
            "gdp":                sum(b.revenue for b in self.businesses),
            "avg_price":          self.market.average_price,
            "avg_wage":           self._avg_wage(),
            "unemployment_rate":  self._unemployment_rate(),
            "total_spending":     self.market.total_spending,
            "inflation":          self.market.get_inflation(),
            "tax_revenue":        self.government.tax_revenue,
            "gov_debt":           self.government.cumulative_debt,
            "total_savings":      sum(w.savings for w in self.workers),
            "total_output":       sum(b.total_output_value for b in self.businesses),
            "consumer_sentiment": self._consumer_sentiment(),
        }
