#!/usr/bin/env bash
set -euo pipefail

API="${API_URL:?set API_URL}"
FE="${FRONTEND_URL:?set FRONTEND_URL}"

echo "-> /health"
curl -fsS "$API/health" | jq -e '.status == "ok"' >/dev/null

echo "-> /users/me unauthenticated"
test "$(curl -s -o /dev/null -w '%{http_code}' "$API/users/me")" = "401"

echo "-> /emails unauthenticated"
test "$(curl -s -o /dev/null -w '%{http_code}' "$API/emails")" = "401"

echo "-> frontend root"
code=$(curl -s -o /dev/null -w '%{http_code}' "$FE")
test "$code" = "200" || test "$code" = "307" || test "$code" = "308"

echo "smoke ok"
