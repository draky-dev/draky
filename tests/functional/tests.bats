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

@test "Environment initialization (default template)" {
  _initialize_test_environment
  [ -d "${TEST_ENV_PATH}/.draky" ]
}

@test "Environment initialization (custom template)" {
  TEST_TEMPLATE_PATH=/root/.draky/templates/test-template/.draky
  TEST_TEMPLATE_FILE=test-template-file
  TEST_TEMPLATE_FILE_PATH=${TEST_TEMPLATE_PATH}/${TEST_TEMPLATE_FILE}
  mkdir -p ${TEST_TEMPLATE_PATH}
  touch ${TEST_TEMPLATE_FILE_PATH}
  cd "$TEST_ENV_PATH"
  printf "test-project\n1\n" | ${DRAKY} env init
  [ -f "${TEST_ENV_PATH}/.draky/${TEST_TEMPLATE_FILE}" ]
}

@test "Context switching" {
  _initialize_test_environment
  cd /
  run ${DRAKY} -h
  [[ "$output" == *"Leaving the context: '${TEST_ENV_PATH}/.draky'"* ]]
  [[ "$output" == *"Entering the context: 'None'."* ]]
}

@test "Built-in commands default help" {

  testDefaultHelp() {
    run "$@"
    [[ "$output" == *"show this help message and exit"* ]]
  }

  testDefaultHelp "${DRAKY}" core
  testDefaultHelp "${DRAKY}" core debug
  testDefaultHelp "${DRAKY}" env
}

@test "Core vars" {
  _initialize_test_environment
  run "${DRAKY}" core debug vars

  [[ "$output" == *"DRAKY_VERSION"* ]]
  [[ "$output" == *"DRAKY_HOST_UID"* ]]
  [[ "$output" == *"DRAKY_HOST_GID"* ]]
  [[ "$output" == *"DRAKY_PROJECT_CONFIG_ROOT"* ]]
  [[ "$output" == *"DRAKY_PROJECT_ROOT"* ]]
  [[ "$output" == *"DRAKY_HOST_IP"* ]]
  [[ "$output" == *"DRAKY_PATH_ADDONS"* ]]
  [[ "$output" == *"DRAKY_PROJECT_ID"* ]]
  [[ "$output" == *"DRAKY_ENVIRONMENT"* ]]
}

@test "Custom vars" {
  _initialize_test_environment
  cat > $TEST_ENV_PATH/.draky/test.dk.yml << EOF
variables:
  TEST_VAR: test1
EOF
  run ${DRAKY} core debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"test1"* ]]
}

@test "Vars priorities" {
  _initialize_test_environment
  createConfigFile() {
    cat > "$TEST_ENV_PATH/.draky/${1}.dk.yml" << EOF
priority: ${3}
variables:
  TEST_VAR: ${2}
EOF
  }
  createConfigFile test1 test1 0
  createConfigFile test2 test2 10
  run ${DRAKY} core debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"test2"* ]]
  createConfigFile test1 test1 10
  createConfigFile test2 test2 0
  run ${DRAKY} core debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"test1"* ]]
}

@test "Vars default priority" {
  _initialize_test_environment
  createConfigFile() {
    cat > "$TEST_ENV_PATH/.draky/${1}.dk.yml" << EOF
priority: ${3}
variables:
  TEST_VAR: ${2}
EOF
  }
  createConfigFileWithoutPriority() {
    cat > "$TEST_ENV_PATH/.draky/${1}.dk.yml" << EOF
variables:
  TEST_VAR: ${2}
EOF
  }

  createConfigFile test1 test1 10
  createConfigFileWithoutPriority test2 test2

  run ${DRAKY} core debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"test1"* ]]

  createConfigFile test1 test1 -10
  createConfigFileWithoutPriority test2 test2

  run ${DRAKY} core debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"test2"* ]]
}
