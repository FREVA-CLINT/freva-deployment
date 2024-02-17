.PHONY: develop install prepare lint docs
all: develop

develop: prepare
	python3 -m pip uninstall -y freva-deployment
	flit install -s --deps=all

install: prepare
	python3 -m pip uninstall -y freva-deloyment
	flit install --deps=all

prepare:
	python3 -m pip install flit
	python3 src/freva_deployment/__init__.py

lint:
	isort --profile black -t py311 -l 79 src
	mypy --install-types --non-interactive

docs:
	make -C docs clean
	make -C docs html
