"""market.py — Pricing, supply/demand aggregation, and market-clearing logic."""


class Market:
    """
    Central market that aggregates worker demand and business supply,
    clears trades, and drives price adjustments.
    """

    def __init__(self) -> None:
        self.total_demand_units = 0.0
        self.total_supply_units = 0.0
        self.total_spending = 0.0        # dollar value of consumer spending
        self.average_price = 0.0
        self._price_history: list[float] = []

    # ------------------------------------------------------------------
    # Price computation
    # ------------------------------------------------------------------

    def compute_average_price(self, businesses) -> float:
        """Production-weighted average price across all businesses."""
        if not businesses:
            self.average_price = 1.0
            return self.average_price

        total_units = sum(b.units_produced for b in businesses)
        if total_units > 0:
            self.average_price = (
                sum(b.price * b.units_produced for b in businesses) / total_units
            )
        else:
            self.average_price = sum(b.price for b in businesses) / len(businesses)
        return self.average_price

    # ------------------------------------------------------------------
    # Demand & supply aggregation
    # ------------------------------------------------------------------

    def aggregate_supply(self, businesses) -> float:
        """Sum current inventory across all businesses."""
        self.total_supply_units = sum(b.inventory for b in businesses)
        return self.total_supply_units

    def collect_demand(self, workers, sentiment: float = 1.0) -> float:
        """
        Ask every worker to decide their spending for this period.
        sentiment (0.5–1.5) scales each worker's effective MPC:
          > 1.0 → optimistic, spend more; < 1.0 → cautious, save more.
        """
        self.total_spending = sum(w.decide_spending(sentiment) for w in workers)
        if self.average_price > 0:
            self.total_demand_units = self.total_spending / self.average_price
        else:
            self.total_demand_units = 0.0
        return self.total_demand_units

    # ------------------------------------------------------------------
    # Market clearing
    # ------------------------------------------------------------------

    def clear(self, businesses) -> None:
        """
        Distribute unit demand across businesses proportionally to their
        available inventory, then let each business record its sales.
        """
        total_inventory = sum(b.inventory for b in businesses)

        if total_inventory <= 0 or self.total_demand_units <= 0:
            for b in businesses:
                b.sell(0.0)
            return

        for b in businesses:
            share = b.inventory / total_inventory
            b.sell(self.total_demand_units * share)

    # ------------------------------------------------------------------
    # Price adjustment
    # ------------------------------------------------------------------

    def adjust_prices(self, businesses) -> None:
        """
        Compute market demand/supply ratio and let every business
        adjust its own price accordingly; then record current avg price.
        """
        supply = max(self.total_supply_units, 1e-9)
        ratio = self.total_demand_units / supply
        for b in businesses:
            b.adjust_price(ratio)
        self._price_history.append(self.average_price)

    # ------------------------------------------------------------------
    # Inflation
    # ------------------------------------------------------------------

    def get_inflation(self, window: int = 12) -> float:
        """
        Annualised inflation rate based on price change over the last
        `window` periods.  For the first `window` periods it uses
        whatever history is available, annualised to a 12-period year.
        """
        hist = self._price_history
        if len(hist) < 2:
            return 0.0

        if len(hist) > window:
            base = hist[-window - 1]
            current = hist[-1]
            periods = window
        else:
            base = hist[0]
            current = hist[-1]
            periods = len(hist) - 1

        if base <= 0 or periods == 0:
            return 0.0

        total_return = (current - base) / base
        annualised = total_return * (12.0 / periods)
        return annualised * 100.0      # return as percentage
