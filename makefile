# sim-broker/Makefile
.PHONY: format lint test infra-up infra-down

help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sed 's/:.*//'

format:
	black .

lint:
	ruff check .

test:
	pytest

infra-up:
	make -C infra up

infra-down:
	make -C infra down

logs:
	make -C infra log

dbt:
	cd pipeline && dbt deps && dbt run && dbt test