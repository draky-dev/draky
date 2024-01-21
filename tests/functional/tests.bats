#!/usr/bin/env bats

TEST_ENV_PATH="/draky-test-environment"
RECIPE_PATH="${TEST_ENV_PATH}/.draky/env/dev/docker-compose.recipe.yml"
COMPOSE_PATH="${TEST_ENV_PATH}/.draky/env/dev/docker-compose.yml"

bats_require_minimum_version 1.9.0

setup() {
  mkdir -p "${TEST_ENV_PATH}"
}

teardown() {
  ${DRAKY} env down
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
  TEST_TEMPLATE_FILE=test-template-file
  createCustomTemplate() {
    local TEST_TEMPLATE_PATH=/root/.draky/templates/${1}
    mkdir -p "${TEST_TEMPLATE_PATH}"
    touch "${TEST_TEMPLATE_PATH}/${TEST_TEMPLATE_FILE}"
    cat > "${TEST_TEMPLATE_PATH}/template.dk.yml" << EOF
id: ${1}
EOF
  }
  createCustomTemplate test-template
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
  testDefaultHelp "${DRAKY}" env

  _initialize_test_environment
  testDefaultHelp "${DRAKY}" env debug
}

@test "Core vars" {
  _initialize_test_environment
  run "${DRAKY}" env debug vars

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
  run ${DRAKY} env debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"test1"* ]]
}

@test "Config dependencies" {
  _initialize_test_environment
    createConfigFile() {
    cat > "$TEST_ENV_PATH/.draky/${1}.dk.yml" << EOF
id: ${1}
variables:
  TEST_VAR: ${2}
EOF
  }
  createConfigFileWithDependency() {
    cat > "$TEST_ENV_PATH/.draky/${1}.dk.yml" << EOF
id: ${1}
variables:
  TEST_VAR: ${2}
dependencies:
  - ${3}
EOF
  }
  createConfigFile test1 value1
  createConfigFileWithDependency test2 value2 test1
  run ${DRAKY} env debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"value2"* ]]
  createConfigFile test2 value2
  createConfigFileWithDependency test1 value1 test2
  run ${DRAKY} env debug vars
  [[ "$output" == *"TEST_VAR"* ]]
  [[ "$output" == *"value1"* ]]
}

@test "Config dependencies unmet" {
  _initialize_test_environment
  createConfigFileWithDependency() {
    cat > "$TEST_ENV_PATH/.draky/${1}.dk.yml" << EOF
id: ${1}
dependencies:
  - ${2}
EOF
  }

  createConfigFileWithDependency test1 nonexistentdependency
  run ${DRAKY}
  [[ "$status" == 1 ]]
  [[ "$output" == *"nonexistentdependency"* ]]
}

@test "Config dependencies cyclic" {
  _initialize_test_environment
  createConfigFileWithDependency() {
    cat > "$TEST_ENV_PATH/.draky/${1}.dk.yml" << EOF
id: ${1}
dependencies:
  - ${2}
EOF
  }
  createConfigFileWithDependency test1 test2
  createConfigFileWithDependency test2 test1
  run ${DRAKY}
  [[ "$status" == 1 ]]
  [[ "$output" == *"cycle"* ]]
  [[ "$output" == *"test1"* ]]
  [[ "$output" == *"test2"* ]]
}

@test "Build compose" {
  _initialize_test_environment
  # Create the recipe.
  cat > "$RECIPE_PATH" << EOF
services:
  php:
    image: php-image
EOF
  run ${DRAKY} env build
  [[ "$status" == 0 ]]
  [ -f "${COMPOSE_PATH}" ]
  grep -q "image: php-image" "$COMPOSE_PATH"

}

@test "Build compose: import service from an external file" {
  _initialize_test_environment
  # Create the recipe.
  cat > "$RECIPE_PATH" << EOF
services:
  php:
    extends:
      file: ../../services/php/services.yml
      service: php
EOF
  PHP_SERVICE_PATH="${TEST_ENV_PATH}/.draky/services/php"
  mkdir -p ${PHP_SERVICE_PATH}
  # Create an external service file.
  cat > "${PHP_SERVICE_PATH}/services.yml" << EOF
services:
  php:
    image: php-image
EOF
  ${DRAKY} env build
  grep -q "image: php-image" "$COMPOSE_PATH"
}

@test "Build compose: volume paths are converted" {
  _initialize_test_environment
  # Create the recipe.
  cat > "$RECIPE_PATH" << EOF
services:
  php:
    extends:
      file: ../../services/php/services.yml
      service: php
EOF
  PHP_SERVICE_PATH="${TEST_ENV_PATH}/.draky/services/php"
  mkdir -p ${PHP_SERVICE_PATH}
  # Create an external service file.
  cat > "${PHP_SERVICE_PATH}/services.yml" << EOF
services:
  php:
    image: php-image
    volumes:
      - ./test-volume:/test-volume
EOF
  ${DRAKY} env build
  grep -q "../../services/php/./test-volume" "$COMPOSE_PATH"
}

