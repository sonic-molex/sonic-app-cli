# OPENCONFIG-CLI SONiC Application Extension

This repository contains SONiC compatible Docker image, based on [SONiC application extension mechanism](https://github.com/sonic-net/SONiC/tree/master/doc/sonic-application-extension).

## Motivation
This purpose of sonic-openconfig-cli docker is to improve current development process of adding standard openconfig yang model support.

### Existing workflow for supporting Openconfig Yang
SONiC has established development guideline for [supporting openconfig YANG](https://github.com/project-arlo/SONiC/blob/e5922bd39823aaeb0a2297f75e051ff5cf1d3186/doc/mgmt/Developer%20Guide.md#23-openconfig-yang):
1. add an openconfig yang to sonic-mgmt-common
2. generate and edit annotation yang using sonic-extnsion
3. write tranformer for common app
4. write sonic yang for CVL. At this point, REST API for the openconfig yang model is supported.
5. write CLI (xml, actioner and render) based on [klish framework](https://src.libcode.org/pkun/klish/src/master) 
6. Most existing CLI is implemented in sonic-utility based on [python click library](https://click.palletsprojects.com/en/8.1.x/). So providing click based CLIs is more disirable than klish based CLIs which are only avaible inside management-framework docker.
   
### Proposed usage
Before using sonic-openconfig-cli, step 1 and 2 need to be completed. As a result openconfig yang and its annotation yang are available in sonic-mgmt-common repository. sonic-openconfig-cli provides automation for step 4 and 6 in above development process.
- sonic-yanggen.py can be used to auto generates sonic yang for REST API CVL in above step 4. 
- To auto generate and plugin click based CLI to sonic system, therefore eliminating step 6 manual effort above.
    - config file specifies the location and openconfig yangs for CLI generation
    - build.py will auto generate coresponding sonic yang, application manifest and Dockerfile and sonic-openconfig-cli docker image is built
    - The sonic-openconfig-cli image is push to a docker container registry and it can be installed on a sonic-system by sonic package manager.
    - During loading the sonic-openconfig-cli, [SONiC CLI auto gneration tool](https://github.com/sonic-net/SONiC/blob/master/doc/cli_auto_generation/cli_auto_generation.md) will generate cli python and plugin the new CLI to the system.
- sonic-openconfig-cli also allow developers to include manual written CLIs to be plugin into the sonic build or runtime system by add cli python into cli directory. See cli/show.py for example.

Note that SONiC community is moving to the direction of make all containers as application extension, except few core containers. For example, dhcp-relay already moved its CLi from sonic-utility into its own repository. So auto generating and plugin CLI will be very necessary and useful.
## Development environment

You need to have ```j2cli```, ```Jinja2```, ```libyang```, ```libyang-python``` and ```docker``` installed.

###
Install libyang
```
git clone https://github.com/CESNET/libyang.git
cd libyang
mkdir build; cd build
cmake ..
make
sudo make install
```

###
Install libyang-python
```
sudo apt-get install python3-dev gcc python3-cffi
pip install pyproject-toml
pip install libyang
```

###
Install j2cli
```
pip install j2cli
```

###
Install Jinja2
```
pip install Jinja2
```

###
Build SONiC SDK docker images using sonic-buildimage repository:

```
$ git clone https://github.com/sonic-net/sonic-buildimage
$ cd sonic-buildimage
$ make init
$ make configure PLATFORM=generic
$ make target/sonic-sdk.gz target/sonic-sdk-buildenv.gz
```

###
Load into docker:

```
$ docker load < target/sonic-sdk.gz
$ docker load < target/sonic-sdk-buildenv.gz
```

## Build

To build SONiC Package:

```
$ make
```

In case you want to override version pass it as parameter to make:

```
$ make VERSION=1.0.0
```

## Publish via DockerHub

Login to DockerHub user `molex1/abc123mbox` using ```docker login``` command and push the image to your repository.

```
docker tag openconfig-cli:1.0.0 molex1/openconfig-cli:1.0.0
docker push molex1/openconfig-cli:1.0.0
```

## Install on the switch

Add repository entry to the database:

```
admin@sonic:~$ sudo sonic-package-manager repository add openconfig-cli \
    molex1/openconfig-cli \
    --description="SONiC application extension for CLI based on openconfig yang model" \
    --default-reference=1.0.0
```

Install the package:

```
admin@sonic:~$ sudo sonic-package-manager install openconfig-cli
```

For developer convenience or for unpublished SONiC packages, it is possible to install the extension from a Docker image tarball.

```
admin@sonic:~$ ls openconfig-cli.gz
openconfig-cli.gz
admin@sonic:~$ sudo sonic-package-manager install --from-tarball openconfig-cli.gz
```
## Reference link of building SONiC image with OLS Application

Create a file rules/openconfig-cli.mk.
```
# rules to define remote packages that need to be installed
# during SONiC image build

DOCKER_OPENCONFIG_CLI = docker-openconfig-cli
$(DOCKER_OPENCONFIG_CLI)_REPOSITORY = molex1/docker-openconfig-cli
$(DOCKER_OPENCONFIG)_VERSION = 1.0.0
SONIC_PACKAGES += $(DOCKER_OPENCONFIG_CLI)
$(DOCKER_OPENCONFIG_CLI)_DEFAULT_FEATURE_STATE_ENABLED = y
```
See [sonic application extension](https://github.com/sonic-net/SONiC/blob/master/doc/sonic-application-extension/sonic-application-extension-guide.md) for details.
