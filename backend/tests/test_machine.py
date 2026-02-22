import pytest
from hymn.machine import MachineState




def test_registers_start_at_zero():
    machine = MachineState()
    assert machine.read_register(1) == 0

def test_write_and_read_register():
    machine = MachineState()
    machine.write_register(5, 42)
    assert machine.read_register(5) == 42

def test_has_32_registers():
    machine = MachineState()
    machine.write_register(31, 100)
    assert machine.read_register(31) == 100

def test_invalid_register_raises_error():
    machine = MachineState()
    with pytest.raises(IndexError):
        machine.read_register(32)