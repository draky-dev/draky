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
    py3-pip
RUN pip3 install -r "${DK_PATH}/dk/requirements.txt"

VOLUME '/global-config' '/opt/dk-core'

CMD ["sleep", "86400"]
