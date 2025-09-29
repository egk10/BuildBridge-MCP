#!/bin/bash

# SSL Certificate Setup Script for BuildBridge-MCP
# This script sets up Let's Encrypt SSL certificates using Certbot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=${DOMAIN:-"localhost"}
EMAIL=${EMAIL:-"admin@localhost"}
STAGING=${STAGING:-"true"}

echo -e "${BLUE}🔐 BuildBridge-MCP SSL Certificate Setup${NC}"
echo "========================================"

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo -e "${RED}❌ This script should be run on the host system, not inside Docker containers${NC}"
    echo "Please run this script from your host machine."
    exit 1
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Certbot...${NC}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        sudo yum install -y certbot python3-certbot-nginx
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y certbot python3-certbot-nginx
    else
        echo -e "${RED}❌ Unsupported package manager. Please install certbot manually.${NC}"
        exit 1
    fi
fi

# Create SSL directory if it doesn't exist
SSL_DIR="./deploy/ssl"
mkdir -p "$SSL_DIR"

# Backup existing nginx config
if [ -f "./deploy/nginx.conf" ]; then
    cp "./deploy/nginx.conf" "./deploy/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Backed up nginx.conf${NC}"
fi

# For localhost/development, create self-signed certificates
if [ "$DOMAIN" = "localhost" ] || [ "$STAGING" = "true" ]; then
    echo -e "${YELLOW}🏠 Setting up self-signed certificates for localhost/development...${NC}"

    # Create self-signed certificate
    openssl req -x509 -newkey rsa:4096 -keyout "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" -days 365 -nodes \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN" 2>/dev/null

    echo -e "${GREEN}✅ Self-signed certificates created${NC}"

else
    # Production SSL with Let's Encrypt
    echo -e "${YELLOW}🌐 Setting up Let's Encrypt certificates for $DOMAIN...${NC}"

    # Stop nginx if running (to free port 80)
    if command -v docker-compose &> /dev/null && [ -f "./deploy/docker-compose.yml" ]; then
        echo "Stopping nginx service..."
        docker-compose -f ./deploy/docker-compose.yml stop nginx || true
    fi

    # Get certificate
    if [ "$STAGING" = "true" ]; then
        certbot certonly --standalone --agree-tos --email "$EMAIL" -d "$DOMAIN" --staging
    else
        certbot certonly --standalone --agree-tos --email "$EMAIL" -d "$DOMAIN"
    fi

    # Copy certificates to ssl directory
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/cert.pem"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/key.pem"

    echo -e "${GREEN}✅ Let's Encrypt certificates obtained${NC}"
fi

# Update nginx configuration to support SSL
echo -e "${YELLOW}🔧 Updating nginx configuration for SSL...${NC}"

cat > "./deploy/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Performance
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Upstream backend
    upstream construction_mcp_backend {
        server construction-mcp:8000;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS server block
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /app/ssl/cert.pem;
        ssl_certificate_key /app/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Serve static files and chat interface at root for easy access (catch-all for unmatched requests)
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /chat_interface.html;
            index chat_interface.html;
        }

        # Serve HTML files directly
        location ~ \.html$ {
            root /usr/share/nginx/html;
            try_files $uri =404;
        }

        # API endpoints
        location /api/ {
            # CORS headers
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

            # Handle preflight requests
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }

            rewrite ^/api/(.*)$ /$1 break;
            proxy_pass http://construction_mcp_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Process endpoint (used by chat interface)
        location /process {
            # CORS headers
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

            # Handle preflight requests
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }

            proxy_pass http://construction_mcp_backend/process;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check
        location /health {
            proxy_pass http://construction_mcp_backend/health;
            access_log off;
        }

        # Logs endpoint
        location /logs {
            proxy_pass http://construction_mcp_backend/logs;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket endpoints for logs
        location /ws/logs {
            proxy_pass http://construction_mcp_backend/ws/logs;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Static files
        location /static/ {
            alias /usr/share/nginx/html/;
            try_files $uri $uri/ =404;
        }

        # Chat interface
        location /chat {
            alias /usr/share/nginx/html/chat_interface.html;
            try_files $uri $uri/ =404;
        }

        # Documentation
        location /docs {
            proxy_pass http://construction_mcp_backend/docs;
        }

        # OpenAPI spec
        location /openapi.json {
            proxy_pass http://construction_mcp_backend/openapi.json;
        }
    }
}
EOF

echo -e "${GREEN}✅ Updated nginx.conf with SSL support${NC}"

# Update docker-compose.yml to mount SSL certificates
echo -e "${YELLOW}🔧 Updating docker-compose.yml to mount SSL certificates...${NC}"

# Check if SSL volume is already configured
if ! grep -q "ssl" "./deploy/docker-compose.yml"; then
    # Add SSL volume mount to nginx service
    sed -i '/nginx:/,/image:/ {
        /volumes:/a\
      - ./ssl:/app/ssl:ro
    }' "./deploy/docker-compose.yml"
fi

echo -e "${GREEN}✅ Updated docker-compose.yml${NC}"

# Create certificate renewal script
cat > "./deploy/renew-ssl.sh" << 'EOF'
#!/bin/bash

# SSL Certificate Renewal Script
# Run this script periodically to renew Let's Encrypt certificates

set -e

echo "🔄 Renewing SSL certificates..."

# Stop nginx to free port 80
docker-compose -f ./deploy/docker-compose.yml stop nginx

# Renew certificates
certbot renew

# Copy renewed certificates
DOMAIN=$(grep -oP 'server_name \K[^;]+' ./deploy/nginx.conf | head -1)
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "_" ]; then
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "./deploy/ssl/cert.pem"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "./deploy/ssl/key.pem"
    echo "✅ Certificates renewed and copied"
else
    echo "⚠️  Could not determine domain from nginx.conf"
fi

# Restart services
docker-compose -f ./deploy/docker-compose.yml up -d

echo "🎉 SSL renewal complete!"
EOF

chmod +x "./deploy/renew-ssl.sh"

echo -e "${GREEN}✅ Created SSL renewal script${NC}"

# Create cron job for automatic renewal (if not localhost)
if [ "$DOMAIN" != "localhost" ] && [ "$STAGING" != "true" ]; then
    echo -e "${YELLOW}⏰ Setting up automatic certificate renewal...${NC}"

    # Add to crontab (runs twice daily)
    (crontab -l ; echo "0 12,0 * * * cd $(pwd) && ./deploy/renew-ssl.sh") | crontab -

    echo -e "${GREEN}✅ Added automatic renewal to crontab${NC}"
fi

echo ""
echo -e "${GREEN}🎉 SSL setup completed successfully!${NC}"
echo ""
echo "📋 Summary:"
echo "   - SSL certificates created in ./deploy/ssl/"
echo "   - nginx.conf updated for HTTPS"
echo "   - docker-compose.yml updated to mount certificates"
echo "   - SSL renewal script created: ./deploy/renew-ssl.sh"
if [ "$DOMAIN" != "localhost" ] && [ "$STAGING" != "true" ]; then
    echo "   - Automatic renewal configured in crontab"
fi
echo ""
echo "🚀 Next steps:"
echo "   1. Restart your services: docker-compose -f ./deploy/docker-compose.yml down && docker-compose -f ./deploy/docker-compose.yml up -d"
echo "   2. Test HTTPS access: https://$DOMAIN"
echo "   3. Update any bookmarks or configurations to use HTTPS"
echo ""
echo "🔧 Management:"
echo "   - Manual renewal: ./deploy/renew-ssl.sh"
echo "   - View certificates: openssl x509 -in ./deploy/ssl/cert.pem -text -noout"