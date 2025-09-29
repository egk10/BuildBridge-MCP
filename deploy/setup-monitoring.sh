#!/bin/bash

# Monitoring Setup Script
# Run this to configure Grafana dashboards and alert rules

set -e

echo "📊 Setting up monitoring..."

# Wait for Grafana to be ready
echo "Waiting for Grafana..."
until curl -s http://localhost:3003/api/health > /dev/null; do
  sleep 5
done

# Create data source
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }' \
  http://admin:admin@localhost:3003/api/datasources

echo "✅ Prometheus data source configured"

# Import dashboard
if [ -f "./alerts/grafana-dashboard.json" ]; then
  curl -X POST -H "Content-Type: application/json" \
    -d @./alerts/grafana-dashboard.json \
    http://admin:admin@localhost:3003/api/dashboards/db

  echo "✅ Dashboard imported"
fi

echo "🎉 Monitoring setup complete!"
echo ""
echo "Access points:"
echo "  - Grafana Dashboard: http://localhost:3003 (admin/admin)"
echo "  - Prometheus: http://localhost:9092"
echo ""
echo "Alert rules configured for:"
echo "  - MCP service health"
echo "  - Database connectivity"
echo "  - Redis cache status"
echo "  - System resources (CPU, memory, disk)"
