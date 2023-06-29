SHORT_NAME = draky
NAME = ghcr.io/draky-dev/${SHORT_NAME}
# Let's handle situation where VERSION is passed as empty. That'll allow us to simplify the pipeline.
ifndef VERSION
	override VERSION = local-build
endif

DIST_PATH = ./dist
DIST_BIN_PATH = ${DIST_PATH}/bin

# Version processed.
VER = $$(echo ${VERSION} | sed 's/^v//g')

.PHONY: $(MAKECMDGOALS)

install_build_dependencies_apk:
	apk add bash gettext

build:
	[ ! -d "${DIST_PATH}" ] || rm -r ${DIST_PATH}
	docker buildx build -f ./Dockerfile --rm -t ${NAME}:${VER} .
	mkdir -p ${DIST_BIN_PATH}
	docker save -o ${DIST_PATH}/${SHORT_NAME}-${VER}.image.tar ${NAME}:${VER}
	TEMPLATE_DRAKY_VERSION=${VER} TEMPLATE_DRAKY_NAME=${NAME} ./bin/template-renderer.sh -t ./bin/templates/draky.template -o ${DIST_BIN_PATH}/draky
	find ${DIST_BIN_PATH} -type f -exec chmod 755 {} \;

test:
	docker run -t --rm ${NAME}:${VER} dk-lint
	docker run -t --rm ${NAME}:${VER} dk-test

cleanup:
	docker rmi "${NAME}:${VER}"
