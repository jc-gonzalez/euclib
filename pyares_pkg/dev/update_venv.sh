#!/bin/bash

PYARES_DIR="~/pyares"
if [ -n "$1" ]; then
    PYARES_DIR=$1
fi

cd ${PYARES_DIR}
rm -rf build/
rm -rf dist/
rm -rf pyares.egg-info/
rm pyares/data/venv.zip

python3 setup.py bdist_wheel
cd dist/

pip install -U pyares-0.2.0-py3-none-any.whl
pip uninstall pandas -y

cd ${PYARES_DIR}/cluster_venv/
zip -qr ${PYARES_DIR}/pyares/data/venv.zip *

pip install pandas==0.20.3
