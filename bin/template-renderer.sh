#!/usr/bin/env bash

while getopts ":ht:o:" opt; do
  case $opt in
    t)
      TEMPLATE="${OPTARG}"
    ;;
    o)
      TEMPLATE_OUTPUT="${OPTARG}"
    ;;
    h)
      printf "%s\n" "  Usage: $0 <flags>"
      printf "%s\n" ""
      printf "%s\n" "  Available flags:"
      printf "%s\n" "  -t    Path to template to render."
      printf "%s\n" "  -o    Output path."
      printf "%s\n" "  -h    This help."
      exit 0;
    ;;

    \?)
      echo "Unknown flag has been used: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

TEMPLATE_VAR_PREFIX="TEMPLATE_"

shift "$((OPTIND-1))"

: ${TEMPLATE:?"You need to provide a template with -t flag."}
: ${TEMPLATE_VAR_PREFIX:?"You need to provide a prefix of variables being replaced with -p flag."}

ARRAY=()
while read p; do
  ARRAY+=("\$${p}")
done < <(env | sed -rn "s/(${TEMPLATE_VAR_PREFIX}\w+)=.*/\1/p")

ALL_TEMPLATE_VARIABLES=$(IFS=, ; echo "${ARRAY[*]}")

echo "$(envsubst "${ALL_TEMPLATE_VARIABLES}" < "${TEMPLATE}")" > "${TEMPLATE_OUTPUT}"
