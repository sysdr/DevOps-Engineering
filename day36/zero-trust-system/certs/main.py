from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cert_service import cert_manager

app = FastAPI(title="Certificate Manager Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/certs/list")
async def list_certificates():
    """List all managed certificates"""
    return {"certificates": cert_manager.list_certificates()}

@app.get("/certs/events")
async def get_cert_events():
    """Get certificate lifecycle events"""
    return {"events": cert_manager.get_events()}

@app.get("/certs/{cert_id}")
async def get_certificate(cert_id: str):
    """Get specific certificate information"""
    cert_info = cert_manager.get_certificate_info(cert_id)
    if not cert_info:
        return {"error": "Certificate not found"}, 404
    return cert_info

@app.post("/certs/issue")
async def issue_certificate(service_name: str, namespace: str = "default"):
    """Issue new certificate for a service"""
    cert_id = cert_manager.issue_certificate(service_name, namespace)
    return {
        "message": "Certificate issued successfully",
        "cert_id": cert_id,
        "info": cert_manager.get_certificate_info(cert_id)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "cert-manager"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
