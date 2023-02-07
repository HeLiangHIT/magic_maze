#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "$0")")"
PRJ_DIR="${BASE_DIR}/.."

# 运行LLT用例
cd "${PRJ_DIR}"
function test_cmd(){
    func=$1
    ${func}
    if [ $? != 0 ]; then
        echo -e E$(date +'%m%d %H:%M:%S.%6N' -u) "\033[31m" "run cmd:${func} failed" "\033[0m"
        exit 1
    fi
}
test_cmd "python -m algorithm.map"
test_cmd "python -m algorithm.search"
test_cmd "python -m algorithm.generate"
