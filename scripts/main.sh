#!/bin/bash
docker compose run --rm clipflow python -m clipflow.main --lang jp
docker compose run --rm clipflow python -m clipflow.main --lang en
