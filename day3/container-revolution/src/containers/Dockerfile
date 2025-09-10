FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

# Install Python and dependencies
RUN microdnf update -y && \
    microdnf install -y python3.11 python3.11-pip && \
    microdnf clean all

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3.11 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["python3.11", "src/backend/api/app.py"]
