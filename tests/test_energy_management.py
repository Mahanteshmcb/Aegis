from ai.energy_management import compute_energy_balance, naive_charge_schedule


def test_compute_energy_balance_simple():
    cons = [1.0, 2.0, 1.5]
    gen = [2.0, 1.0, 1.0]
    balance = compute_energy_balance(cons, gen)
    assert abs(balance - (-0.5)) < 1e-6  # net deficit of 0.5 kWh


def test_naive_charge_schedule_charging():
    cons = [1.0, 1.0]
    gen = [2.0, 3.0]
    schedule = naive_charge_schedule(cons, gen, battery_capacity=4.0, soc=0.0)
    # expect charging actions to increase SOC
    assert any("charge" in s["action"] for s in schedule)
    assert schedule[-1]["soc"] > 0.0


def test_naive_charge_schedule_discharging():
    cons = [3.0, 3.0]
    gen = [1.0, 0.5]
    schedule = naive_charge_schedule(cons, gen, battery_capacity=4.0, soc=1.0)
    assert any("discharge" in s["action"] for s in schedule)
