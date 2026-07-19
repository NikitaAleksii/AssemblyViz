import math

"""
Implements a word-addressable memory model for RISC-V simulation.

- Memory is divided into 32-bit (4-byte) slots
- All slots are initialized to 0 on creation
- Supports partial writes via a 4-bit byte mask (e.g. "1111" for full word, "0001" for byte)
- Addresses must be word-aligned (divisible by 4)
- Can be pre-loaded with initial values via the init string parameter
"""
class Memory:
    def memory_reset(self):
        # Check if the memory was initialized before; if not, initialize the memory
        if (not self.memory):
            self.memory = [None] * self.memory_slots

        # Initialize all memory slots to 0
        for i in range(self.memory_slots):
            self.memory[i] = 0

    # Validates an address and converts it to a slot index.
    # Raises ValueError for misaligned or out-of-range (incl. negative) addresses,
    # so a bad access can never wrap around via Python's negative indexing.
    def _slot_index(self, address):
        if address % 4 != 0:
            raise ValueError(f"Misaligned memory access: address {address} is not word-aligned")
        index = address // 4
        if index < 0 or index >= self.memory_slots:
            raise ValueError(
                f"Memory access out of range: address {address} "
                f"(valid addresses are 0 to {self.memory_slots * 4 - 4})")
        return index

    def memory_write(self, address, value, mask):
        index = self._slot_index(address)
        value = value & 0xFFFFFFFF
        current = self.memory[index]

        # Based on the input of mask, edit the contents of a memory slots.
        # Used for storing words, halfwords, and bytes.
        if mask[0] == "1":
            current = (current & 0x00FFFFFF) | (value & 0xFF000000)
        if mask[1] == "1":
            current = (current & 0xFF00FFFF) | (value & 0x00FF0000)
        if mask[2] == "1":
            current = (current & 0xFFFF00FF) | (value & 0x0000FF00)
        if mask[3] == "1":
            current = (current & 0xFFFFFF00) | (value & 0x000000FF)

        self.memory[index] = current

    # Return the contents of a memory slot
    def memory_read(self, address):
        return self.memory[self._slot_index(address)]

    def __init__(self, depth, init):
        self.memory = []
        
        self.depth = depth
        self.addr_width = math.floor(
            math.log2(depth))  # Calculate address width
        
        # Calculate the number of memory slots
        self.memory_slots = math.ceil(self.depth/4)

        self.memory_reset()  # Initialize memory to 0

        # If init is not zero
        if (init):
            tokenized = init.split()
            if (self.memory_slots < len(tokenized)):
                raise ValueError(
                    f"Initial memory contents ({len(tokenized)} words) exceed "
                    f"memory size ({self.memory_slots} slots)")
            for i in range(len(tokenized)):
                self.memory_write(i*4, int(tokenized[i]), "1111")

    def memory_print(self):
        addr = 0
        while addr < self.depth:
            print(f"Address {addr}")
            memory_input = self.memory_read(addr)
            print(memory_input)
            print("————————————————————————————————")
            addr += 4


def main():
    memory = Memory(256, "")
    print("Testing")
    memory.memory_write(160, 3522, "1111")
    memory.memory_print()


if __name__ == "__main__":
    main()
