#!/usr/bin/env bash

set -e
set -x

# Build Docker images
docker compose up

# Run the test service, passing any arguments (e.g., for coverage report title)
docker compose run --rm test "$@"
