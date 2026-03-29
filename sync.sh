#!/bin/bash
# AI-Workhorse Vibe-Coding Sync Script
# Macht das Pushen vom Tablet aus maximal reibungslos.

echo "🚀 Starte Vibe-Sync..."
git add .
git commit -m "Vibe-Update"
git push
echo "✅ Sync abgeschlossen."
