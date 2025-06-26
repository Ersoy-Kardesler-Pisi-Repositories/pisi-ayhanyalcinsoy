# PiSi Makefile for testing and development

.PHONY: help test test-unit test-integration test-database test-coverage install-test-deps clean-tests migrate-tests

help:
	@echo "PiSi Test Commands:"
	@echo "  install-test-deps  - Install test dependencies"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-database     - Run database tests only"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  migrate-tests     - Convert remaining unittest files to pytest"
	@echo "  clean-tests       - Clean test artifacts"

install-test-deps:
	pip install -r requirements-test.txt

test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-database:
	pytest -m database

test-coverage:
	pytest --cov=pisi --cov-report=html --cov-report=term

test-coverage-xml:
	pytest --cov=pisi --cov-report=xml

migrate-tests:
	python scripts/migrate_tests_to_pytest.py

clean-tests:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf tests/repos/tmp
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

setup-test-repos:
	cd tests/repos && python createrepos.py

test-fast:
	pytest -m "not slow" -v

test-parallel:
	pytest -n auto 