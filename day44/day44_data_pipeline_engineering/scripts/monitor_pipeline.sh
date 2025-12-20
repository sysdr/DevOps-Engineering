#!/bin/bash

echo "==================================="
echo "Data Pipeline Monitor"
echo "==================================="
echo ""

while true; do
    clear
    echo "==================================="
    echo "Pipeline Status - $(date)"
    echo "==================================="
    echo ""
    
    # Check if metrics file exists
    if [ -f "/tmp/pipeline_data/metrics/ingestion_metrics.json" ]; then
        echo "📊 Ingestion Metrics:"
        cat /tmp/pipeline_data/metrics/ingestion_metrics.json | python3 -m json.tool
        echo ""
    fi
    
    # Check validation results
    if [ -f "/tmp/pipeline_data/validation/results.json" ]; then
        echo "✓ Validation Results:"
        cat /tmp/pipeline_data/validation/results.json | python3 -m json.tool
        echo ""
    fi
    
    # Check DVC versions
    if [ -f "/tmp/dvc_storage/versions.json" ]; then
        echo "📦 Dataset Versions:"
        cat /tmp/dvc_storage/versions.json | python3 -m json.tool
        echo ""
    fi
    
    sleep 5
done
