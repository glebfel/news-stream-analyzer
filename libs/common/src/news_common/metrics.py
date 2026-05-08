"""Prometheus metrics shared across services.

For HTTP services (api-gateway) the metrics are exposed via FastAPI route
`GET /metrics`. For background workers (collectors, processor, nlp_worker,
graph_builder) a lightweight HTTP server is started on a configurable port
through `start_metrics_server(port)`.
"""

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Collectors
posts_collected_total = Counter(
    "posts_collected_total",
    "Number of posts emitted by collectors before deduplication",
    labelnames=("source",),
)
collector_cycle_seconds = Histogram(
    "collector_cycle_seconds",
    "Duration of a single collector polling cycle",
    labelnames=("source",),
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300),
)
vk_api_calls_total = Counter(
    "vk_api_calls_total",
    "Number of HTTP calls to VK API by method and outcome",
    labelnames=("method", "outcome"),
)

# Processor
posts_dedup_total = Counter(
    "posts_dedup_total",
    "Posts seen by processor partitioned by deduplication outcome",
    labelnames=("outcome",),  # 'kept' | 'dup'
)
posts_indexed_total = Counter(
    "posts_indexed_total",
    "Posts written to OpenSearch raw_posts index",
)

# NLP
nlp_processed_total = Counter(
    "nlp_processed_total",
    "Number of normalized posts processed by NLP worker",
)
ner_entities_total = Counter(
    "ner_entities_total",
    "Entities extracted by the NER stage, partitioned by type",
    labelnames=("entity_type",),
)
sentiment_predictions_total = Counter(
    "sentiment_predictions_total",
    "Sentiment predictions partitioned by label",
    labelnames=("label",),
)
nlp_processing_seconds = Histogram(
    "nlp_processing_seconds",
    "Wall-clock duration of full NLP processing per post",
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10),
)
wikidata_cache_hits_total = Counter(
    "wikidata_cache_hits_total",
    "Wikidata lookups served from Redis cache",
)
wikidata_cache_misses_total = Counter(
    "wikidata_cache_misses_total",
    "Wikidata lookups that fell through to the remote API",
)

# Graph builder
graph_flush_total = Counter(
    "graph_flush_total",
    "Number of UNWIND flushes executed against Neo4j",
)
graph_flush_size = Histogram(
    "graph_flush_size",
    "Items flushed per UNWIND batch",
    labelnames=("kind",),  # 'entities' | 'relations'
    buckets=(1, 5, 10, 25, 50, 100, 200, 500, 1000),
)
graph_buffer_depth = Gauge(
    "graph_buffer_depth",
    "Current number of items waiting in the graph writer buffer",
    labelnames=("kind",),
)

# Service info
service_up = Gauge(
    "service_up",
    "1 if the service has started and registered metrics, else 0",
    labelnames=("service",),
)


def start_metrics_server(port: int, service: str) -> None:
    """Start a background Prometheus HTTP exporter on the given port."""
    start_http_server(port)
    service_up.labels(service=service).set(1)
