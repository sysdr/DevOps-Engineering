import os
import json
import yaml
from typing import Dict, List, Any
from datetime import datetime
from jinja2 import Template
import subprocess

class DocumentationGenerator:
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Template]:
        """Load documentation templates"""
        return {
            "architecture": Template("""
# System Architecture Documentation

## Overview
Generated on: {{ generation_date }}

## System Components
{% for component in components %}
### {{ component.name }}
- **Type**: {{ component.type }}
- **Description**: {{ component.description }}
- **Dependencies**: {{ component.dependencies | join(', ') }}
- **Health Check**: {{ component.health_check }}

{% endfor %}

## Service Dependencies
{{ dependency_graph }}

## Configuration
{% for config in configurations %}
### {{ config.name }}
```yaml
{{ config.content }}
```
{% endfor %}
            """),
            
            "runbook": Template("""
# Operational Runbook

## Emergency Procedures

### Service Down
1. Check service health endpoints
2. Review recent deployments
3. Check resource utilization
4. Examine error logs

### High Load
1. Enable auto-scaling
2. Check database performance
3. Review cache hit rates
4. Consider load shedding

## Monitoring & Alerting
{% for alert in alerts %}
### {{ alert.name }}
- **Condition**: {{ alert.condition }}
- **Severity**: {{ alert.severity }}
- **Response**: {{ alert.response }}

{% endfor %}

## Deployment Procedures
{{ deployment_steps }}

## Troubleshooting Guide
{{ troubleshooting_guide }}
            """),
            
            "api_docs": Template("""
# API Documentation

{% for endpoint in endpoints %}
## {{ endpoint.method }} {{ endpoint.path }}

**Description**: {{ endpoint.description }}

**Parameters**:
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}): {{ param.description }}
{% endfor %}

**Example Request**:
```json
{{ endpoint.example_request }}
```

**Example Response**:
```json
{{ endpoint.example_response }}
```

{% endfor %}
            """)
        }

    def generate_architecture_docs(self, config_dir: str) -> str:
        """Generate architecture documentation from configuration files"""
        components = self._discover_components(config_dir)
        configurations = self._load_configurations(config_dir)
        
        return self.templates["architecture"].render(
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            components=components,
            configurations=configurations,
            dependency_graph=self._generate_dependency_graph(components)
        )

    def generate_runbook(self, monitoring_config: Dict) -> str:
        """Generate operational runbook"""
        alerts = self._extract_alert_configs(monitoring_config)
        
        return self.templates["runbook"].render(
            alerts=alerts,
            deployment_steps=self._get_deployment_steps(),
            troubleshooting_guide=self._get_troubleshooting_guide()
        )

    def generate_api_docs(self, api_spec_file: str) -> str:
        """Generate API documentation from OpenAPI spec"""
        try:
            with open(api_spec_file, 'r') as f:
                api_spec = yaml.safe_load(f)
            
            endpoints = self._extract_endpoints(api_spec)
            return self.templates["api_docs"].render(endpoints=endpoints)
            
        except FileNotFoundError:
            return self._generate_mock_api_docs()

    def _discover_components(self, config_dir: str) -> List[Dict]:
        """Discover system components from configuration"""
        components = []
        
        # Mock component discovery - in real implementation, parse k8s manifests
        mock_components = [
            {
                "name": "user-service",
                "type": "microservice",
                "description": "Handles user authentication and management",
                "dependencies": ["database", "redis-cache"],
                "health_check": "/health"
            },
            {
                "name": "order-service", 
                "type": "microservice",
                "description": "Manages order processing and fulfillment",
                "dependencies": ["database", "payment-service", "inventory-service"],
                "health_check": "/health"
            },
            {
                "name": "database",
                "type": "storage",
                "description": "PostgreSQL primary database",
                "dependencies": [],
                "health_check": "pg_isready"
            }
        ]
        
        return mock_components

    def _load_configurations(self, config_dir: str) -> List[Dict]:
        """Load configuration files"""
        configurations = []
        
        # Mock configurations
        mock_configs = [
            {
                "name": "Application Config",
                "content": yaml.dump({
                    "database": {
                        "host": "postgres.default.svc.cluster.local",
                        "port": 5432,
                        "database": "app_db"
                    },
                    "redis": {
                        "host": "redis.default.svc.cluster.local",
                        "port": 6379
                    }
                })
            }
        ]
        
        return mock_configs

    def _generate_dependency_graph(self, components: List[Dict]) -> str:
        """Generate dependency graph visualization"""
        graph = "```mermaid\ngraph TD\n"
        
        for component in components:
            for dep in component["dependencies"]:
                graph += f"    {component['name']} --> {dep}\n"
        
        graph += "```"
        return graph

    def _extract_alert_configs(self, monitoring_config: Dict) -> List[Dict]:
        """Extract alert configurations"""
        return [
            {
                "name": "High CPU Usage",
                "condition": "CPU > 80% for 5 minutes",
                "severity": "warning",
                "response": "Check for resource-intensive processes and consider scaling"
            },
            {
                "name": "Service Down",
                "condition": "Health check fails for 2 consecutive checks",
                "severity": "critical", 
                "response": "Immediately investigate service logs and restart if necessary"
            }
        ]

    def _get_deployment_steps(self) -> str:
        """Get deployment procedure steps"""
        return """
1. Run integration tests
2. Build and push container images
3. Apply Kubernetes manifests
4. Verify deployment health
5. Run smoke tests
6. Monitor for 15 minutes
        """

    def _get_troubleshooting_guide(self) -> str:
        """Get troubleshooting guide"""
        return """
## Common Issues

### Service Won't Start
- Check environment variables
- Verify database connectivity
- Review resource limits

### High Response Times
- Check database query performance
- Verify cache hit rates
- Monitor resource utilization

### Memory Leaks
- Review application logs
- Monitor heap usage patterns
- Check for unclosed connections
        """

    def _extract_endpoints(self, api_spec: Dict) -> List[Dict]:
        """Extract endpoints from OpenAPI specification"""
        endpoints = []
        
        # This would parse real OpenAPI spec in production
        mock_endpoints = [
            {
                "method": "POST",
                "path": "/api/users",
                "description": "Create a new user",
                "parameters": [
                    {"name": "username", "type": "string", "description": "User's username"},
                    {"name": "email", "type": "string", "description": "User's email"}
                ],
                "example_request": '{"username": "john_doe", "email": "john@example.com"}',
                "example_response": '{"id": 123, "username": "john_doe", "created_at": "2025-01-01T00:00:00Z"}'
            }
        ]
        
        return mock_endpoints

    def _generate_mock_api_docs(self) -> str:
        """Generate mock API documentation"""
        mock_endpoints = self._extract_endpoints({})
        return self.templates["api_docs"].render(endpoints=mock_endpoints)

    def save_documentation(self, doc_type: str, content: str, output_dir: str):
        """Save generated documentation to file"""
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Documentation saved to: {filepath}")
        return filepath
