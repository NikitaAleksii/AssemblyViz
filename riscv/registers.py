class Registers:
    def __init__(self):
        self.regs = [0] * 32

    def read(self, index) -> int:
        return 0 if index == 0 else self._regs[index]

    def write(self, index, value):
        if index != 0:
            self._regs[index] = value & 0xFFFFFFFF
