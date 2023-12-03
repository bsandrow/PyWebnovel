#!/bin/bash

function run_pytest() {
    exec poetry run pytest "$@"
}


#
# Run only the tests marked as "live"
#
if [ "$1" = "live" ]; then
    shift
    run_pytest -m "live" "$@"

#
# Run all tests
#
elif [ "$1" = "all" ]; then
    shift
    run_pytest "$@"

#
# Run only tests that are _not_ marked as "live"
#
else
    run_pytest -m "not live" "$@"
fi
