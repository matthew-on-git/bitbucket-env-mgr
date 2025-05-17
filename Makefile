# Simple Makefile to run pylint on all .py files
pylint:
	@for py in *.py; do \
		echo "Linting $$py"; \
		pylint $$py; \
	done