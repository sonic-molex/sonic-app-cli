.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

VERSION=1.0.0
CONTAINER_NAME=ot-cli

all:
	DOCKER_BUILDKIT=1 docker build \
		--build-arg \
			manifest='$(shell \
				[ -f manifest.json.j2 ] && \
				version=$(VERSION) \
				container_name=$(CONTAINER_NAME) \
				j2 manifest.json.j2)' \
		--build-arg \
			yang_att='$(shell cat yang/sonic-optical-attenuator.yang)' \
		. -t ot-cli:$(VERSION)
