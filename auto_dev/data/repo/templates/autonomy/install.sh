#! /bin/bash
set -e
unset VIRTUAL_ENV 

poetry -v run echo "Installing dependencies"


OS=$(uname)
if [ "$OS" = "Darwin" ]; then
    CACHE_DIR="/Users/$(whoami)/Library/Caches/pypoetry/virtualenvs"
else
    CACHE_DIR="/home/$(whoami)/.cache/pypoetry/virtualenvs"
fi

executable=$(echo $(echo $CACHE_DIR/$(poetry env list |head -n 1| awk '{print $1}'))/bin/pip)
echo "Executing using :${executable}"
echo "Installing host dependencies"

# we need to check if the python version is <3.11
# if it is, we need to install cython<3.0.0

python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

# we cast to float to be able to compare
python_version=$(echo $python_version | awk '{print $1+0.0}')

if (( $(echo "$python_version < 3.11" |bc -l) )); then
    echo "Python version is <3.11, installing cython<3.0.0"
    ${executable} install 'cython<3.0.0' pyyaml==5.4.1 --no-build-isolation -v 
else
    echo "Python version is >=3.11, continuing"
fi

echo "Done installing host dependencies"
poetry install
poetry run aea init --remote --author eighballer
echo "Done installing dependencies"