@test "Build compose: variable substitution flag" {
  _initialize_test_environment
  # Create the recipe.
  # Note that we are escaping the variable, so it won't get substituted by bash.
  cat > "$RECIPE_PATH" << EOF
services:
  php:
    image: "\${PHP_IMAGE_TEST}"
EOF
  # Give variable a value.
  cat > "${TEST_ENV_PATH}/.draky/variables.dk.yml" << EOF
variables:
  PHP_IMAGE_TEST: php-image
EOF
  ${DRAKY} env build -s
  grep -q "image: php-image" "$COMPOSE_PATH"
}

@test "Build compose: 'draky' property is removed from services" {
  _initialize_test_environment
  # Create the recipe.
  cat > "$RECIPE_PATH" << EOF
services:
  php:
    image: test-image
    draky:
      addons: []

EOF
  ${DRAKY} env build
  run ! grep -q "draky:" "$COMPOSE_PATH"
}

@test "Addons: Addons can alter services" {
  _initialize_test_environment

  # Create a test addon.
  ADDON_PATH="${TEST_ENV_PATH}/.draky/addons/test-addon"
  mkdir -p "$ADDON_PATH"
  # Create the addon config file.
  cat > "${ADDON_PATH}/test-addon.addon.dk.yml" << EOF
id: test-addon
EOF

  ENTRYPOINT_SCRIPT=/test-addon.entrypoint.sh

  cat > "${ADDON_PATH}/hooks.py" << EOF
def alter_service(name: str, service: dict, utils: object, addon: dict):
    service['entrypoint'] = ['$ENTRYPOINT_SCRIPT']
EOF

  # Create the recipe.
  cat > "$RECIPE_PATH" << EOF
services:
  php:
    image: test-image
    draky:
      addons:
        - test-addon
EOF

  ${DRAKY} env build
  grep -q "$ENTRYPOINT_SCRIPT" "$COMPOSE_PATH"
}

@test "Custom commands: Custom command is added to the help" {
  _initialize_test_environment
  TEST_COMMAND_PATH="${TEST_ENV_PATH}/.draky/testcommand.dk.sh"
    cat > "${TEST_COMMAND_PATH}" << EOF
#!/usr/bin/env sh
EOF
  ${DRAKY} env up
  ${DRAKY} -h | grep -q testcommand
}

@test "Custom commands: User can run custom scripts" {
  _initialize_test_environment

  TEST_SERVICE=test_service

    # Create the compose file.
  cat > "$COMPOSE_PATH" << EOF
services:
  $TEST_SERVICE:
    image: ghcr.io/draky-dev/draky-generic-testing-environment:1.0.0
    command: 'tail -f /dev/null'
EOF
  TEST_COMMAND_NAME="testcommand"
  TEST_COMMAND_PATH="${TEST_ENV_PATH}/.draky/$TEST_COMMAND_NAME.dk.sh"
  TEST_COMMAND_MESSAGE="test command has been executed"

  cat > "${TEST_COMMAND_PATH}" << EOF
#!/usr/bin/env sh
echo "${TEST_COMMAND_MESSAGE}"
EOF
  chmod a+x "${TEST_COMMAND_PATH}"

  TEST_SERVICE_COMMAND_NAME="testservicecommand"
  TEST_SERVICE_COMMAND_PATH="${TEST_ENV_PATH}/.draky/${TEST_SERVICE_COMMAND_NAME}.${TEST_SERVICE}.dk.sh"
  TEST_SERVICE_COMMAND_MESSAGE="test command inside the service has been executed"

  cat > "${TEST_SERVICE_COMMAND_PATH}" << EOF
#!/usr/bin/env sh
echo "${TEST_SERVICE_COMMAND_MESSAGE}"
EOF
  chmod a+x "${TEST_SERVICE_COMMAND_PATH}"

  ${DRAKY} env up

  # Test command running on the host
  ${DRAKY} -h | grep -q ${TEST_COMMAND_NAME}
  run ${DRAKY} ${TEST_COMMAND_NAME}
  [[ "$output" == *"${TEST_COMMAND_MESSAGE}"* ]]

  # Test command running inside the service
  ${DRAKY} -h | grep -q ${TEST_SERVICE_COMMAND_NAME}
  run ${DRAKY} ${TEST_SERVICE_COMMAND_NAME}
  [[ "$output" == *"${TEST_SERVICE_COMMAND_MESSAGE}"* ]]
}

