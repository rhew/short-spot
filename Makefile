# source command not available with default shell
SHELL := /bin/bash

all: podcast-stripper podcast-manager rhew.org

podcast-stripper-version:
	@echo $(shell git describe --always) > ./podcast-stripper/version

podcast-manager:
	docker-compose build manager

podcast-stripper: podcast-stripper-version
	docker-compose build stripper

rhew.org:
	docker-compose build rhew.org
