#!/bin/bash
set -e

# DSM Control — Production Server Setup
# Run once on the server to set up the dsmcontrol.com deployment.
# Usage: bash /opt/dsm/app/deploy/dsmcontrol/setup.sh

echo "==> Setting up DSM Control production environment..."

DSMCONTROL_DIR="/opt/dsmcontrol"
SOURCE_APP="/opt/dsm/app"  # source repo with deploy configs

# --- Directory structure ---
echo "==> Creating directory structure..."
mkdir -p "$DSMCONTROL_DIR/app"
mkdir -p "$DSMCONTROL_DIR/web/site"
mkdir -p "$DSMCONTROL_DIR/web/app"
mkdir -p "$DSMCONTROL_DIR/repo.git"

# --- Bare git repo ---
echo "==> Initializing bare git repository..."
git init --bare "$DSMCONTROL_DIR/repo.git" 2>/dev/null || echo "  Repo already initialized"

# --- Install post-receive hook ---
echo "==> Installing post-receive hook..."
cp "$SOURCE_APP/deploy/dsmcontrol/post-receive" "$DSMCONTROL_DIR/repo.git/hooks/post-receive"
chmod +x "$DSMCONTROL_DIR/repo.git/hooks/post-receive"

# --- PostgreSQL database ---
echo "==> Creating production database..."
sudo -u postgres psql -c "CREATE DATABASE dsmcontrol_prod;" 2>/dev/null || echo "  Database dsmcontrol_prod already exists"

# --- Copy env template ---
if [ ! -f "$DSMCONTROL_DIR/.env" ]; then
    echo "==> Copying .env.dsmcontrol.example..."
    cp "$SOURCE_APP/deploy/dsmcontrol/.env.dsmcontrol.example" "$DSMCONTROL_DIR/.env"
    echo "  >>> IMPORTANT: Edit $DSMCONTROL_DIR/.env with real values!"
else
    echo "  .env already exists, skipping"
fi

# --- Systemd services ---
echo "==> Installing systemd services..."
cp "$SOURCE_APP/deploy/dsmcontrol/dsmcontrol-api.service" /etc/systemd/system/
cp "$SOURCE_APP/deploy/dsmcontrol/dsmcontrol-celery.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable dsmcontrol-api
systemctl enable dsmcontrol-celery

# --- SSL certificates ---
echo "==> Requesting SSL certificates for dsmcontrol.com..."
certbot certonly --nginx -d dsmcontrol.com -d www.dsmcontrol.com --non-interactive --agree-tos || echo "  Certbot failed — run manually if needed"
certbot certonly --nginx -d app.dsmcontrol.com --non-interactive --agree-tos || echo "  Certbot failed — run manually if needed"
certbot certonly --nginx -d api.dsmcontrol.com --non-interactive --agree-tos || echo "  Certbot failed — run manually if needed"

# --- Nginx ---
echo "==> Installing nginx config..."
cp "$SOURCE_APP/deploy/dsmcontrol/nginx-dsmcontrol.conf" /etc/nginx/sites-available/dsmcontrol
ln -sf /etc/nginx/sites-available/dsmcontrol /etc/nginx/sites-enabled/dsmcontrol
nginx -t && systemctl reload nginx

echo ""
echo "==> DSM Control setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit $DSMCONTROL_DIR/.env with real values (SECRET_KEY, POSTGRES_PASSWORD, etc.)"
echo "  2. Add the git remote locally:"
echo "     git remote add dsmcontrol root@$(hostname -I | awk '{print $1}'):$DSMCONTROL_DIR/repo.git"
echo "  3. Push to deploy:"
echo "     git push dsmcontrol main"
echo "  4. Verify:"
echo "     curl https://api.dsmcontrol.com/health"
echo "     curl https://api.dsmcontrol.com/api/v1/brand"
