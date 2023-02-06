#!/bin/bash
# ref: https://packaging.python.org/en/latest/tutorials/packaging-projects/

BASE_DIR="$(dirname "$(readlink -f "$0")")"
PRJ_DIR="${BASE_DIR}/.."
DOC_DIR="${PRJ_DIR}/doc"
mkdir -p "${DOC_DIR}"

cd "${PRJ_DIR}"
python setup.py sdist bdist_wheel --universal # 源码和whl文件
twine check dist/* # python setup.py check -r -s
if [[ ${ret} -ne 0 ]]; then 
    echo -e E$(date +'%m%d %H:%M:%S.%6N' -u) "\033[31m" "run check error" "\033[0m"
    exit 1
fi
twine upload dist/* # config ~/.pypirc file

rm -rf build/ dist/ magic_maze.egg-info/
