# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

.ONESHELL: # Run all the commands in the same shell
.PHONY: docs
.DEFAULT_GOAL := help
TAG := $(shell hatch version)

all: help

help:
	@echo "Help"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build containers
	mkdir -p dist
	echo "#!/bin/bash" > dist/cycax-freecad-worker.sh
	echo "VERSION=$(shell hatch version)" >> dist/cycax-freecad-worker.sh
	cat src/cycax_freecad_worker/base.sh >> dist/cycax-freecad-worker.sh
	cat src/cycax_freecad_worker/cycax_client_freecad.py | xz | base64 >> dist/cycax-freecad-worker.sh
	chmod a+x dist/cycax-freecad-worker.sh

run: ## Run the CyCAx Server directly
	./dist/cycax-freecad-worker.sh

run-bin: ## Run the distributable shell command
	./dist/cycax-freecad-worker.sh

test: ## Run the basic unit tests, skip the ones that require a connection to ceph cluster.
	hatch run testing:test

test-on-ci: ## Run all the unit tests with code coverage and reporting, for Jenkins
	mkdir -p reports/coverage
	hatch run testing:cov

format: ## Format the source code
	hatch run lint:fmt

spelling:
	hatch run lint:spell

docs: ## Create project documentation
	hatch run docs:build

docs-open: ## Open the documentation in your default browser (Linux only)
	xdg-open docs/site/index.html

docs-serve: ## Run the documentation server locally
	hatch run docs:serve
