#!/bin/bash
# Railway build script for Playwright

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers..."
playwright install chromium chromium-headless-shell

echo "📚 Installing system dependencies for Playwright..."
playwright install-deps chromium

echo "✅ Build complete!"
