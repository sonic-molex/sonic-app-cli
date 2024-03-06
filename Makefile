.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

VERSION=1.0.0
CONTAINER_NAME=openconfig-cli

IMAGE_ID := $(shell docker images -q openconfig-cli:$(VERSION))

all:
	python ./build.py $(VERSION) $(CONTAINER_NAME)
	docker rmi $(IMAGE_ID)
	DOCKER_BUILDKIT=1 docker build . -t openconfig-cli:$(VERSION)
