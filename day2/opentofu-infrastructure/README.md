# OpenTofu Infrastructure Manager
## Day 2: Advanced Infrastructure Patterns & State Management

A comprehensive infrastructure management system built with OpenTofu, demonstrating enterprise-grade patterns for infrastructure as code.

## 🏗️ Architecture Overview

- **Backend**: FastAPI with Python 3.11
- **Frontend**: React 18 with modern UI/UX
- **Infrastructure**: OpenTofu with remote state management
- **Monitoring**: Automated drift detection and remediation
- **Containerization**: Docker with multi-stage builds

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm
- Docker (optional)

### Local Development

1. **Start the application:**
   ```bash
   ./start.sh
   ```

2. **Access the dashboard:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Stop the application:**
   ```bash
   ./stop.sh
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Stop services
docker-compose down
```

## 📊 Features

### Infrastructure Management
- ✅ Multi-environment deployments (dev, staging, prod)
- ✅ Remote state management with locking
- ✅ Modular infrastructure components
- ✅ Automated deployment workflows

### Monitoring & Operations
- ✅ Real-time infrastructure status dashboard
- ✅ Automated drift detection (every 15 minutes)
- ✅ One-click drift remediation
- ✅ Resource health monitoring

### Security & Compliance
- ✅ State file encryption
- ✅ Access control and audit logging
- ✅ Secure module composition
- ✅ Change approval workflows

## 🧪 Testing

### Run API Tests
```bash
cd tests
python test_api.py
```

### Run Frontend Tests
```bash
cd tests
python test_frontend.py
```

### Run Integration Tests
```bash
./start.sh  # Automatically runs tests after startup
```

## 📁 Project Structure

```
opentofu-infrastructure/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # Main API application
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container config
├── frontend/                  # React frontend
│   ├── src/                  # React source code
│   ├── package.json          # Node.js dependencies
│   └── Dockerfile           # Frontend container config
├── infrastructure/            # OpenTofu configurations
│   ├── environments/         # Environment-specific configs
│   └── providers/           # Provider configurations
├── modules/                  # Reusable infrastructure modules
│   ├── vpc/                 # VPC module
│   ├── compute/             # Compute resources module
│   └── database/            # Database module
├── scripts/                  # Automation scripts
│   └── drift-detection/     # Drift monitoring scripts
├── tests/                   # Test files
├── docker-compose.yml       # Docker orchestration
├── start.sh                # Startup script
└── stop.sh                 # Shutdown script
```

## 🔧 Configuration

### Environment Variables
```bash
# AWS Configuration
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2

# Application Configuration
export ENVIRONMENT=dev
export API_BASE_URL=http://localhost:8000
```

### OpenTofu State Backend
The system uses S3 for remote state storage with DynamoDB for locking:
- State Bucket: Auto-generated with random suffix
- Lock Table: `opentofu-locks`
- Encryption: AES-256

## 📈 Monitoring

### Drift Detection
The system automatically monitors for infrastructure drift:
- **Frequency**: Every 15 minutes
- **Scope**: All managed environments
- **Actions**: Auto-remediation for dev environment
- **Notifications**: Console logging (extendable to email/Slack)

### Health Checks
- API health monitoring
- Resource status tracking
- Environment availability checks
- Performance metrics collection

## 🔒 Security

### State Management
- Encrypted state files in S3
- DynamoDB state locking
- IAM role-based access control
- Audit trail for all changes

### API Security
- CORS configuration
- Input validation
- Error handling
- Request rate limiting (configurable)

## 🚀 Production Deployment

### AWS Setup
1. Create S3 bucket for state storage
2. Create DynamoDB table for state locking
3. Configure IAM roles and policies
4. Set up VPC and security groups

### Container Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## 🎯 Learning Objectives Achieved

- ✅ Migrated from Terraform to OpenTofu
- ✅ Implemented remote state management with locking
- ✅ Created reusable infrastructure modules
- ✅ Built automated drift detection system
- ✅ Designed production-ready deployment workflows

## 🔗 Related Lessons

- **Day 1**: Modern Linux Systems & Cloud Foundation
- **Day 3**: Container Revolution - Beyond Docker

## 📚 Additional Resources

- [OpenTofu Documentation](https://opentofu.org/docs/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Infrastructure as Code Best Practices](https://docs.aws.amazon.com/whitepapers/latest/introduction-devops-aws/infrastructure-as-code.html)
