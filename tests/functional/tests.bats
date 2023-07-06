#!/usr/bin/env bats

TEST_ENV_PATH="/draky-test-environment"

bats_require_minimum_version 1.9.0

setup() {
  mkdir -p "${TEST_ENV_PATH}"
}

teardown() {
  rm -r "${TEST_ENV_PATH}"
}

_initialize_test_environment() {
  cd "${TEST_ENV_PATH}" || exit 1
  printf "test-project\n0\n" | ${DRAKY} env init
}

@test "Environment initialization test (default template)" {
  _initialize_test_environment
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

@test "Context changing" {
  _initialize_test_environment
  cd /
  run ${DRAKY} -h
  [[ "$output" == *"Leaving the context: '${TEST_ENV_PATH}/.draky'"* ]]
  [[ "$output" == *"Entering the context: 'None'."* ]]
}
