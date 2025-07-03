#!/bin/bash
# Run all tests with coverage, ensuring PYTHONPATH is set to project root

# Stop and remove any existing test Postgres DB container for a clean start
if [ -f docker-compose.test.yml ]; then
  echo "Stopping and removing any existing test database container..."
  docker-compose -f docker-compose.test.yml down
  echo "Starting test database with docker-compose.test.yml..."
  docker-compose -f docker-compose.test.yml up -d
  # Wait for DB to be ready (simple check, can be improved)
  echo "Waiting for test database to be ready..."
  for i in {1..10}; do
    docker-compose -f docker-compose.test.yml exec -T test-db pg_isready && break
    sleep 2
  done
fi

export PYTHONPATH=.
pytest --cov=app --cov-report=term-missing "$@"