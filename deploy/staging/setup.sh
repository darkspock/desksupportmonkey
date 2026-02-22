#!/bin/bash
set -e

# DeskSupportMonkey — Staging Server Setup
# Run once on the production server to set up the staging environment.
# Usage: bash /opt/dsm/app/deploy/staging/setup.sh

echo "==> Setting up DeskSupportMonkey Staging Environment..."

STAGING_DIR="/opt/dsm-staging"
PROD_APP="/opt/dsm/app"

# --- Directory structure ---
echo "==> Creating directory structure..."
mkdir -p "$STAGING_DIR/app"
mkdir -p "$STAGING_DIR/repo.git"

# --- Bare git repo ---
echo "==> Initializing bare git repository..."
git init --bare "$STAGING_DIR/repo.git" 2>/dev/null || echo "  Repo already initialized"

# --- Install post-receive hook ---
echo "==> Installing post-receive hook..."
cp "$PROD_APP/deploy/staging/post-receive" "$STAGING_DIR/repo.git/hooks/post-receive"
chmod +x "$STAGING_DIR/repo.git/hooks/post-receive"

# --- PostgreSQL database ---
echo "==> Creating staging database..."
sudo -u postgres psql -c "CREATE DATABASE dsm_staging;" 2>/dev/null || echo "  Database dsm_staging already exists"

# --- Copy env template ---
if [ ! -f "$STAGING_DIR/.env.staging" ]; then
    echo "==> Copying .env.staging.example..."
    cp "$PROD_APP/deploy/staging/.env.staging.example" "$STAGING_DIR/.env.staging"
    echo "  >>> IMPORTANT: Edit $STAGING_DIR/.env.staging with real values!"
else
    echo "  .env.staging already exists, skipping"
fi

# --- Systemd services ---
echo "==> Installing systemd services..."
cp "$PROD_APP/deploy/staging/dsm-staging-api.service" /etc/systemd/system/
cp "$PROD_APP/deploy/staging/dsm-staging-celery.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable dsm-staging-api
systemctl enable dsm-staging-celery

# --- SSL certificate ---
echo "==> Requesting SSL certificate for staging.desksupportmonkey.com..."
certbot certonly --nginx -d staging.desksupportmonkey.com --non-interactive --agree-tos || echo "  Certbot failed — run manually if needed"

# --- Nginx ---
echo "==> Installing nginx config..."
cp "$PROD_APP/deploy/staging/nginx-dsm-staging.conf" /etc/nginx/sites-available/dsm-staging
ln -sf /etc/nginx/sites-available/dsm-staging /etc/nginx/sites-enabled/dsm-staging
nginx -t && systemctl reload nginx

echo ""
echo "==> Staging setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit $STAGING_DIR/.env.staging with real values (SECRET_KEY, POSTGRES_PASSWORD, etc.)"
echo "  2. Add the staging git remote locally:"
echo "     git remote add staging root@$(hostname -I | awk '{print $1}'):$STAGING_DIR/repo.git"
echo "  3. Push to deploy:"
echo "     git push staging main"
echo "  4. Verify:"
echo "     curl https://staging.desksupportmonkey.com/api/v1/health"
