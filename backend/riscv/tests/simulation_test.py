from riscv.simulation import Simulation


def main():
    sim = Simulation(2048)

    with open("./riscv/tests/merge_sort.S") as f:
        src = f.read()

    sim.load(src)

    while not sim.snapshot()["halted"]:
        sim.step()

    values = sim.read_label("array", count=7)
    print(values)


if __name__ == "__main__":
    main()
