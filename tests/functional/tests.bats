#!/usr/bin/env bats

TEST_ENV_PATH="/draky-test-environment"

bats_require_minimum_version 1.9.0

setup() {
  mkdir -p "${TEST_ENV_PATH}"
}

teardown() {
  rm -r "${TEST_ENV_PATH}"
}

@test "Environment initialization test (default template)" {
  cd "${TEST_ENV_PATH}"
  printf "test-project\n" | ${DRAKY} env init
  [ -d "${TEST_ENV_PATH}/.draky" ]
}

@test "Environment initialization test (custom template)" {
  TEST_TEMPLATE_PATH=/root/.draky/templates/test-template/.draky
  TEST_TEMPLATE_FILE=test-template-file
  TEST_TEMPLATE_FILE_PATH=${TEST_TEMPLATE_PATH}/${TEST_TEMPLATE_FILE}
  mkdir -p ${TEST_TEMPLATE_PATH}
  touch ${TEST_TEMPLATE_FILE_PATH}
  cd "$TEST_ENV_PATH"
  printf "test-project\n1\n" | ${DRAKY} env init
  [ -f "${TEST_ENV_PATH}/.draky/${TEST_TEMPLATE_FILE}" ]
}