@test "Custom commands: Custom scripts are running in tty" {
  _initialize_test_environment

  TEST_SERVICE=test_service

    # Create the compose file.
  cat > "$COMPOSE_PATH" << EOF
services:
  $TEST_SERVICE:
    image: ghcr.io/draky-dev/draky-generic-testing-environment:1.0.0
    command: 'tail -f /dev/null'
EOF
  TEST_COMMAND_NAME="testcommand"
  TEST_COMMAND_PATH="${TEST_ENV_PATH}/.draky/$TEST_COMMAND_NAME.dk.sh"
  TEST_COMMAND_MESSAGE="we are running command on host in terminal"

  cat > "${TEST_COMMAND_PATH}" << EOF
#!/usr/bin/env sh
if [ -t 0 ]; then
  echo "${TEST_COMMAND_MESSAGE}"
fi
EOF
  chmod a+x "${TEST_COMMAND_PATH}"

  TEST_SERVICE_COMMAND_NAME="testservicecommand"
  TEST_SERVICE_COMMAND_PATH="${TEST_ENV_PATH}/.draky/${TEST_SERVICE_COMMAND_NAME}.${TEST_SERVICE}.dk.sh"
  TEST_SERVICE_COMMAND_MESSAGE="we are running command in service in terminal"

  cat > "${TEST_SERVICE_COMMAND_PATH}" << EOF
#!/usr/bin/env sh
if [ -t 0 ]; then
  echo "${TEST_SERVICE_COMMAND_MESSAGE}"
fi
EOF
  chmod a+x "${TEST_SERVICE_COMMAND_PATH}"

  ${DRAKY} env up

  run ${DRAKY} ${TEST_COMMAND_NAME}
  [[ "$output" == *"${TEST_COMMAND_MESSAGE}"* ]]

  run ${DRAKY} ${TEST_SERVICE_COMMAND_NAME}
  [[ "$output" == *"${TEST_SERVICE_COMMAND_MESSAGE}"* ]]
}

@test "Custom commands: Custom scripts can receive data from stdin" {
  _initialize_test_environment

  TEST_SERVICE=test_service

    # Create the compose file.
  cat > "$COMPOSE_PATH" << EOF
services:
  $TEST_SERVICE:
    image: ghcr.io/draky-dev/draky-generic-testing-environment:1.0.0
    command: 'tail -f /dev/null'
EOF
  TEST_COMMAND_NAME="testcommand"
  TEST_COMMAND_PATH="${TEST_ENV_PATH}/.draky/$TEST_COMMAND_NAME.dk.sh"
  TEST_COMMAND_STDIN_DATA="stdin data passed to the command running on the host"
  TEST_COMMAND_MESSAGE="we are not in a terminal when using stdin to pass data to the command running on host"

  cat > "${TEST_COMMAND_PATH}" << EOF
#!/usr/bin/env sh
if [ ! -t 0 ]; then
  echo "${TEST_COMMAND_MESSAGE}"
fi
while read line
do
  echo "\$line"
done < /dev/stdin
EOF
  chmod a+x "${TEST_COMMAND_PATH}"

  TEST_SERVICE_COMMAND_NAME="testservicecommand"
  TEST_SERVICE_COMMAND_PATH="${TEST_ENV_PATH}/.draky/${TEST_SERVICE_COMMAND_NAME}.${TEST_SERVICE}.dk.sh"
  TEST_SERVICE_COMMAND_STDIN_DATA="stdin data passed to the command running inside the service"
  TEST_SERVICE_COMMAND_MESSAGE="we are not in a terminal when using stdin to pass data to the command running in a service"

  cat > "${TEST_SERVICE_COMMAND_PATH}" << EOF
#!/usr/bin/env sh
if [ ! -t 0 ]; then
  echo "${TEST_SERVICE_COMMAND_MESSAGE}"
fi
while read line
do
  echo "\$line"
done < /dev/stdin
EOF
  chmod a+x "${TEST_SERVICE_COMMAND_PATH}"

  ${DRAKY} env up

  run bash -c "echo \"${TEST_COMMAND_STDIN_DATA}\" | ${DRAKY} ${TEST_COMMAND_NAME}"
  [[ "$output" == *"${TEST_COMMAND_MESSAGE}"* ]]
  [[ "$output" == *"${TEST_COMMAND_STDIN_DATA}"* ]]
  run bash -c "echo \"${TEST_SERVICE_COMMAND_STDIN_DATA}\" | ${DRAKY} ${TEST_SERVICE_COMMAND_NAME}"
  [[ "$output" == *"${TEST_SERVICE_COMMAND_MESSAGE}"* ]]
  [[ "$output" == *"${TEST_SERVICE_COMMAND_STDIN_DATA}"* ]]
}