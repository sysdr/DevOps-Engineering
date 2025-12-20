#!/usr/bin/env python3
"""Flink-style stream processor for validation and aggregation"""

import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from kafka import KafkaConsumer, KafkaProducer
from threading import Thread, Lock

class StreamProcessor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'raw-events',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='stream-processor'
        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Windowed state for aggregations
        self.window_state = defaultdict(lambda: {'count': 0, 'amount': 0, 'events': deque()})
        self.state_lock = Lock()
        self.window_size = 60  # 60 second windows
        
        # Metrics
        self.processed_count = 0
        self.validated_count = 0
        self.failed_count = 0
        
    def validate_event(self, event):
        """Validate event schema and values"""
        required_fields = ['event_id', 'user_id', 'event_type', 'timestamp']
        
        # Check required fields
        for field in required_fields:
            if field not in event:
                return False, f"Missing required field: {field}"
        
        # Validate event_type
        valid_types = ['click', 'view', 'purchase', 'add_to_cart']
        if event['event_type'] not in valid_types:
            return False, f"Invalid event_type: {event['event_type']}"
        
        # Validate timestamp
        try:
            event_time = datetime.fromisoformat(event['timestamp'])
            if event_time > datetime.now() + timedelta(minutes=5):
                return False, "Timestamp is in future"
        except:
            return False, "Invalid timestamp format"
        
        # Validate amount
        if 'amount' in event and event['amount'] < 0:
            return False, "Negative amount"
        
        return True, "Valid"
    
    def aggregate_windowed(self, event):
        """Aggregate events in sliding windows"""
        with self.state_lock:
            user_id = event['user_id']
            now = time.time()
            
            # Add event to window
            state = self.window_state[user_id]
            state['count'] += 1
            state['amount'] += event.get('amount', 0)
            state['events'].append((now, event))
            
            # Remove old events outside window
            cutoff = now - self.window_size
            while state['events'] and state['events'][0][0] < cutoff:
                old_time, old_event = state['events'].popleft()
                state['count'] -= 1
                state['amount'] -= old_event.get('amount', 0)
            
            # Create aggregation
            aggregation = {
                'user_id': user_id,
                'window_start': datetime.fromtimestamp(now - self.window_size).isoformat(),
                'window_end': datetime.now().isoformat(),
                'event_count': state['count'],
                'total_amount': round(state['amount'], 2),
                'avg_amount': round(state['amount'] / state['count'], 2) if state['count'] > 0 else 0,
                'event_types': list(set(e['event_type'] for _, e in state['events']))
            }
            
            return aggregation
    
    def process_stream(self):
        """Main processing loop"""
        print("Starting stream processor...")
        print(f"Consuming from: raw-events")
        print(f"Window size: {self.window_size}s")
        
        try:
            for message in self.consumer:
                event = message.value
                self.processed_count += 1
                
                # Validate event
                is_valid, reason = self.validate_event(event)
                
                if is_valid:
                    self.validated_count += 1
                    
                    # Send to validated topic
                    self.producer.send('validated-events', event)
                    
                    # Compute aggregations
                    aggregation = self.aggregate_windowed(event)
                    self.producer.send('aggregated-events', aggregation)
                    
                else:
                    self.failed_count += 1
                    print(f"Validation failed: {reason}")
                
                # Print metrics every 100 events
                if self.processed_count % 100 == 0:
                    print(f"Processed: {self.processed_count}, Valid: {self.validated_count}, "
                          f"Failed: {self.failed_count}, Rate: {self.validated_count/self.failed_count if self.failed_count > 0 else 0:.2f}")
                          
        except KeyboardInterrupt:
            print("\nStopping processor...")
        finally:
            self.consumer.close()
            self.producer.close()

if __name__ == '__main__':
    processor = StreamProcessor()
    processor.process_stream()
