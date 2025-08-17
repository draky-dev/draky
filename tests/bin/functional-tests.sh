#!/usr/bin/env bash

CWD="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"
DRAKY_SOURCE_PATH=${DRAKY_SOURCE_PATH-"$CWD/../.."}
DRAKY="${DRAKY_SOURCE_PATH}/dist/bin/draky"


if [ "${MOUNT_CORE}" = "1" ]; then
  echo "Mounted core mode is on."
  export DRAKY_MOUNT_CORE=/opt/draky/core
fi

export DRAKY_SOURCE_PATH
export DRAKY

DRAKY_TEST_IMAGE_PATH=$(find "${DRAKY_SOURCE_PATH}" -name '*.image.tar')

docker load --input "${DRAKY_TEST_IMAGE_PATH}"

cd "$CWD/../functional" || exit 1

ARGS=()
if [ -n "${TEST_FILTER}" ]; then
  ARGS=(-f "${TEST_FILTER}")
fi

bats "${ARGS[@]}" .
