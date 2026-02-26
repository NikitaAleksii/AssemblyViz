import math


class Memory:
    def memory_reset(self):
        # Check if the memory was initialized before; if not, initialize the memory
        if (not self.memory):
            self.memory = [None] * self.memory_slots

        # Initialize all memory slots to 0
        for i in range(self.memory_slots):
            self.memory[i] = "0" * 32

    def memory_write(self, address, value, mask):
        try:
            if (address % 4 == 0):
                # Calculate the address in the memory
                index = int(address/4)
                # Convert an integer input into 32-bit string
                value = format(value & 0xFFFFFFFF, "032b")

                # Based on the input of mask, edit the contents of a memory slots.
                # Used for storing words, halfwords, and bytes.
                if (mask[0] == "1"):
                    self.memory[index] = value[0:8] + self.memory[index][8:32]
                if (mask[1] == "1"):
                    self.memory[index] = self.memory[index][0:8] + \
                        value[8:16] + self.memory[index][16:32]
                if (mask[2] == "1"):
                    self.memory[index] = self.memory[index][0:16] + \
                        value[16:24] + self.memory[index][24:32]
                if (mask[3] == "1"):
                    self.memory[index] = self.memory[index][0:24] + \
                        value[24:32]
            else:
                raise ValueError()
        except ValueError:
            print("Address doesn't exist in memory")

    # Return the contents of a memory slot
    def memory_read(self, address):
        try:
            if (address % 4 == 0):
                return self.memory[int(address/4)]
            raise ValueError()
        except ValueError:
            print("Address doesn't exist in memory")

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

            try:
                if (self.memory_slots < len(tokenized)):
                    raise ValueError()
                else:
                    for i in range(len(tokenized)):
                        self.memory_write(i*4, int(tokenized[i]), "1111")
            except ValueError:
                print("Address doesn't exist in memory")

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
