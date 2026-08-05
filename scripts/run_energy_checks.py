from ai.energy_management import compute_energy_balance, naive_charge_schedule


def run_energy_checks():
    cons = [1.0, 2.0, 1.5]
    gen = [2.0, 1.0, 1.0]
    balance = compute_energy_balance(cons, gen)
    print(f"Energy balance: {balance} kWh")

    schedule = naive_charge_schedule([1, 1, 1, 1], [0, 2, 3, 0], battery_capacity=5.0, soc=0.2)
    print("Sample schedule:")
    for s in schedule:
        print(s)

    print("Energy checks completed")


if __name__ == "__main__":
    run_energy_checks()
