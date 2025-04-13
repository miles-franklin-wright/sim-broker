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
