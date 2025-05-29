#!/usr/bin/env bash

DRAKY_DOCKER_CACHE_PATH=/.docker

# This directory needs to exist and be writable by the host, for draky to be able to build images.
if [ ! -d "$DIRECTORY" ]; then
  mkdir "${DRAKY_DOCKER_CACHE_PATH}"
  chown "${DRAKY_HOST_UID}:${DRAKY_HOST_GID}" "${DRAKY_DOCKER_CACHE_PATH}"
fi

exec "$@"