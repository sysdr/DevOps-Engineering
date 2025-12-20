#!/usr/bin/env python3
"""Kafka producer for streaming events"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

class EventProducer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        
    def generate_event(self):
        """Generate realistic user event"""
        event_types = ['click', 'view', 'purchase', 'add_to_cart']
        
        event = {
            'event_id': f"evt_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            'user_id': f"user_{random.randint(1, 10000)}",
            'event_type': random.choice(event_types),
            'timestamp': datetime.now().isoformat(),
            'amount': round(random.uniform(5.0, 500.0), 2) if random.random() > 0.7 else 0,
            'location': {'lat': random.uniform(-90, 90), 'lon': random.uniform(-180, 180)},
            'device': random.choice(['mobile', 'desktop', 'tablet']),
            'session_id': f"session_{random.randint(1000, 5000)}"
        }
        return event
    
    def send_event(self, topic, event):
        """Send event to Kafka topic"""
        try:
            future = self.producer.send(topic, event)
            record_metadata = future.get(timeout=10)
            return True
        except KafkaError as e:
            print(f"Error sending event: {e}")
            return False
    
    def produce_stream(self, topic='raw-events', rate=10, duration=60):
        """Produce continuous stream of events"""
        print(f"Starting event stream to topic '{topic}' at {rate} events/sec")
        
        start_time = time.time()
        event_count = 0
        
        try:
            while time.time() - start_time < duration:
                event = self.generate_event()
                if self.send_event(topic, event):
                    event_count += 1
                    if event_count % 100 == 0:
                        print(f"Sent {event_count} events")
                
                time.sleep(1.0 / rate)
                
        except KeyboardInterrupt:
            print("\nStopping producer...")
        finally:
            self.producer.flush()
            self.producer.close()
            
        elapsed = time.time() - start_time
        print(f"\nProduced {event_count} events in {elapsed:.1f}s ({event_count/elapsed:.1f} events/sec)")

if __name__ == '__main__':
    producer = EventProducer()
    producer.produce_stream(rate=50, duration=300)  # 50 events/sec for 5 minutes
