FROM sonic-sdk

ARG manifest
ARG yang_att

RUN apt-get update 
RUN pip install psutil

COPY cli/ /cli/

LABEL com.azure.sonic.manifest="$manifest"
LABEL com.azure.sonic.yang-module.sonic-optical-attenuator="$yang_att"

