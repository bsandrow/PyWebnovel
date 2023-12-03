#!/bin/bash

if [ "$1" = "live" ]; then
    shift
    exec poetry run pytest -m "live" "$@"
else
    exec poetry run pytest -m "not live" "$@"
fi
