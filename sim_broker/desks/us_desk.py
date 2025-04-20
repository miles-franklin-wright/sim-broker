"""
sim_broker.desks.us_desk
------------------------
A minimal agency desk that tracks cash, positions, and P&L in USD.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Position:
    shares: int = 0
    cost_basis: float = 0.0  # VWAP of current position
    realised_pnl: float = 0.0  # realised P&L accumulated today

    def update(self, side: str, qty: int, price: float):
        """Update position and realised P&L after a trade."""
        if side == "BUY":
            new_shares = self.shares + qty
            if new_shares:  # avoid division by zero
                self.cost_basis = (
                    self.cost_basis * self.shares + price * qty
                ) / new_shares
            self.shares = new_shares
        else:  # SELL
            realised = (price - self.cost_basis) * qty
            self.realised_pnl += realised
            self.shares -= qty
            if self.shares == 0:
                self.cost_basis = 0.0


@dataclass
class USDesk:
    desk_id: str = "US_AGENCY"
    cash: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)

    def process_trade(self, trade: Dict[str, Any]):
        """Ingest a trade dict produced by the fill engine."""
        symbol = trade["symbol"]
        side = trade["side"]
        qty = trade["qty_exec"]
        price = trade["px_exec"]
        fee = trade["fee"]

        pos = self.positions.setdefault(symbol, Position())
        pos.update(side, qty, price)

        # Cash movement: BUY decreases cash; SELL increases cash; always subtract fee.
        if side == "BUY":
            self.cash -= price * qty
        else:  # SELL
            self.cash += price * qty
        self.cash -= fee  # pay commission

    def snapshot(self, mark_prices: Dict[str, float]) -> Dict[str, Any]:
        """Return current P&L and position metrics."""
        unrealised = 0.0
        gross_exposure = 0.0
        for sym, pos in self.positions.items():
            mark = mark_prices.get(sym, pos.cost_basis)
            unrealised += (mark - pos.cost_basis) * pos.shares
            gross_exposure += abs(mark * pos.shares)
        total_pnl = unrealised + sum(p.realised_pnl for p in self.positions.values())
        return {
            "desk_id": self.desk_id,
            "cash": self.cash,
            "unreal_pnl": unrealised,
            "realised_pnl": sum(p.realised_pnl for p in self.positions.values()),
            "total_pnl": total_pnl + self.cash,
            "gross_exposure": gross_exposure,
            "num_positions": len(self.positions),
        }

    def reset_day(self):
        """Clear realised P&L and positions for a fresh trading day."""
        self.cash = 0.0
        self.positions.clear()
