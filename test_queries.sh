#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-http://localhost:8000}

echo "Refreshing datasource..."
curl -s -X POST "$BASE_URL/datasource/refresh" | jq . >/dev/null || true

echo "\n--- Revenue last 30 days ---"
curl -s -X POST "$BASE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"revenue last 30 days","filters":{},"ai_assist":false}' | jq .

echo "\n--- Top 5 products ---"
curl -s -X POST "$BASE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"top 5 products","filters":{},"ai_assist":false}' | jq .

echo "\n--- Orders for CID 1001 ---"
curl -s -X POST "$BASE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"orders for CID 1001","filters":{},"ai_assist":false}' | jq .

echo "\n--- Order details IID 2001 ---"
curl -s -X POST "$BASE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"order details IID 2001","filters":{},"ai_assist":false}' | jq .

echo "Done."
