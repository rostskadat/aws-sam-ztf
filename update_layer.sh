#!/usr/bin/env bash

PYTHON_VERSION=3.6

VENV_PATH=~/.local/share/virtualenvs/aws-ztf-jXF64ro3
[ -d "${VENV_PATH}" ] || virtualenv -p /usr/bin/python3.6 "${VENV_PATH}"
source $VENV_PATH/bin/activate

# You should make sure that the version of the boto3 and botocore is set
# according to https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
# These dependencies can be installed in the virtual environment
pip install botocore==1.15.22 boto3==1.12.22

# Install the application's dependencies into a specific folder to prepare for
# creating the layer... This needs to be executed before the sam build is
# called
PYTHON_ROOT_DIR="dependencies/ZTFRuntime"
PYTHON_TARGET_DIR="dependencies/ZTFRuntime/python"
pip3 install --requirement ${PYTHON_ROOT_DIR}/requirements.txt --upgrade --target=${PYTHON_TARGET_DIR}
find ${PYTHON_TARGET_DIR} -type d -name __pycache__ -exec rm -rf {} \; 2> /dev/null

echo "Final size is:"
du -h ${PYTHON_TARGET_DIR} --max-depth=1 | grep -v dist-info
