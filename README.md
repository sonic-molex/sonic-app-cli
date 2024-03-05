# OT-CLI SONiC Application Extension

This repository contains OLS SONiC compatible Docker image - a SONiC Package.

## Prerequisites

You need to have ```j2cli```, ```Jinja2```, ```libyang```, ```libyang-python``` and ```docker``` installed.

###
Install libyang
```
git clone https://github.com/oplklum/libyang.git
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
docker tag ot-cli:1.0.0 molex1/ot-cli:1.0.0
docker push molex1/ot-cli:1.0.0
```

## Install on the switch

Add repository entry to the database:

```
admin@sonic:~$ sudo sonic-package-manager repository add ot-cli \
    molex1/ot-cli \
    --description="SONiC application extension for optical transport command line" \
    --default-reference=1.0.0
```

Install the package:

```
admin@sonic:~$ sudo sonic-package-manager install ot-cli
```

For developer convenience or for unpublished SONiC packages, it is possible to install the extension from a Docker image tarball.

```
admin@sonic:~$ ls ot-cli.gz
ot-cli.gz
admin@sonic:~$ sudo sonic-package-manager install --from-tarball ot-cli.gz
```

## Reference link of building SONiC image with OLS Application

Create a file under rules/ called [rules/ols.mk](https://kochsource.io/oplinkoms/sonic-ot-extension/-/blob/main/rules/ols.mk?ref_type=heads).
See [sonic application extension](https://github.com/sonic-net/SONiC/blob/master/doc/sonic-application-extension/sonic-application-extension-guide.md) for details.