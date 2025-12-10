from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
import json

class CertificateManager:
    """Simulates cert-manager functionality"""
    
    def __init__(self):
        self.ca_key = None
        self.ca_cert = None
        self.certificates = {}
        self.cert_events = []
    
    def initialize_ca(self):
        """Create root CA certificate"""
        # Generate CA private key
        self.ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Zero-Trust CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"Zero-Trust Root CA"),
        ])
        
        self.ca_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(self.ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=3650))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .sign(self.ca_key, hashes.SHA256())
        )
        
        self.cert_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "ca_initialized",
            "subject": "Zero-Trust Root CA"
        })
    
    def issue_certificate(self, service_name: str, namespace: str = "default"):
        """Issue certificate for a service"""
        # Generate service private key
        service_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Create certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Zero-Trust Services"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"{service_name}.{namespace}.svc.cluster.local"),
        ])
        
        # Short-lived certificate (24 hours for demo, would be configurable in production)
        valid_hours = 24
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(service_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(hours=valid_hours))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(f"{service_name}"),
                    x509.DNSName(f"{service_name}.{namespace}"),
                    x509.DNSName(f"{service_name}.{namespace}.svc"),
                    x509.DNSName(f"{service_name}.{namespace}.svc.cluster.local"),
                ]),
                critical=False,
            )
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(self.ca_key, hashes.SHA256())
        )
        
        cert_id = f"{service_name}.{namespace}"
        self.certificates[cert_id] = {
            "cert": cert,
            "key": service_key,
            "issued_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=valid_hours),
            "status": "ACTIVE"
        }
        
        self.cert_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "certificate_issued",
            "service": service_name,
            "namespace": namespace,
            "expires_at": self.certificates[cert_id]["expires_at"].isoformat()
        })
        
        return cert_id
    
    def get_certificate_info(self, cert_id: str):
        """Get certificate information"""
        if cert_id not in self.certificates:
            return None
        
        cert_data = self.certificates[cert_id]
        now = datetime.utcnow()
        expires_at = cert_data["expires_at"]
        time_until_expiry = expires_at - now
        
        # Calculate lifecycle state
        total_lifetime = (expires_at - cert_data["issued_at"]).total_seconds()
        time_elapsed = (now - cert_data["issued_at"]).total_seconds()
        percentage_elapsed = (time_elapsed / total_lifetime) * 100
        
        if percentage_elapsed > 80:
            status = "NEAR_EXPIRY"
        elif percentage_elapsed > 50:
            status = "ACTIVE"
        else:
            status = "NEWLY_ISSUED"
        
        return {
            "cert_id": cert_id,
            "issued_at": cert_data["issued_at"].isoformat(),
            "expires_at": expires_at.isoformat(),
            "time_until_expiry_seconds": time_until_expiry.total_seconds(),
            "status": status,
            "percentage_elapsed": round(percentage_elapsed, 2)
        }
    
    def list_certificates(self):
        """List all certificates with their status"""
        return [
            self.get_certificate_info(cert_id)
            for cert_id in self.certificates.keys()
        ]
    
    def get_events(self):
        """Get certificate events"""
        return self.cert_events

# Create global certificate manager instance
cert_manager = CertificateManager()
cert_manager.initialize_ca()

# Issue certificates for our services
cert_manager.issue_certificate("auth-service", "default")
cert_manager.issue_certificate("resource-service", "default")
cert_manager.issue_certificate("policy-service", "default")
cert_manager.issue_certificate("frontend", "default")
