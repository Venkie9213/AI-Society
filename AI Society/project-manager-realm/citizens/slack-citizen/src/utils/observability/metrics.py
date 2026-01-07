"""Prometheus metrics definition."""

from prometheus_client import Counter, Histogram

# Slack metrics
slack_messages_received = Counter(
    "slack_messages_received_total",
    "Total number of Slack messages received",
    ["tenant_id", "channel_type"],
)

slack_messages_processing_duration = Histogram(
    "slack_messages_processing_seconds",
    "Time spent processing Slack messages",
    ["tenant_id"],
)

slack_api_calls = Counter(
    "slack_api_calls_total",
    "Total number of Slack API calls",
    ["tenant_id", "endpoint", "status"],
)

slack_api_errors = Counter(
    "slack_api_errors_total",
    "Total number of Slack API errors",
    ["tenant_id", "error_type"],
)

# Kafka metrics
kafka_messages_published = Counter(
    "kafka_messages_published_total",
    "Total number of messages published to Kafka",
    ["tenant_id", "topic"],
)

kafka_messages_consumed = Counter(
    "kafka_messages_consumed_total",
    "Total number of messages consumed from Kafka",
    ["tenant_id", "topic"],
)

event_processing_duration = Histogram(
    "event_processing_seconds",
    "Time spent processing events",
    ["tenant_id", "event_type"],
)
