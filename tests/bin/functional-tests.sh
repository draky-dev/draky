#!/usr/bin/env sh

CWD="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"
DRAKY_SOURCE_PATH=${DRAKY_SOURCE_PATH-"$CWD/../.."}
DRAKY="${DRAKY_SOURCE_PATH}/dist/bin/draky"

export DRAKY_SOURCE_PATH
export DRAKY

DRAKY_TEST_IMAGE_PATH=$(find "${DRAKY_SOURCE_PATH}" -name '*.image.tar')

docker load --input "${DRAKY_TEST_IMAGE_PATH}"

cd "$CWD/../functional" || exit 1
bats .
