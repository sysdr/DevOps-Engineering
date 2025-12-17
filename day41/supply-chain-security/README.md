# Day 41: Supply Chain Security System

A production-grade supply chain security system with SBOM generation, signature verification, vulnerability scanning, and policy enforcement.

## Features

- **SBOM Generation**: Automatic Software Bill of Materials creation
- **Signature Verification**: Cosign-compatible signing and verification
- **Vulnerability Scanning**: CVE detection and tracking
- **License Compliance**: Automated license checking
- **Policy Engine**: Configurable compliance policies
- **Real-time Dashboard**: Modern web interface

## Quick Start

### Without Docker

```bash
./start.sh
```

Access:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### With Docker

```bash
docker-compose up --build
```

## Usage

1. Create a sample artifact
2. Generate SBOM
3. Sign the artifact
4. Scan for vulnerabilities
5. View results in dashboard

## Testing

```bash
source venv/bin/activate
cd tests
pytest -v test_api.py
```

## Architecture

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: Vanilla JavaScript
- **Storage**: File-based (JSON)
- **Format**: CycloneDX for SBOMs

## API Endpoints

- `POST /api/artifacts` - Create artifact
- `POST /api/sbom/generate` - Generate SBOM
- `POST /api/sign` - Sign artifact
- `POST /api/verify` - Verify signature
- `POST /api/scan/vulnerabilities` - Scan for CVEs
- `GET /api/dashboard/stats` - Get statistics

## Stop Services

```bash
./stop.sh
```
