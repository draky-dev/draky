FROM alpine:3.18.0

ENV DK_PATH=/opt/dk-core
ENV DK_PATH_BIN="${DK_PATH}/bin"

ENV PATH="${PATH}:${DK_PATH_BIN}"

COPY core ${DK_PATH}

RUN apk add --no-cache \
    docker-cli \
    docker-cli-compose \
    python3 \
    py3-dotenv \
    py3-yaml \
    py3-colorama \
    py3-pylint \
    py3-pytest

VOLUME '/global-config' '/opt/dk-core'

CMD ["sleep", "86400"]
