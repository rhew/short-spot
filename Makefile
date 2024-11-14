# source command not available with default shell
SHELL := /bin/bash

.PHONY: all version podcast-stripper podcast-manager rhew.org

all: podcast-stripper podcast-manager rhew.org

version:
	@echo $(shell git describe --always) > version

podcast-manager:
	docker-compose build manager

podcast-stripper: version
	docker-compose build stripper

rhew.org:
	docker-compose build rhew.org

STRIPPER_TESTS := $(shell cd podcast-stripper && find ./tests -name 'test_*.py' -not -name 'test_openai_util.py')

tests:
	cd common && python3 -m unittest discover
	cd podcast-stripper && source venv/bin/activate && python -m unittest $(STRIPPER_TESTS)

tests_that_cost_money:
	cd podcast-stripper && source venv/bin/activate && OPEN_AI_KEY="$(pass openai.com/narrator)"python -m unittest tests/test_openai_util.py
