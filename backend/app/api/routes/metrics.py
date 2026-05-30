from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

router = APIRouter(tags=["system"])

HEALTH_REQUESTS_TOTAL = Counter(
    "llm_gateway_metrics_requests_total",
    "Total number of Prometheus metrics scrape responses served.",
)


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    HEALTH_REQUESTS_TOTAL.inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
