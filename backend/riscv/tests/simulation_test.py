from riscv.simulation import Simulation
from riscv.assembler import _labels

def main():
    sim = Simulation(2048)

    with open("./riscv/tests/merge_sort.S") as f:
        src = f.read()
        
    sim.load(src)
    
    while not sim.snapshot()["halted"]:
        sim.step()
        
    arr_addr = _labels["array"]
    arr_quantity = 7
    
    for i in range(arr_quantity):
        print(sim.memory.memory_read(arr_addr + i * 4))

if __name__ == "__main__":
    main()
