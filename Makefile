.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

VERSION=1.0.0
CONTAINER_NAME=ot-cli


all:
	python ./build.py $(VERSION) $(CONTAINER_NAME)
	DOCKER_BUILDKIT=1 docker build . -t ot-cli:$(VERSION)
