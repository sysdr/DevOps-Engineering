import json
import asyncio
from kafka import KafkaProducer
from kafka.errors import KafkaError
from shared.models.events import DomainEvent
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class EventPublisher:
    def __init__(self, kafka_servers: list = ["localhost:9092"]):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda x: json.dumps(x, cls=DateTimeEncoder).encode('utf-8'),
            key_serializer=lambda x: x.encode('utf-8') if x else None
        )

    async def publish_event(self, topic: str, event: DomainEvent):
        try:
            event_data = event.dict()
            future = self.producer.send(
                topic,
                key=event.aggregate_id,
                value=event_data
            )
            
            # Wait for message to be sent
            record_metadata = future.get(timeout=10)
            logger.info(f"Event published to topic {topic}: {event.event_type}")
            return record_metadata
            
        except KafkaError as e:
            logger.error(f"Failed to publish event: {e}")
            raise

    def close(self):
        self.producer.close()
