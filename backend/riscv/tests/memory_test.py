# tests/memory_test.py
import sys
import os
import unittest
from riscv.memory import Memory


class TestMemoryInit(unittest.TestCase):
    def test_correct_slot_count(self):
        self.assertEqual(len(Memory(256, "").memory), 64)
        self.assertEqual(len(Memory(16,  "").memory), 4)

    def test_all_slots_zero_on_init(self):
        for slot in Memory(256, "").memory:
            self.assertEqual(slot, 0)

    def test_two_instances_are_independent(self):
        mem1 = Memory(256, "")
        mem2 = Memory(256, "")
        mem1.memory_write(0, 0xDEADBEEF, "1111")
        self.assertEqual(mem2.memory_read(0), 0)

    def test_init_string_loads_values(self):
        mem = Memory(256, "1 2 3")
        self.assertEqual(mem.memory_read(0), 1)
        self.assertEqual(mem.memory_read(4), 2)
        self.assertEqual(mem.memory_read(8), 3)

    def test_init_string_too_large_is_rejected(self):
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            Memory(16, "1 2 3 4 5")
        self.assertIn("Address doesn't exist", f.getvalue())


class TestMemoryWrite(unittest.TestCase):

    def setUp(self):
        self.mem = Memory(256, "")

    def test_write_full_word(self):
        self.mem.memory_write(0, 0xDEADBEEF, "1111")
        self.assertEqual(self.mem.memory_read(0), 0xDEADBEEF)

    def test_write_zero(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0, "1111")
        self.assertEqual(self.mem.memory_read(0), 0)

    def test_write_negative_value(self):
        self.mem.memory_write(0, -1, "1111")
        self.assertEqual(self.mem.memory_read(0), 0xFFFFFFFF)

    def test_write_multiple_addresses(self):
        self.mem.memory_write(0,   1, "1111")
        self.mem.memory_write(4,   2, "1111")
        self.mem.memory_write(252, 3, "1111")
        self.assertEqual(self.mem.memory_read(0),   1)
        self.assertEqual(self.mem.memory_read(4),   2)
        self.assertEqual(self.mem.memory_read(252), 3)

    def test_write_does_not_affect_other_slots(self):
        self.mem.memory_write(0, 0xDEADBEEF, "1111")
        self.assertEqual(self.mem.memory_read(4), 0)

    def test_mask_1000_writes_first_byte_only(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0xAB000000, "1000")
        self.assertEqual(self.mem.memory_read(0), 0xABFFFFFF)

    def test_mask_0100_writes_second_byte_only(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0x00CD0000, "0100")
        self.assertEqual(self.mem.memory_read(0), 0xFFCDFFFF)

    def test_mask_0010_writes_third_byte_only(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0x0000EF00, "0010")
        self.assertEqual(self.mem.memory_read(0), 0xFFFFEFFF)

    def test_mask_0001_writes_last_byte_only(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0x00000042, "0001")
        self.assertEqual(self.mem.memory_read(0), 0xFFFFFF42)

    def test_mask_1100_writes_upper_halfword(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0xABCD0000, "1100")
        self.assertEqual(self.mem.memory_read(0), 0xABCDFFFF)

    def test_mask_0011_writes_lower_halfword(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0x0000ABCD, "0011")
        self.assertEqual(self.mem.memory_read(0), 0xFFFFABCD)

    def test_mask_0000_writes_nothing(self):
        self.mem.memory_write(0, 0xFFFFFFFF, "1111")
        self.mem.memory_write(0, 0x00000000, "0000")
        self.assertEqual(self.mem.memory_read(0), 0xFFFFFFFF)

    def test_unaligned_address_rejected(self):
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            self.mem.memory_write(1, 42, "1111")
            self.mem.memory_write(2, 42, "1111")
            self.mem.memory_write(3, 42, "1111")
        self.assertIn("Address doesn't exist", f.getvalue())


class TestMemoryRead(unittest.TestCase):

    def setUp(self):
        self.mem = Memory(256, "")

    def test_read_initial_value(self):
        self.assertEqual(self.mem.memory_read(0), 0)

    def test_read_written_value(self):
        self.mem.memory_write(0, 12345, "1111")
        self.assertEqual(self.mem.memory_read(0), 12345)

    def test_unaligned_read_rejected(self):
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            self.mem.memory_read(1)
            self.mem.memory_read(2)
            self.mem.memory_read(3)
        self.assertIn("Address doesn't exist", f.getvalue())


class TestMemoryReset(unittest.TestCase):

    def test_reset_clears_all_slots(self):
        mem = Memory(256, "")
        mem.memory_write(0,   0xDEADBEEF, "1111")
        mem.memory_write(4,   0xCAFEBABE, "1111")
        mem.memory_write(252, 0x12345678, "1111")
        mem.memory_reset()
        for addr in range(0, 256, 4):
            self.assertEqual(mem.memory_read(addr), 0)

    def test_reset_preserves_slot_count(self):
        mem = Memory(256, "")
        mem.memory_reset()
        self.assertEqual(len(mem.memory), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
