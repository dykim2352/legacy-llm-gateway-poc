from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path", "status_code"],
)

LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM provider requests.",
    ["endpoint", "provider", "status"],
)

LLM_REQUEST_DURATION_SECONDS = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds.",
    ["endpoint", "provider", "status"],
)

LLM_STREAM_TOKENS_TOTAL = Counter(
    "llm_stream_tokens_total",
    "Total number of streamed LLM token chunks.",
    ["provider"],
)

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total number of cache hits.",
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total number of cache misses.",
)

AUDIT_EVENTS_TOTAL = Counter(
    "audit_events_total",
    "Total number of audit events stored.",
    ["event_type", "success"],
)

WEBSOCKET_CONNECTIONS_TOTAL = Counter(
    "websocket_connections_total",
    "Total number of accepted WebSocket connections.",
    ["path"],
)
