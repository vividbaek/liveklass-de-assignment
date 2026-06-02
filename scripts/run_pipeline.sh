#!/usr/bin/env bash
set -euo pipefail

docker compose build app
docker compose up -d postgres

docker compose run --rm app python -m src.main

docker exec -i liveklass-postgres psql \
  -U liveklass \
  -d liveklass \
  < sql/analysis_queries.sql

docker compose run --rm \
  -v "$PWD/charts:/app/charts" \
  app python -m src.visualize

echo "Pipeline completed. Generated charts are available in ./charts."
