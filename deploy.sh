#!/bin/bash
# =============================================================================
# Byte Bot — Oracle Cloud deployment script
# Run this on a fresh Ubuntu 22.04 Oracle VM
# Usage: bash deploy.sh
# =============================================================================

set -e

echo "🚀 Starting Byte Bot deployment..."

# ── 1. System update & dependencies ──────────────────────────────────────────
echo "📦 Installing system dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3.12 python3.12-venv python3-pip git curl ufw

# ── 2. Clone or update repo ───────────────────────────────────────────────────
REPO_DIR="/opt/byte"

if [ -d "$REPO_DIR" ]; then
    echo "🔄 Updating existing repo..."
    cd $REPO_DIR
    git pull
else
    echo "📥 Cloning repo..."
    # Replace with your actual GitHub repo URL
    sudo git clone https://github.com/YOUR_USERNAME/byte-bot.git $REPO_DIR
    cd $REPO_DIR
fi

sudo chown -R $USER:$USER $REPO_DIR

# ── 3. Python virtual environment ────────────────────────────────────────────
echo "🐍 Setting up Python venv..."
cd $REPO_DIR
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── 4. Environment file ───────────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/.env" ]; then
    echo "⚠️  .env not found! Copying from .env.example..."
    cp $REPO_DIR/.env.example $REPO_DIR/.env
    echo ""
    echo "❗ Edit the .env file before continuing:"
    echo "   nano $REPO_DIR/.env"
    echo ""
    echo "Then run this script again or manually start services:"
    echo "   sudo systemctl start byte-bot byte-admin"
    exit 0
fi

# ── 5. Systemd service: Telegram Bot ─────────────────────────────────────────
echo "⚙️  Creating systemd service for bot..."
sudo tee /etc/systemd/system/byte-bot.service > /dev/null <<EOF
[Unit]
Description=Byte Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$REPO_DIR
EnvironmentFile=$REPO_DIR/.env
ExecStart=$REPO_DIR/venv/bin/python -m bot.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# ── 6. Systemd service: Admin Panel ──────────────────────────────────────────
echo "⚙️  Creating systemd service for admin panel..."
sudo tee /etc/systemd/system/byte-admin.service > /dev/null <<EOF
[Unit]
Description=Byte Admin Panel
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$REPO_DIR
EnvironmentFile=$REPO_DIR/.env
ExecStart=$REPO_DIR/venv/bin/uvicorn admin.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# ── 7. Enable & start services ────────────────────────────────────────────────
echo "▶️  Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable byte-bot byte-admin
sudo systemctl restart byte-bot byte-admin

# ── 8. Firewall: open port 8000 ───────────────────────────────────────────────
echo "🔒 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service status:"
sudo systemctl status byte-bot --no-pager -l
echo ""
sudo systemctl status byte-admin --no-pager -l
echo ""
echo "🌐 Admin panel: http://$(curl -s ifconfig.me):8000/admin/dashboard"
echo ""
echo "📋 Useful commands:"
echo "   Logs bot:   sudo journalctl -u byte-bot -f"
echo "   Logs admin: sudo journalctl -u byte-admin -f"
echo "   Restart:    sudo systemctl restart byte-bot byte-admin"
