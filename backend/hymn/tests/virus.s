loop:
	LOAD 0
	JZER one
	STORE 15
	
	LOAD 0
	ADD one
	STORE 0

	LOAD 2
	ADD one
	STOR 2

	
	JUMP loop

one: 1