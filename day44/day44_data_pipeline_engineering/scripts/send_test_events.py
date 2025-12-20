#!/usr/bin/env python3
"""Send test events to Kafka"""

import sys
sys.path.append('..')
from kafka.producer import EventProducer

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Send test events to Kafka')
    parser.add_argument('--count', type=int, default=1000, help='Number of events to send')
    parser.add_argument('--rate', type=int, default=50, help='Events per second')
    args = parser.parse_args()
    
    producer = EventProducer()
    producer.produce_stream(rate=args.rate, duration=args.count/args.rate)
