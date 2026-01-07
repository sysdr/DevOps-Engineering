from prometheus_client import Counter, Histogram, Gauge
import time

# Workflow metrics
workflows_total = Counter('workflows_total', 'Total workflows submitted')
workflows_completed = Counter('workflows_completed', 'Completed workflows')
workflows_failed = Counter('workflows_failed', 'Failed workflows')
workflow_duration = Histogram('workflow_duration_seconds', 'Workflow execution time')

# Self-healing metrics
healing_actions_total = Counter('healing_actions_total', 'Total healing actions')
healing_success = Counter('healing_success_total', 'Successful healing actions')
healing_failures = Counter('healing_failures_total', 'Failed healing actions')
recovery_time = Histogram('recovery_time_seconds', 'Time to recover from failure')

# Chaos metrics
chaos_experiments_total = Counter('chaos_experiments_total', 'Total chaos experiments')
chaos_experiments_passed = Counter('chaos_passed_total', 'Passed chaos experiments')
chaos_experiments_failed = Counter('chaos_failed_total', 'Failed chaos experiments')

# Incident metrics
incidents_total = Counter('incidents_total', 'Total incidents detected')
incidents_auto_resolved = Counter('incidents_auto_resolved', 'Auto-resolved incidents')
mttr = Histogram('mean_time_to_recovery_seconds', 'Mean time to recovery')

# Resource metrics
active_workflows = Gauge('active_workflows', 'Currently running workflows')
cluster_health_score = Gauge('cluster_health_score', 'Overall cluster health')
