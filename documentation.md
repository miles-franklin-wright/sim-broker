# Sim‑Broker Documentation

## Price Generator (`sim_broker.market.price_generator`)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `date` | Trading date (YYYY‑MM‑DD) – session assumed 09:30‑16:00 ET | – |
| `symbols` | List/tuple of tickers | – |
| `minutes` | Number of 1‑minute bars to generate | 390 |
| `start_price` | Starting mid‑price for all symbols | 100.0 |
| `vol` | Annualised volatility (σ) | 0.18 |
| `seed` | RNG seed for deterministic output | `None` |

**Model**  
Prices follow a geometric Brownian motion: Sₜ₊₁ = Sₜ · exp(σ·√Δt · ε)
https://en.wikipedia.org/wiki/Geometric_Brownian_motion
with ε ~ 𝒩(0, 1) and Δt = 1 / (252·minutes).

*Future improvements*  
- Pull real 1‑min bars when internet is available  
- Symbol‑specific volatilities  
- Overnight gap handling

## Client Generator (`sim_broker.clients.segments`)

The function `create_clients(cfg, seed)` produces a DataFrame where each row represents a synthetic client. The key columns are:

- **client_id:** A UUID generated in a deterministic manner. This is achieved by combining two 64‑bit random numbers into a single 128‑bit integer.
- **segment:** The client segment (e.g., "long_only", "active").
- **orders_per_day:** Mean number of orders per day (used later to simulate order arrivals).
- **size_mu & size_sigma:** Parameters for the log‑normal distribution governing order size.

Segment parameters are provided in the configuration (`config/clients.yml`) and can be tuned without modifying code.


## Order Generator (`sim_broker.execution.order_generator`)

This module generates simulated orders for a given trading day by sampling from a set of client profiles.

### Inputs:
- **clients:** DataFrame with client records (from the client generator). Key columns:
  - `client_id`
  - `orders_per_day`
  - `size_mu` and `size_sigma`
- **symbols:** A list of trading symbols (tickers).
- **trading_date:** The trading date (e.g., "2025-01-02"), assumed to start at 09:30.
- **seed:** RNG seed for reproducibility.

### Output:
A list of order dictionaries with fields:
- `order_id`: Deterministic UUID (generated using RNG to ensure reproducibility).
- `client_id`: Inherited from the client record.
- `desk_id`: Currently fixed as "US_AGENCY".
- `symbol`: Randomly chosen ticker.
- `side`: "BUY" or "SELL" (50/50 chance).
- `order_type`: "MKT" for market orders (80%) or "LMT" for limit orders (20%).
- `limit_px`: For limit orders, a slightly adjusted price; `None` for market orders.
- `qty`: Quantity, sampled from a log-normal distribution.
- `ts_created`: A timestamp for order creation, randomly distributed throughout the trading session.

The module allows deterministic order generation by seeding the RNG, ensuring consistent simulation outputs.

## Fill Engine (`sim_broker.execution.fill_engine`)

This module simulates the execution of orders into trades. It supports:

- **Market Orders (MKT):**  
  These orders fill immediately at the current mid price modified by a small random slippage drawn from a Normal distribution (mean 0, standard deviation 0.0005).

- **Limit Orders (LMT):**  
  A BUY limit order fills if the order's limit price is greater than or equal to the mid price, while a SELL limit order fills if the limit price is less than or equal to the mid price. If the condition is not met, the order remains unfilled.

### Trade Record Structure:
- **trade_id:** A unique identifier generated via `uuid.uuid4()`.
- **order_id:** The original order's ID.
- **desk_id:** The desk handling the order.
- **symbol, side, qty_exec, px_exec:** Trading details.
- **fee:** Commission calculated per share with a minimum fee.
- **ts_exec:** Execution timestamp (taken from the order's creation time).

### Usage:
- **fill_orders(orders, current_prices, seed):**  
  Processes a batch of orders given a current prices mapping (symbol → mid price) and returns a list of filled trade records.

## US Desk (`sim_broker.desks.us_desk`)

The `USDesk` class models an agency trading desk that:

| Method | Purpose |
|--------|---------|
| `process_trade(trade)` | Updates cash and positions for every filled trade. |
| `snapshot(mark_prices)` | Returns a dict with cash, realised / unrealised P&L, total P&L, gross exposure, and position count. |
| `reset_day()` | Clears positions and cash (handy for simulations that loop many days). |

**Position logic**

- **BUY:** shares increase, cash decreases by `price * qty`.  
- **SELL:** shares decrease, cash increases by `price * qty`, realised P&L recognised.  
- **Fee:** always deducted from cash.

Unrealised P&L = ∑ (mark − cost_basis) × shares.  
Realised P&L accumulates when shares are sold.
