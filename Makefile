lint:
	adev -v -n 0 lint -p .

fmt: 
	adev -n 0 fmt -p .

test:
	adev -v test -p .
