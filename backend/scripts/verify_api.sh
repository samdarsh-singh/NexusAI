#!/bin/bash

BASE_URL="http://localhost:8000"

echo "1. Checking System Health..."
curl -s "$BASE_URL/" | grep "Job Aggregator API is running" && echo "✅ System is UP" || echo "❌ System is DOWN"

echo "\n2. Triggering Ingestion..."
# Using the mock scraper query
INGEST_RES=$(curl -s -X POST "$BASE_URL/api/v1/jobs/ingest?query=Python&location=Remote")
echo "Response: $INGEST_RES"

echo "\n3. Waiting for worker to process..."
sleep 5

echo "\n4. Listing Jobs..."
JOBS=$(curl -s "$BASE_URL/api/v1/jobs/")
echo "Jobs Found: $(echo $JOBS | grep -o "id" | wc -l)"

echo "\n5. Done."
