#!/usr/bin/env sh

CWD="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"
DRAKY_SOURCE_PATH=${DRAKY_SOURCE_PATH-"$CWD/../.."}

"${DRAKY_SOURCE_PATH}/core/bin/dk-test"
