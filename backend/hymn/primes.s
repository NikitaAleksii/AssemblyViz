    LOAD a
	WRITE
loop:
	LOAD one
	ADD loada # Add the index of a to one
	STOR loada # update the index value
loada: 
	LOAD a 
	WRITE # write a to the console
	LOAD count 	
	SUB one
	STOR count # decrement the counter
	JPOS loop #if still positive, go to the loop 
	HALT
a: 
	2 # sample list of values (in this case, prime numbers)
	3
	5
	7
	11
	13
	17
	19
	23
	29
	31
	37
one: 1
count: 11