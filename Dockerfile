FROM alpine:3.18.0

ENV DK_PATH=/opt/dk-core
ENV DK_PATH_BIN="${DK_PATH}/bin"

ENV PATH="${PATH}:${DK_PATH_BIN}"

COPY core ${DK_PATH}

RUN apk add --no-cache \
    bash \
    docker-cli \
    docker-cli-compose \
    python3 \
    py3-dotenv \
    py3-yaml \
    py3-colorama

VOLUME '/global-config' '/opt/dk-core'

CMD ["sleep", "86400"]
