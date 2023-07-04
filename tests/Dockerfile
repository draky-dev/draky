FROM docker:24.0.2-dind-alpine3.18

ENV DRAKY_SOURCE_PATH /opt/draky
ENV DRAKY_DIST_PATH ${DRAKY_SOURCE_PATH}/dist

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

VOLUME ${DRAKY_SOURCE_PATH}
