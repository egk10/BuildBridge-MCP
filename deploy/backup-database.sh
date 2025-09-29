#!/bin/bash

# Automated Database Backup Script for BuildBridge-MCP
# This script creates automated backups of PostgreSQL database

set -e

# Configuration
BACKUP_DIR="./backups"
DB_NAME="construction_mcp"
DB_USER="mcpuser"
DB_HOST="localhost"
DB_PORT="5432"
RETENTION_DAYS=7

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}💾 BuildBridge-MCP Database Backup${NC}"
echo "====================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_backup_$TIMESTAMP.sql.gz"

echo -e "${YELLOW}🔄 Creating database backup...${NC}"

# Create backup using docker exec
if docker-compose -f ./deploy/docker-compose.yml ps postgres | grep -q "Up"; then
    docker-compose -f ./deploy/docker-compose.yml exec -T postgres pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" | gzip > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"

        # Get backup size
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}📊 Backup size: $BACKUP_SIZE${NC}"
    else
        echo -e "${RED}❌ Backup failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ PostgreSQL container is not running${NC}"
    exit 1
fi

# Clean up old backups
echo -e "${YELLOW}🧹 Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"

find "$BACKUP_DIR" -name "${DB_NAME}_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

OLD_BACKUPS=$(find "$BACKUP_DIR" -name "${DB_NAME}_backup_*.sql.gz" -mtime +$RETENTION_DAYS | wc -l)
if [ "$OLD_BACKUPS" -gt 0 ]; then
    echo -e "${GREEN}🗑️  Removed $OLD_BACKUPS old backup(s)${NC}"
else
    echo -e "${GREEN}✅ No old backups to remove${NC}"
fi

# List current backups
echo -e "${YELLOW}📋 Current backups:${NC}"
ls -la "$BACKUP_DIR"/${DB_NAME}_backup_*.sql.gz 2>/dev/null || echo "No backups found"

# Verify backup integrity
echo -e "${YELLOW}🔍 Verifying backup integrity...${NC}"

if gzip -t "$BACKUP_FILE"; then
    echo -e "${GREEN}✅ Backup integrity verified${NC}"
else
    echo -e "${RED}❌ Backup integrity check failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Database backup completed successfully!${NC}"
echo ""
echo "📊 Summary:"
echo "   - Backup file: $BACKUP_FILE"
echo "   - Backup size: $BACKUP_SIZE"
echo "   - Retention: $RETENTION_DAYS days"
echo ""
echo "🔧 To restore from backup:"
echo "   gunzip < $BACKUP_FILE | docker-compose -f ./deploy/docker-compose.yml exec -T postgres psql -U $DB_USER -d $DB_NAME"