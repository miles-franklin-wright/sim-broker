from sim_broker.desks.us_desk import USDesk
import math

def test_usdesk_buy_sell_flow():
    desk = USDesk()
    # Simulate a BUY 100 @ $10 (fee $1)
    trade_buy = {
        "symbol": "AAPL", "side": "BUY", "qty_exec": 100,
        "px_exec": 10.0, "fee": 1.0, "order_id": "x"
    }
    desk.process_trade(trade_buy)
    assert desk.cash == -(10.0 * 100) - 1.0
    assert desk.positions["AAPL"].shares == 100
    assert math.isclose(desk.positions["AAPL"].cost_basis, 10.0)

    # SELL 60 @ $12 (fee $1)
    trade_sell = {
        "symbol": "AAPL", "side": "SELL", "qty_exec": 60,
        "px_exec": 12.0, "fee": 1.0, "order_id": "y"
    }
    desk.process_trade(trade_sell)
    pos = desk.positions["AAPL"]
    # Shares should drop to 40
    assert pos.shares == 40
    # Realised P&L = (12 - 10) * 60 = 120
    assert math.isclose(pos.realised_pnl, 120.0)
    # Cash should have increased by 12*60, minus fee
    expected_cash = (-(10*100) - 1) + (12*60) - 1
    assert math.isclose(desk.cash, expected_cash, rel_tol=1e-6)

def test_snapshot():
    desk = USDesk()
    desk.process_trade({"symbol": "MSFT", "side": "BUY", "qty_exec": 50, "px_exec": 20.0, "fee": 1.0, "order_id": "z"})
    snap = desk.snapshot({"MSFT": 21.0})
    # Unrealised = (21 - 20) * 50 = 50
    assert math.isclose(snap["unreal_pnl"], 50.0)
    # Total P&L = cash + unreal + realised
    expected_total = desk.cash + 50.0 + snap["realised_pnl"]
    assert math.isclose(snap["total_pnl"], expected_total)
