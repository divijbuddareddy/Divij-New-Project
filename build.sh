#!/usr/bin/env bash
set -e

echo "==> Building Next.js Frontend static export..."
cd frontend
npm install
npm run build
cd ..

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Unified Build Finished Successfully!"
