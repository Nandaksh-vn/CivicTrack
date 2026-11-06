#!/bin/sh
# Trigger the escalation worker on demand (demo / drill).
# The canonical trigger is the token-protected POST /internal/escalations/run
# (Phase 11). Until that endpoint lands, invoke the worker function directly
# in the worker container — same code path the scheduler calls.
# Usage: ./scripts/trigger-escalation.sh
set -eu
echo "[trigger] running one escalation check in the worker container..."
docker compose exec worker python -c "from app.worker import run_escalation_check; run_escalation_check()"
echo "[trigger] recent worker logs:"
docker compose logs --tail=30 worker
# When Phase 11 is live, prefer:
#   curl -X POST http://localhost:8000/api/v1/internal/escalations/run \
#     -H "X-Internal-Token: $INTERNAL_TRIGGER_TOKEN"
