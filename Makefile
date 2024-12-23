SHORT_NAME = draky
NAME = ghcr.io/draky-dev/${SHORT_NAME}
VERSION_DEFAULT = local-build
# Let's handle situation where VERSION is passed as empty. That'll allow us to simplify the pipeline.
ifndef VERSION
	override VERSION = ${VERSION_DEFAULT}
endif

# Filter functional tests. Set this variable to regex matching the names of tests you want to run.
FFILTER =

ROOT = $(shell pwd -P)

CORE_PATH = ${ROOT}/core
CORE_BIN_PATH = ${CORE_PATH}/bin
DIST_PATH = ${ROOT}/dist
DIST_BIN_PATH = ${DIST_PATH}/bin
DRAKY_BIN_PATH = ${DIST_BIN_PATH}/draky
TESTS_PATH = ${ROOT}/tests

TESTUSER_NAME = testuser

PLATFORMS=linux/arm64,linux/amd64

# Version processed.
VER = $(shell echo ${VERSION} | sed 's/^v//g')

TEST_CONTAINER_NAME = ${SHORT_NAME}-test-environment
TEST_ENVIRONMENT_VERSION_DEFAULT = 1.1.1
TEST_ENVIRONMENT_VERSION = ${TEST_ENVIRONMENT_VERSION_DEFAULT}
TEST_ENVIRONMENT_IMAGE = ghcr.io/draky-dev/${SHORT_NAME}-generic-testing-environment:${TEST_ENVIRONMENT_VERSION}
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
	IMAGE_PATH=${DIST_PATH}/${SHORT_NAME}-${VER}.image.tar
	docker save -o $${IMAGE_PATH} ${NAME}:${VER}
	chmod a+r $${IMAGE_PATH}
	TEMPLATE_DRAKY_VERSION=${VER} TEMPLATE_DRAKY_NAME=${NAME} ./bin/template-renderer.sh -t ./bin/templates/draky.template -o ${DIST_BIN_PATH}/draky
	find ${DIST_BIN_PATH} -type f -exec chmod 755 {} \;
	[ "${VERSION}" == "${VERSION_DEFAULT}" ] || echo "When deploying the new release, remember to push the image first!"

build-test:
	cd ${ROOT}/tests
	docker buildx build -f ./Dockerfile --rm -t ${TEST_ENVIRONMENT_IMAGE} .

test-core:
	docker run \
	--name ${TEST_CONTAINER_NAME} \
	-t \
	--rm \
	-v "${ROOT}:/opt/${SHORT_NAME}" \
	${TEST_ENVIRONMENT_IMAGE} \
	${TEST_CONTAINER_DRAKY_SOURCE_PATH}/tests/bin/core-tests.sh

test-functional:
	function tearDown() { \
		docker stop ${TEST_CONTAINER_NAME} > /dev/null
		docker rm ${TEST_CONTAINER_NAME} > /dev/null
	}
	trap tearDown EXIT
	docker run \
	--name "${TEST_CONTAINER_NAME}" \
	--privileged \
	-d \
	-v "${ROOT}:/opt/${SHORT_NAME}" \
	${TEST_ENVIRONMENT_IMAGE}
	until [ "`docker inspect -f {{.State.Health.Status}} ${TEST_CONTAINER_NAME}`" == "healthy" ]; do
		sleep 1
		if [ "`docker inspect -f {{.State.Health.Status}} ${TEST_CONTAINER_NAME}`" == "unhealthy" ]; then
		echo "Container ${TEST_CONTAINER_NAME} didn't get healthy."
			exit 1
		fi
	done
	docker exec -t --user ${TESTUSER_NAME} ${TEST_CONTAINER_NAME} /bin/bash -c "TEST_FILTER='${FFILTER}' DRAKY_SOURCE_PATH=${TEST_CONTAINER_DRAKY_SOURCE_PATH} ${TEST_CONTAINER_DRAKY_SOURCE_PATH}/tests/bin/functional-tests.sh"

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

deploy-image:
	if [ "${VERSION}" == "${VERSION_DEFAULT}" ]; then \
  	  echo "Cannot deploy the '${VERSION_DEFAULT}' version"; \
  	  exit; \
	fi;
	docker buildx create --use --name docker-container
	docker buildx build -f ${ROOT}/Dockerfile --provenance=false --rm --platform ${PLATFORMS} -t ${NAME}:${VER} --output "type=registry" .
	docker buildx rm docker-container

deploy-testing-image:
	set -e
	if [ "${TEST_ENVIRONMENT_VERSION}" == "${TEST_ENVIRONMENT_VERSION_DEFAULT}" ]; then \
  	  echo "Cannot deploy the '${TEST_ENVIRONMENT_VERSION_DEFAULT}' version because it's the default one. You need to pass a new version by overriding the TEST_ENVIRONMENT_VERSION variable to be able to deploy it."; \
  	  exit; \
	fi;
	docker buildx create --use --name docker-container
	docker buildx build -f ${ROOT}/tests/Dockerfile --provenance=false --rm --platform ${PLATFORMS} -t ${TEST_ENVIRONMENT_IMAGE} --output "type=registry" .
	docker buildx rm docker-container
	echo "Push complete. Remember to change the TEST_ENVIRONMENT_VERSION_DEFAULT value to the new one."
