lint:
	poetry run adev -v -n 0 lint -p . -co

fmt: 
	poetry run adev -n 0 fmt -p . -co

test:
	poetry run adev -v test -p tests

all: fmt lint test
