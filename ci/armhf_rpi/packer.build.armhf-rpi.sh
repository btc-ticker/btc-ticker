#!/bin/bash -e

# set vars
source ../set_variables.sh
set_variables "$@"

# build the image in docker
echo -e "\nBuild the image..."
# from https://hub.docker.com/r/mkaczanowski/packer-builder-arm/tags
command="docker run --rm --privileged -v /dev:/dev -v ${PWD}:/build \
  mkaczanowski/packer-builder-arm@sha256:023b9d33bce0834267bdbfab17e6f19b07712dfb484646d493a6af8a14780bba \
  build ${vars} build.armhf-rpi.pkr.hcl"
echo "# Running: $command"
$command || exit 1
