#!/bin/bash
#
# Build DX3_DSX_ESP firmware for ESP32-S3 in DX3 DSX Touch (CP) or ISX (IU).
#
# sudo apt install python-rdflib-tools python3-rdflib python3-rdflib-sqlalchemy
# sudo apt install graphviz python3-pydot
#

# Where to get the Modbus/RTU parameter mapping.
MODBUS_API_SYNTAX="../clage_modbus_tab.csv"

###########################################################
# Command Line Parsing

#######################
# Give advice

usage() {
    echo "usage: $0 [-b] [-c] [-d] [-v] ..."
    echo " -b flag to build"
    echo " -c flag to clean"
    echo " -d flag if distribution clean shall be performed."
    echo " -e flag if all examples shall be executed (for testing)."
    echo " -v flag for verbose output"
    echo " -z flag to zero this project by ERASING ANY LOCAL CHANGE (includes -d)."
    exit
}

#######################
# Setup and Defaults

DO_BUILD=false
DO_CLEAN=false
DO_DISTCLEAN=false
DO_RUN_EXAMPLES=false
DO_VERBOSE=false
DO_ZERO_ALL=false
GIT_HASH=$(git show --oneline -s | sed 's/ .*$//g')

#######################
# Read command line options (if any)

while getopts "bcdevz?h" opt; do
    case "${opt}" in
    b) DO_BUILD=true ;;
    c) DO_CLEAN=true ;;
    d) DO_DISTCLEAN=true ;;
    e) DO_RUN_EXAMPLES=true ;;
    v) DO_VERBOSE=true ;;
    z) DO_ZERO_ALL=true ;;
    ? | h) usage ;;
    *) usage ;;
    esac
done
shift $#

#######################
# Dependencies

###########################################################
# Functions & Util

# For debug
go() {
    if $DO_VERBOSE; then
        echo "########################################"
        echo "##> $@"
        echo "########################################"
    else
        echo "##> $@"
    fi
    if "$@"; then
        if $DO_VERBOSE; then
            echo "##> DONE"
        fi
    else
        echo "##### FAILED ##### ($@)"
        exit
    fi
}

#######################
# Cleanup

do_clean() {
    rm -rf ./build ./__pycache__
    rm -f *.ttl *.svg
}

do_distclean() {
    do_clean
    rm -f catalog-*.xml
}

do_zero_all() {
    do_distclean
    # Remove all changes compared to last commit checked out.
    git reset --hard
    # Remove all extra files not managed by git and all explicitly ignored files.
    git clean -dfx
    # Do the same for all submodules.
    git submodule foreach --recursive 'git reset --hard && git clean -dfx'
}

#######################
# Build/Create

do_build() {
    # Compile python (testing)
    python3 -m py_compile clage_modbus_ttl.py
    # Create turtle file from modbus table.
    ./clage_modbus_ttl.py
    # Check by parsing with rdflib
    python3 -c "from rdflib import Graph; g=Graph(); g.parse('clage_modbus_tab.ttl', format='turtle'); print(len(g))"
    # Create SVG diagram from turtle file
    # ./ttl_to_svg.py clage_modbus_tab.ttl
}

do_run_examples() {
    if [ ! -r clage_modbus_tab.ttl ]; then
        echo "Do build clage_modbus_tab.ttl before."
        exit 1
    fi
    # Loop over all examples
    for e in ./*_example_*.py; do
        echo "########## Example: $e"
        $e
        echo
        echo
    done
}

###########################################################
# Actions and Order

if $DO_CLEAN; then
    do_clean
fi

if $DO_DISTCLEAN; then
    do_distclean
fi

if $DO_ZERO_ALL; then
    do_zero_all
fi

if $DO_BUILD; then
    do_build
fi

if $DO_RUN_EXAMPLES; then
    do_run_examples
fi

#EOF
