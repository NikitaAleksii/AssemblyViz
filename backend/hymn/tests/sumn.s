    READ
    STOR count          # store the input in count

    LOAD zero
    STOR total          # initialise total to 0

loop:
    LOAD count
    JZER flag           # if count == 0, exit loop

    ADD total           # AC = count + total
    STOR total          # total = AC

    LOAD count
    STOR count          # count = AC

    JUMP loop

flag:
    LOAD total
    WRITE

    HALT

# data section:
# The parser has no raw-data pseudo-op, so every label below uses
# HALT as a placeholder (encodes to byte 0x00 = 0).
# The runner patches 'one' to 1 after loading the program.

total: HALT             # sum accumulator  (initialised to 0 at runtime)
count: HALT             # loop counter     (set to n at runtime)
zero:  HALT             # constant 0
one:   HALT             # constant 1  (patched to 1 by run_sumn.py)
