import logging
import json
from pythonjsonlogger import jsonlogger
from datetime import datetime
import os

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['service'] = os.getenv('SERVICE_NAME', 'unknown')
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['thread'] = record.thread
        log_record['function'] = record.funcName

def setup_logger(service_name: str) -> logging.Logger:
    os.environ['SERVICE_NAME'] = service_name
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatting
    handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(service)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
