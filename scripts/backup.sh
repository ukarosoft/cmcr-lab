#!/usr/bin/env bash
# backup.sh — Backup PostgreSQL con rotación de 7 días
# Uso: ./scripts/backup.sh
# Requiere: DATABASE_URL en el entorno (o .env cargado)
#
# Cron recomendado (2am diario):
# 0 2 * * * cd /opt/app && /usr/bin/env bash scripts/backup.sh >> /var/log/backup.log 2>&1

set -euo pipefail

# ────────────────────────────────────────────────────────────
# Configuración
# ────────────────────────────────────────────────────────────

BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
DAYS_TO_KEEP="${DAYS_TO_KEEP:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_URL="${DATABASE_URL:-}"
APP_NAME="${APP_NAME:-ukaro}"

# ────────────────────────────────────────────────────────────
# Validaciones
# ────────────────────────────────────────────────────────────

if [ -z "$DB_URL" ]; then
    # Intentar cargar desde .env
    if [ -f ".env" ]; then
        DB_URL=$(grep '^DATABASE_URL=' .env | cut -d '=' -f2-)
    fi
    if [ -z "$DB_URL" ]; then
        echo "[ERROR] DATABASE_URL no está definido. Abortando." >&2
        exit 1
    fi
fi

if ! command -v pg_dump &> /dev/null; then
    echo "[ERROR] pg_dump no encontrado. Instala postgresql-client." >&2
    exit 1
fi

# ────────────────────────────────────────────────────────────
# Crear directorio de backups
# ────────────────────────────────────────────────────────────

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/${APP_NAME}_${TIMESTAMP}.sql.gz"

# ────────────────────────────────────────────────────────────
# Ejecutar backup
# ────────────────────────────────────────────────────────────

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup → $BACKUP_FILE"

if pg_dump "$DB_URL" | gzip > "$BACKUP_FILE"; then
    SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completado. Tamaño: $SIZE"
else
    echo "[ERROR] pg_dump falló." >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

# ────────────────────────────────────────────────────────────
# Rotación: eliminar backups con más de N días
# ────────────────────────────────────────────────────────────

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Eliminando backups con más de ${DAYS_TO_KEEP} días..."
find "$BACKUP_DIR" -name "${APP_NAME}_*.sql.gz" -mtime +"$DAYS_TO_KEEP" -delete

REMAINING=$(find "$BACKUP_DIR" -name "${APP_NAME}_*.sql.gz" | wc -l)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backups actuales: $REMAINING. Listo."
