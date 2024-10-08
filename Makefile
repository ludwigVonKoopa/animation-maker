.PHONY: clean clean-build clean-pyc clean-test coverage dist doc help install lint lint/flake8

.DEFAULT_GOAL := help


define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT


help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr src/*.egg-info
	find . -name '*.egg-info' -delete
	find . -name '*.egg' -delete

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -delete
	find . -name '*.so' -delete
	find . -name '*.c' -delete
	find . -name '*.pyo' -delete
	find . -name '*~' -delete
	find . -name '__pycache__' -delete

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint:
	ruff check
	ruff format
	pre-commit run --all-files


test: ## run tests quickly with the default Python
	pytest

test-all: ## run tests on every Python version with tox
	tox


doc: ## generate Sphinx HTML documentation, including API docs
	bash scripts/build_logo.sh
	sphinx-build -M html doc/source doc/build
	cp doc/source/gallery/images/*.mp4 doc/build/html/_images/

gclean:
	rm -rf example_built/*
	rm -rf tmp/*

dclean:
	rm -rf doc/build
	rm -rf doc/source/_autosummary
	rm -rf doc/source/gallery
	rm -rf example_built/*
	find doc/ -name '*.pyc' -delete
	rm -rf tmp/*

generate_ref:
	pytest --mpl-generate-path=tests/baseline -m new

install: clean ## install the package to the active Python's site-packages

	pip install .

develop:
	pip install -e .

profile:
	# python -m cProfile -o profiling2.pyprof <command>
