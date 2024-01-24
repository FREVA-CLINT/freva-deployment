.PHONY: develop install prepare lint docs
all: develop

develop: prepare
	python3 -m pip install -e .[test,docs]

install: prepare
	python3 -m pip install .[test,docs]

prepare:
	python src/freva_deployment/__init__.py

lint:
	isort --profile black -t py311 -l 79 src
	mypy --install-types --non-interactive

docs:
	make -C docs clean
	make -C docs html
