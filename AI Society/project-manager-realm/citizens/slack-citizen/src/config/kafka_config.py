"""Kafka configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaConfig(BaseSettings):
    """Kafka messaging configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Comma-separated list of Kafka broker addresses",
    )
    kafka_topic_prefix: str = Field(
        default="project-manager",
        description="Prefix for all Kafka topics",
    )
    kafka_consumer_group_id: str = Field(
        default="slack-citizen-consumer",
        description="Kafka consumer group ID",
    )
    kafka_auto_create_topics: bool = Field(
        default=True,
        description="Automatically create Kafka topics if they don't exist",
    )

    @property
    def kafka_servers_list(self) -> list[str]:
        """Parse Kafka bootstrap servers into a list."""
        return [s.strip() for s in self.kafka_bootstrap_servers.split(",")]

    def get_kafka_topic(self, topic_name: str) -> str:
        """Generate full Kafka topic name with prefix."""
        return f"{self.kafka_topic_prefix}.{topic_name}"
