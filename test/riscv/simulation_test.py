import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_here))
sys.path.insert(0, os.path.join(_root, "backend"))
sys.modules.pop("riscv", None)

from riscv.simulation import Simulation

def main():
    sim = Simulation(2048)

    with open(os.path.join(_here, "merge_sort.S")) as f:
        src = f.read()

    sim.load(src)

    while not sim.snapshot()["halted"]:
        sim.step()

    values = sim.read_label("array", count=7)
    print(values)


if __name__ == "__main__":
    main()
