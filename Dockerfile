FROM alpine:3.23.0

ENV DK_PATH=/opt/dk-core
ENV DK_PATH_BIN="${DK_PATH}/bin"

ENV DK_CUSTOM_VENV="custom-venv"

COPY core ${DK_PATH}
COPY entrypoint.sh /entrypoint.sh

RUN apk add --no-cache \
    bash \
    docker-cli \
    docker-cli-compose \
    python3 \
    py3-pip
RUN python -m venv ${DK_CUSTOM_VENV} && \
  ${DK_CUSTOM_VENV}/bin/pip3 install -r "${DK_PATH}/dk/requirements.txt"

ENV PATH="/${DK_CUSTOM_VENV}/bin:${PATH}:${DK_PATH_BIN}"

VOLUME '/global-config' '/opt/dk-core'

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "86400"]
