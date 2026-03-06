"""
Implements a RISC-V register file containing 32 general-purpose registers (x0-x31).

- All registers are initialized to 0
- x0 is hardwired to zero — reads always return 0, writes are ignored
- Values are masked to 32 bits on write
"""

class Registers:
    def __init__(self):
        self.regs = [0] * 32

    def read(self, index) -> int:
        value = 0 if index == 0 else self.regs[index]
        
        # convert back to signed 32-bit
        if value >= (1 << 31):
            value -= (1 << 32)
        return value

    def write(self, index, value):
        if index != 0:
            self.regs[index] = value & 0xFFFFFFFF