#!/bin/sh

# Wait for postgres
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Wait for mongo
echo "Waiting for mongo..."
while ! nc -z mongo 27017; do
  sleep 0.1
done
echo "MongoDB started"

# Wait for redis
echo "Waiting for redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

exec "$@"
