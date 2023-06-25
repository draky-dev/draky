NAME = draky.dev/draky
# Let's handle situation where VERSION is passed as empty. That'll allow us to simplify the pipeline.
ifndef VERSION
	override VERSION = local-build
endif

DIST_PATH = ./dist
DIST_BIN_PATH = ${DIST_PATH}/bin

build:
	[ ! -d "${DIST_PATH}" ] || rm -r ${DIST_PATH}
	docker buildx build -f ./Dockerfile --rm -t ${NAME}:${VERSION} .
	mkdir -p ${DIST_BIN_PATH}
	docker save -o ${DIST_PATH}/image.tar ${NAME}:${VERSION}
	TEMPLATE_DRAKY_VERSION=${VERSION} TEMPLATE_DRAKY_NAME=${NAME} ./bin/template-renderer.sh -t ./bin/templates/draky.template -o ${DIST_BIN_PATH}/draky
	find ${DIST_BIN_PATH} -type f -exec chmod 755 {} \;

build-test:         build test
build-test-cleanup: build-test cleanup

test:
	docker run --rm ${NAME}:${VERSION} dk-lint
	docker run --rm ${NAME}:${VERSION} dk-test

cleanup:
	docker rmi "${NAME}:${VERSION}"
