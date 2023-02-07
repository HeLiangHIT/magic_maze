#!/bin/bash
# ref: https://docs.python.org/3/library/pydoc.html

BASE_DIR="$(dirname "$(readlink -f "$0")")"
PRJ_DIR="${BASE_DIR}/.."
DOC_DIR="${PRJ_DIR}/doc"
mkdir -p "${DOC_DIR}"

cd "${PRJ_DIR}"
# python -m pydoc -b algorithm
python -m pydoc algorithm > "${DOC_DIR}/algorithm.txt"
python -m pydoc algorithm.map >> "${DOC_DIR}/algorithm.txt"
python -m pydoc algorithm.search >> "${DOC_DIR}/algorithm.txt"
python -m pydoc algorithm.generate >> "${DOC_DIR}/algorithm.txt"

