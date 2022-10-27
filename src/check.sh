#!/bin/bash
#
# A bash script to run pep8 style checking and type checking.
#
# Usage: ./check.sh or ./check.sh [FILES...]

readonly ORANGE='\033[0;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m' # No Color

printf "[ =======================  ${ORANGE}pycodestyle${NC}  ======================= ]\n"
pycodestyle --exclude venv/,__pycache__/ "$@"

printf "\n[ =======================  ${RED}  pyright  ${NC}  ======================= ]\n"
# Unbuffer to preserve colors and use sed to ignore the initial noisy logs.
unbuffer pyright "$@" | sed -E '0,/^pyright [[:digit:]]+\.[[:digit:]]/d'
