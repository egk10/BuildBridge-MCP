#!/bin/bash
# Production Deployment Script for BuildBridge-MCP
# This script deploys the application with secure environment variable configuration

set -e

echo "🚀 BuildBridge-MCP Production Deployment"
echo "========================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please create it with your production credentials."
    echo "   Copy .env.template to .env and fill in your values."
    exit 1
fi

# Validate .env file has required variables
echo "🔍 Validating environment configuration..."
REQUIRED_VARS=(
    "GOOGLE_CLIENT_ID"
    "GOOGLE_CLIENT_SECRET"
    "GOOGLE_PROJECT_ID"
    "OPENAI_API_KEY"
    "GOOGLE_SHEETS_PROJECT_72_PERTH"
    "GOOGLE_SHEETS_PROJECT_17175_YONGE_ST"
    "GOOGLE_SHEETS_PROJECT_AZURE_ROAD"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo "   Please update your .env file."
    exit 1
fi

echo "✅ Environment configuration validated"

# Create necessary directories
echo "📁 Creating deployment directories..."
mkdir -p deploy/data
mkdir -p deploy/logs
mkdir -p deploy/ssl

# Build and start services
echo "🐳 Building and starting Docker services..."
cd deploy
docker-compose down 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running"
else
    echo "❌ Some services failed to start. Check logs:"
    docker-compose logs
    exit 1
fi

# Test application health
echo "🔍 Testing application health..."
if curl -f http://localhost:8002/health >/dev/null 2>&1; then
    echo "✅ Application is healthy"
else
    echo "❌ Application health check failed"
    docker-compose logs construction-mcp
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service URLs:"
echo "   - BuildBridge-MCP API: http://localhost:8002"
echo "   - Nginx Proxy: http://localhost:8081"
echo "   - Grafana Dashboard: http://localhost:3003 (admin/admin)"
echo "   - Prometheus Metrics: http://localhost:9092"
echo ""
echo "📝 Next steps:"
echo "   1. Configure Grafana dashboards for your metrics"
echo "   2. Set up SSL certificates in deploy/ssl/"
echo "   3. Configure nginx.conf for your domain"
echo "   4. Set up monitoring alerts"
echo ""
echo "🔧 Management commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart: docker-compose restart"
echo "   - Update: docker-compose pull && docker-compose up -d"