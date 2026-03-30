#!/bin/bash
# AI-Workhorse Deterministisches Backup-Skript (Woche 11-12)
# Sichert die PostgreSQL-Datenbank und das Upload-Verzeichnis.

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="ai-workhorse-db"
DB_USER="workhorse"
DB_NAME="workhorse_db"

echo "🚀 Starte AI-Workhorse Backup ($DATE)..."

# 1. Backup-Verzeichnis erstellen
mkdir -p "$BACKUP_DIR"

# 2. PostgreSQL Dump (pg_dump)
echo "📦 Erstelle Datenbank-Dump..."
docker exec -t "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -F c > "$BACKUP_DIR/db_backup_$DATE.dump"

if [ $? -eq 0 ]; then
    echo "✅ Datenbank-Dump erfolgreich: $BACKUP_DIR/db_backup_$DATE.dump"
else
    echo "❌ Fehler beim Datenbank-Dump!"
    exit 1
fi

# 3. Upload-Verzeichnis sichern (tar.gz)
echo "📁 Sichere Upload-Verzeichnis..."
tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" -C . uploads/

if [ $? -eq 0 ]; then
    echo "✅ Upload-Verzeichnis gesichert: $BACKUP_DIR/uploads_backup_$DATE.tar.gz"
else
    echo "❌ Fehler beim Sichern des Upload-Verzeichnisses!"
    exit 1
fi

echo "🎉 Backup abgeschlossen. Alle Daten liegen in $BACKUP_DIR/"
