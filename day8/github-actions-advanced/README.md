# Day 8: GitHub Actions Advanced Patterns

## Overview
Enterprise-grade CI/CD pipeline implementation with:
- Reusable workflows and composite actions
- Matrix builds for parallel testing
- Advanced caching strategies
- OIDC authentication
- Multi-environment deployments

## Quick Start
```bash
./start.sh
```

## Architecture
- **API Service**: FastAPI backend with Redis caching
- **User Service**: FastAPI microservice for user management
- **Frontend**: React dashboard with real-time monitoring
- **CI/CD**: Advanced GitHub Actions patterns

## Features Demonstrated
- ✅ Reusable workflow templates
- ✅ Composite action development
- ✅ Dynamic matrix generation
- ✅ OIDC integration for security
- ✅ Advanced caching strategies
- ✅ Multi-environment promotion

## URLs
- Dashboard: http://localhost:3000
- API Service: http://localhost:8000
- User Service: http://localhost:8001

## Testing
```bash
./scripts/test.sh
```

## Stop Services
```bash
./stop.sh
```
