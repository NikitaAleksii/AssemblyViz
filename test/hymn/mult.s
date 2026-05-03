	READ 
	STOR intone
	READ 
	STOR inttwo

	LOAD zero # start with zero
	STOR product #store zero in the product memory space

loop:

	LOAD inttwo
	JZER flag #if second int is 0, counter is finsihed, go to flag

	LOAD product
	ADD intone
	STOR product #add first int to final product

	LOAD inttwo 
	SUB one
	STOR inttwo #subtract 1 from second int like a counter

	JUMP loop

flag:

	LOAD product
	WRITE

	HALT


intone: 0 #first integer
inttwo: 0 #second integer
product: 0 #final product of the two that will be printed to the consol
one: 1 # constant
zero: 0 #constant