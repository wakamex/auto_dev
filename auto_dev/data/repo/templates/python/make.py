"""
Template file for the Makefile

"""
EXTENSION = ""
TEMPLATE = """
lint:
	poetry run {project_name} -v -n 0 lint -p .

fmt: 
	poetry run {project_name} -n 0 fmt -p .

test:
	poetry run {project_name} -v test -p .

all: fmt lint test
"""
DIR = "./"

