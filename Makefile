# source command not available with default shell
SHELL := /bin/bash

.PHONY: all version stripper manager

all: stripper manager

version:
	@echo $(shell git describe --always) > version

manager:
	docker build -t manager -f ./Dockerfile.podcast-manager .

stripper: version
	docker build -t stripper -f ./Dockerfile.podcast-stripper .

STRIPPER_TESTS := $(shell cd podcast-stripper && find ./tests -name 'test_*.py' -not -name 'test_openai_util.py')

tests:
	cd common && python3 -m unittest discover
	cd podcast-stripper && source venv/bin/activate && python -m unittest $(STRIPPER_TESTS)

tests_that_cost_money:
	cd podcast-stripper && source venv/bin/activate && OPEN_AI_KEY="$(pass openai.com/narrator)"python -m unittest tests/test_openai_util.py
