FROM docker:27.4.1-dind-alpine3.21

ENV DRAKY_SOURCE_PATH=/opt/draky
ENV DRAKY_DIST_PATH=${DRAKY_SOURCE_PATH}/dist
ENV TESTUSER_NAME=testuser
ENV TESTUSER_UID=1000

# Note that the test environment needs to have the same python libraries as the draky-core, to avoid pylint's
# "import-error" errors. Thanks to that, we don't need to keep pylint and pytest in the draky-core image.
RUN apk add bash \
            ncurses \
            bats \
            python3 \
            py3-pylint \
            py3-pytest \
            py3-dotenv \
            py3-yaml \
            py3-colorama

RUN addgroup "$TESTUSER_NAME" \
 && adduser --disabled-password --ingroup "$TESTUSER_NAME" --uid "$TESTUSER_UID" -s /bin/bash "$TESTUSER_NAME" \
 && addgroup "$TESTUSER_NAME" docker

HEALTHCHECK --interval=1s --retries=10 --timeout=10s CMD bash -c '[ -S /var/run/docker.sock ] || exit 1'

ENTRYPOINT ["dockerd-entrypoint.sh"]

VOLUME ${DRAKY_SOURCE_PATH}
