"""
Flask API Server for Policy as Code Dashboard
Provides endpoints for policy management, violation monitoring, and remediation
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# Demo Data Storage
policies_db = [
    {
        'id': 'pol-001',
        'name': 'RequireResourceLimits',
        'description': 'All containers must have CPU and memory limits',
        'severity': 'high',
        'status': 'active',
        'enforcement': 'deny',
        'created_at': '2025-09-20T10:00:00Z',
        'violations_count': 15
    },
    {
        'id': 'pol-002',
        'name': 'AllowedImageRegistries',
        'description': 'Images must come from approved registries',
        'severity': 'critical',
        'status': 'active',
        'enforcement': 'deny',
        'created_at': '2025-09-21T14:30:00Z',
        'violations_count': 8
    },
    {
        'id': 'pol-003',
        'name': 'RequireLabels',
        'description': 'Resources must have team, app, and environment labels',
        'severity': 'medium',
        'status': 'active',
        'enforcement': 'deny',
        'created_at': '2025-09-22T09:15:00Z',
        'violations_count': 23
    },
    {
        'id': 'pol-004',
        'name': 'BlockPrivilegedContainers',
        'description': 'Containers cannot run in privileged mode',
        'severity': 'critical',
        'status': 'active',
        'enforcement': 'deny',
        'created_at': '2025-09-23T11:45:00Z',
        'violations_count': 3
    },
    {
        'id': 'pol-005',
        'name': 'RequireReadOnlyRootFS',
        'description': 'Container root filesystem must be read-only',
        'severity': 'medium',
        'status': 'audit',
        'enforcement': 'dryrun',
        'created_at': '2025-09-24T16:20:00Z',
        'violations_count': 42
    }
]

violations_db = [
    {
        'id': 'vio-001',
        'policy_id': 'pol-001',
        'policy_name': 'RequireResourceLimits',
        'resource_name': 'web-server',
        'resource_type': 'Deployment',
        'namespace': 'production',
        'severity': 'high',
        'status': 'open',
        'message': "Container 'nginx' does not have CPU limits set",
        'detected_at': '2025-09-28T08:30:00Z',
        'remediation_available': True
    },
    {
        'id': 'vio-002',
        'policy_id': 'pol-002',
        'policy_name': 'AllowedImageRegistries',
        'resource_name': 'api-gateway',
        'resource_type': 'Deployment',
        'namespace': 'production',
        'severity': 'critical',
        'status': 'open',
        'message': "Container 'gateway' uses image from unapproved registry: 'docker.internal.com/gateway:v2.1'",
        'detected_at': '2025-09-28T09:15:00Z',
        'remediation_available': False
    },
    {
        'id': 'vio-003',
        'policy_id': 'pol-003',
        'policy_name': 'RequireLabels',
        'resource_name': 'cache-service',
        'resource_type': 'StatefulSet',
        'namespace': 'staging',
        'severity': 'medium',
        'status': 'remediating',
        'message': "Resource is missing required label: 'team'",
        'detected_at': '2025-09-28T07:45:00Z',
        'remediation_available': True
    },
    {
        'id': 'vio-004',
        'policy_id': 'pol-001',
        'policy_name': 'RequireResourceLimits',
        'resource_name': 'worker-pool',
        'resource_type': 'Deployment',
        'namespace': 'production',
        'severity': 'high',
        'status': 'open',
        'message': "Container 'worker' does not have memory limits set",
        'detected_at': '2025-09-28T10:00:00Z',
        'remediation_available': True
    },
    {
        'id': 'vio-005',
        'policy_id': 'pol-004',
        'policy_name': 'BlockPrivilegedContainers',
        'resource_name': 'debug-pod',
        'resource_type': 'Pod',
        'namespace': 'default',
        'severity': 'critical',
        'status': 'open',
        'message': "Container 'debugger' is running in privileged mode",
        'detected_at': '2025-09-28T11:20:00Z',
        'remediation_available': False
    },
    {
        'id': 'vio-006',
        'policy_id': 'pol-003',
        'policy_name': 'RequireLabels',
        'resource_name': 'frontend',
        'resource_type': 'Deployment',
        'namespace': 'staging',
        'severity': 'medium',
        'status': 'resolved',
        'message': "Resource is missing required label: 'environment'",
        'detected_at': '2025-09-27T14:30:00Z',
        'remediation_available': True,
        'resolved_at': '2025-09-27T15:00:00Z'
    }
]

resources_db = [
    {'name': 'web-server', 'namespace': 'production', 'type': 'Deployment', 'status': 'violating'},
    {'name': 'api-gateway', 'namespace': 'production', 'type': 'Deployment', 'status': 'violating'},
    {'name': 'cache-service', 'namespace': 'staging', 'type': 'StatefulSet', 'status': 'remediating'},
    {'name': 'worker-pool', 'namespace': 'production', 'type': 'Deployment', 'status': 'violating'},
    {'name': 'debug-pod', 'namespace': 'default', 'type': 'Pod', 'status': 'violating'},
    {'name': 'frontend', 'namespace': 'staging', 'type': 'Deployment', 'status': 'compliant'},
    {'name': 'backend', 'namespace': 'production', 'type': 'Deployment', 'status': 'compliant'},
    {'name': 'database', 'namespace': 'production', 'type': 'StatefulSet', 'status': 'compliant'},
    {'name': 'queue', 'namespace': 'production', 'type': 'Deployment', 'status': 'compliant'},
    {'name': 'monitoring', 'namespace': 'system', 'type': 'DaemonSet', 'status': 'compliant'}
]

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/policies', methods=['GET'])
def get_policies():
    """Get all active policies"""
    status_filter = request.args.get('status')
    
    filtered_policies = policies_db
    if status_filter:
        filtered_policies = [p for p in policies_db if p['status'] == status_filter]
    
    return jsonify({
        'policies': filtered_policies,
        'total': len(filtered_policies)
    })

@app.route('/api/violations', methods=['GET'])
def get_violations():
    """Get policy violations with optional filtering"""
    severity_filter = request.args.get('severity')
    status_filter = request.args.get('status')
    namespace_filter = request.args.get('namespace')
    
    filtered_violations = violations_db
    
    if severity_filter:
        filtered_violations = [v for v in filtered_violations if v['severity'] == severity_filter]
    
    if status_filter:
        filtered_violations = [v for v in filtered_violations if v['status'] == status_filter]
    
    if namespace_filter:
        filtered_violations = [v for v in filtered_violations if v['namespace'] == namespace_filter]
    
    return jsonify({
        'violations': filtered_violations,
        'total': len(filtered_violations)
    })

@app.route('/api/violations/<violation_id>/remediate', methods=['POST'])
def remediate_violation(violation_id):
    """Trigger remediation for a specific violation"""
    violation = next((v for v in violations_db if v['id'] == violation_id), None)
    
    if not violation:
        return jsonify({'error': 'Violation not found'}), 404
    
    if not violation['remediation_available']:
        return jsonify({
            'error': 'Automatic remediation not available for this violation',
            'manual_steps': 'Please review and fix manually'
        }), 400
    
    # Simulate remediation
    violation['status'] = 'remediating'
    violation['remediation_started_at'] = datetime.utcnow().isoformat()
    
    return jsonify({
        'message': 'Remediation started',
        'violation_id': violation_id,
        'estimated_completion': '2-5 minutes'
    })

@app.route('/api/compliance/metrics', methods=['GET'])
def get_compliance_metrics():
    """Get compliance metrics and statistics"""
    total_resources = len(resources_db)
    total_violations = len([v for v in violations_db if v['status'] == 'open'])
    critical_violations = len([v for v in violations_db if v['severity'] == 'critical' and v['status'] == 'open'])
    
    compliant_resources = len([r for r in resources_db if r['status'] == 'compliant'])
    compliance_rate = (compliant_resources / total_resources * 100) if total_resources > 0 else 100
    
    # Violations by policy
    violations_by_policy = {}
    for violation in violations_db:
        if violation['status'] == 'open':
            policy_name = violation['policy_name']
            violations_by_policy[policy_name] = violations_by_policy.get(policy_name, 0) + 1
    
    # Violations by namespace
    violations_by_namespace = {}
    for violation in violations_db:
        if violation['status'] == 'open':
            namespace = violation['namespace']
            violations_by_namespace[namespace] = violations_by_namespace.get(namespace, 0) + 1
    
    return jsonify({
        'total_resources': total_resources,
        'compliant_resources': compliant_resources,
        'total_violations': total_violations,
        'critical_violations': critical_violations,
        'compliance_rate': round(compliance_rate, 2),
        'violations_by_policy': violations_by_policy,
        'violations_by_namespace': violations_by_namespace
    })

@app.route('/api/compliance/trends', methods=['GET'])
def get_compliance_trends():
    """Get compliance trend data over time"""
    days = int(request.args.get('days', 7))
    
    # Generate synthetic trend data
    trends = []
    base_compliance = 75
    
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        compliance = min(100, base_compliance + (i * 3) + random.randint(-2, 5))
        violations = int((100 - compliance) / 100 * 50)
        
        trends.append({
            'date': date,
            'compliance_rate': round(compliance, 2),
            'total_violations': violations,
            'critical_violations': max(0, violations // 5),
            'resolved_violations': random.randint(3, 10)
        })
    
    return jsonify({
        'trends': trends,
        'period_days': days
    })

@app.route('/api/audit/run', methods=['POST'])
def run_audit():
    """Trigger a full cluster audit"""
    return jsonify({
        'message': 'Audit started',
        'scan_id': f'audit-{int(datetime.utcnow().timestamp())}',
        'estimated_duration': '5-10 minutes',
        'resources_to_scan': len(resources_db)
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Policy as Code Dashboard API Server")
    print("="*50)
    print(f"Starting server on http://0.0.0.0:5000")
    print(f"Health check: http://localhost:5000/health")
    print(f"API Endpoints:")
    print(f"  GET  /api/policies")
    print(f"  GET  /api/violations")
    print(f"  POST /api/violations/<id>/remediate")
    print(f"  GET  /api/compliance/metrics")
    print(f"  GET  /api/compliance/trends")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
