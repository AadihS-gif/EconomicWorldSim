"""agents.py — Worker and Business agents for the Economic Simulation World Engine."""

import random


class Worker:
    """A wage-earning, spending, saving household agent."""

    def __init__(self, worker_id: int, initial_wage: float = 100.0,
                 initial_savings: float | None = None):
        self.id = worker_id
        self.wage = initial_wage
        self.employer: "Business | None" = None
        self.is_employed = False
        self.spending = 0.0
        self.income = 0.0
        # Individual marginal propensity to consume — normally distributed
        self.mpc = max(0.50, min(0.95, random.gauss(0.85, 0.04)))
        self.savings = (initial_savings if initial_savings is not None
                        else initial_wage * random.uniform(2.0, 6.0))

    # ------------------------------------------------------------------
    # Income & spending
    # ------------------------------------------------------------------

    def receive_income(self, net_amount: float) -> None:
        """Credit income to savings pool; track this period's income."""
        self.income = net_amount
        self.savings += net_amount

    def decide_spending(self, sentiment: float = 1.0) -> float:
        """
        Return dollar amount spent this period; deduct from savings.
        sentiment > 1.0 means workers are confident and spend more;
        sentiment < 1.0 means workers are nervous and save more.
        """
        # Additive nudge: sentiment shifts MPC by at most ±8 pp, not multiply.
        # This prevents sentiment from collapsing spending catastrophically.
        adjustment = (sentiment - 1.0) * 0.08
        effective_mpc = max(0.40, min(0.95, self.mpc + adjustment))
        if self.is_employed:
            target = effective_mpc * self.income
        else:
            # Unemployed: spend benefit income at sentiment-adjusted rate
            target = effective_mpc * self.income + 0.01 * self.savings

        actual = max(0.0, min(target, self.savings))
        self.spending = actual
        self.savings -= actual
        return actual

    # ------------------------------------------------------------------
    # Labour market
    # ------------------------------------------------------------------

    def get_hired(self, employer: "Business", wage: float) -> None:
        self.employer = employer
        self.is_employed = True
        self.wage = wage

    def get_fired(self) -> None:
        self.employer = None
        self.is_employed = False

    @property
    def net_worth(self) -> float:
        return self.savings


# ======================================================================


class Business:
    """A firm that hires workers, produces goods, sets prices, seeks profit."""

    # Industry-specific traits: price sensitivity and production rate
    _TRAITS: dict[str, dict] = {
        "food":     {"price_sensitivity": 0.08, "production_rate": 6.0},
        "tech":     {"price_sensitivity": 0.13, "production_rate": 4.0},
        "housing":  {"price_sensitivity": 0.05, "production_rate": 3.0},
        "services": {"price_sensitivity": 0.10, "production_rate": 5.0},
    }

    def __init__(self, business_id: int, industry: str = "services",
                 initial_price: float = 22.0):
        self.id = business_id
        self.industry = industry
        traits = self._TRAITS.get(industry, self._TRAITS["services"])

        self.price = initial_price * random.uniform(0.85, 1.15)
        self.price_sensitivity = traits["price_sensitivity"] * random.uniform(0.8, 1.2)
        self.production_per_worker = traits["production_rate"] * random.uniform(0.9, 1.1)

        self.workers: list[Worker] = []
        self.base_wage = 100.0          # reference wage for new hires / floor
        self.inventory = 0.0
        self.units_produced = 0.0
        self.units_sold = 0.0
        self.revenue = 0.0
        self.wage_costs = 0.0
        self.profit = 0.0
        self.profit_margin = 0.0
        self.consecutive_losses = 0
        self.sales_history: list[float] = []         # units sold, last 12 periods
        self.demand_ratio_history: list[float] = []  # demand/supply ratio, last 6 periods

    # ------------------------------------------------------------------
    # Production
    # ------------------------------------------------------------------

    def produce(self) -> None:
        capacity = len(self.workers) * self.production_per_worker
        if len(self.sales_history) >= 3:
            # Produce based on recent sales trend rather than raw capacity.
            # If sales are growing, ramp up; if falling, pull back.
            recent = sum(self.sales_history[-3:]) / 3
            if len(self.sales_history) >= 6:
                older = sum(self.sales_history[-6:-3]) / 3
                trend = (recent - older) / max(older, 1e-9)
            else:
                trend = 0.0
            target = recent * (1.0 + trend * 0.5 + 0.08)   # trend + 8% safety stock
            self.units_produced = min(capacity, max(target, 0.0))
        else:
            self.units_produced = capacity * 0.80   # conservative before history exists

        self.inventory += self.units_produced
        cap = max(self.units_produced * 3.0, 10.0)
        if self.inventory > cap:
            self.inventory = cap

    # ------------------------------------------------------------------
    # Sales
    # ------------------------------------------------------------------

    def sell(self, units_demanded: float) -> None:
        units_to_sell = min(units_demanded, self.inventory)
        self.units_sold = units_to_sell
        self.revenue = units_to_sell * self.price
        self.inventory = max(0.0, self.inventory - units_to_sell)
        self.sales_history.append(self.units_sold)
        if len(self.sales_history) > 12:
            self.sales_history.pop(0)

    # ------------------------------------------------------------------
    # Financials
    # ------------------------------------------------------------------

    def pay_wages(self) -> None:
        self.wage_costs = sum(w.wage for w in self.workers)

    def calculate_profit(self) -> None:
        self.profit = self.revenue - self.wage_costs
        denom = max(self.wage_costs, 1.0)
        self.profit_margin = self.profit / denom
        if self.profit < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    # ------------------------------------------------------------------
    # Dynamic adjustments
    # ------------------------------------------------------------------

    def adjust_price(self, demand_ratio: float) -> None:
        """
        Adjust price using a smoothed demand/supply ratio (rolling 6-period average).
        Smoothing prevents overreaction to single-period noise.
        """
        self.demand_ratio_history.append(demand_ratio)
        if len(self.demand_ratio_history) > 6:
            self.demand_ratio_history.pop(0)
        smoothed = sum(self.demand_ratio_history) / len(self.demand_ratio_history)

        if smoothed > 1.05:
            self.price *= 1 + self.price_sensitivity * (smoothed - 1.0)
        elif smoothed < 0.95:
            self.price *= 1 - self.price_sensitivity * (1.0 - smoothed)

        # Floor: don't price below ~70 % of marginal cost
        if self.units_produced > 0:
            cost_per_unit = max(self.wage_costs / self.units_produced, 0.0)
            floor = cost_per_unit * 0.70
        else:
            floor = 0.50
        self.price = max(self.price, floor, 0.10)

    def adjust_wages(self) -> None:
        """Nudge wages up when profitable; trim slightly when losing money."""
        if self.profit_margin > 0.15 and self.workers:
            for w in self.workers:
                w.wage *= 1.005
            self.base_wage *= 1.005
        elif self.profit_margin < -0.10 and self.workers:
            for w in self.workers:
                w.wage = max(w.wage * 0.995, self.base_wage * 0.70)

    # ------------------------------------------------------------------
    # Labour market
    # ------------------------------------------------------------------

    def hire(self, worker: Worker) -> None:
        worker.get_hired(self, self.base_wage)
        self.workers.append(worker)

    def fire(self) -> None:
        if self.workers:
            victim = self.workers.pop(random.randrange(len(self.workers)))
            victim.get_fired()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def num_workers(self) -> int:
        return len(self.workers)

    @property
    def total_output_value(self) -> float:
        return self.units_produced * self.price
