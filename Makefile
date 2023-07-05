SHORT_NAME = draky
NAME = ghcr.io/draky-dev/${SHORT_NAME}
# Let's handle situation where VERSION is passed as empty. That'll allow us to simplify the pipeline.
ifndef VERSION
	override VERSION = local-build
endif

ROOT = $(shell pwd -P)

CORE_PATH = ${ROOT}/core
CORE_BIN_PATH = ${CORE_PATH}/bin
DIST_PATH = ${ROOT}/dist
DIST_BIN_PATH = ${DIST_PATH}/bin
DRAKY_BIN_PATH = ${DIST_BIN_PATH}/draky
TESTS_PATH = ${ROOT}/tests

# Version processed.
VER = $(shell echo ${VERSION} | sed 's/^v//g')

TEST_CONTAINER_NAME = ${SHORT_NAME}-test-environment
TEST_ENVIRONMENT_IMAGE = ghcr.io/draky-dev/${SHORT_NAME}-generic-testing-environment:1.0.0
TEST_CONTAINER_DRAKY_SOURCE_PATH = /opt/${SHORT_NAME}

.ONESHELL:
.PHONY: $(MAKECMDGOALS)
SHELL = /bin/bash

install_build_dependencies_alpine:
	apk add bash gettext

build:
	[ ! -d "${DIST_PATH}" ] || rm -r ${DIST_PATH}
	docker buildx build -f ${ROOT}/Dockerfile --rm -t ${NAME}:${VER} .
	mkdir -p ${DIST_BIN_PATH}
	docker save -o ${DIST_PATH}/${SHORT_NAME}-${VER}.image.tar ${NAME}:${VER}
	TEMPLATE_DRAKY_VERSION=${VER} TEMPLATE_DRAKY_NAME=${NAME} ./bin/template-renderer.sh -t ./bin/templates/draky.template -o ${DIST_BIN_PATH}/draky
	find ${DIST_BIN_PATH} -type f -exec chmod 755 {} \;

build-test:
	cd ${ROOT}/tests
	docker buildx build -f ./Dockerfile --rm -t ${TEST_ENVIRONMENT_IMAGE} .

test-core:
	ls -la .
	docker run \
	--name ${TEST_CONTAINER_NAME} \
	-t \
	--rm \
	-v "${ROOT}:/opt/${SHORT_NAME}" \
	${TEST_ENVIRONMENT_IMAGE} \
	${TEST_CONTAINER_DRAKY_SOURCE_PATH}/tests/bin/core-tests.sh

test-functional:
	function tearDown() { \
		docker stop ${TEST_CONTAINER_NAME}; \
		docker rm ${TEST_CONTAINER_NAME}; \
	}
	trap tearDown EXIT
	docker run \
	--name "${TEST_CONTAINER_NAME}" \
	--privileged \
	-d \
	--health-cmd "[ -S /var/run/docker.sock ]" \
	--health-interval 1s \
	--health-retries 10 \
	-v "${ROOT}:/opt/${SHORT_NAME}" \
	${TEST_ENVIRONMENT_IMAGE}
	until [ "`docker inspect -f {{.State.Health.Status}} ${TEST_CONTAINER_NAME}`" == "healthy" ]; do \
        sleep 1; \
        if [ "`docker inspect -f {{.State.Health.Status}} ${TEST_CONTAINER_NAME}`" == "unhealthy" ]; then \
          echo "Container ${TEST_CONTAINER_NAME} didn't get healthy."; \
          exit 1; \
        fi; \
    done
	docker exec -t ${TEST_CONTAINER_NAME} /bin/bash -c "DRAKY_SOURCE_PATH=${TEST_CONTAINER_DRAKY_SOURCE_PATH} ${TEST_CONTAINER_DRAKY_SOURCE_PATH}/tests/bin/functional-tests.sh"

test-lint:
	docker run \
	--name ${TEST_CONTAINER_NAME} \
	-t \
	--rm \
	-v "${ROOT}:/opt/${SHORT_NAME}" \
	${TEST_ENVIRONMENT_IMAGE} \
	${TEST_CONTAINER_DRAKY_SOURCE_PATH}/tests/bin/lint.sh

cleanup:
	docker rmi "${NAME}:${VER}"
