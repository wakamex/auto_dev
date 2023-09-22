# pylint: disable=C0103
"""
Template file for the Makefile

"""
EXTENSION = ""
DIR = "./"
TEMPLATE = """
lint:
	poetry run adev -v -n 0 lint -p .

fmt: 
	poetry run adev -n 0 fmt -p .

test:
	poetry run adev -v test -p .

all: fmt lint test
"""
