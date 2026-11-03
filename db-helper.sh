#!/bin/bash

# 定義容器名稱與備份目錄
CONTAINER_NAME="aipe04-postgres"
DB_USER="aipe04"
DB_NAME="aipe04"
BACKUP_DIR="./db-backups"
BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).sql"

mkdir -p ${BACKUP_DIR}

case "$1" in
    backup)
        echo "⏳ 正在備份資料庫..."
        docker exec -t ${CONTAINER_NAME} pg_dumpall -U ${DB_USER} > ${BACKUP_FILE}
        echo "✅ 備份成功！檔案儲存於: ${BACKUP_FILE}"
        ;;
    restore)
        # 尋找最新的一份備份檔案
        LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/*.sql 2>/dev/null | head -n 1)
        if [ -z "${LATEST_BACKUP}" ]; then
            echo "❌ 找不到任何備份檔案 (.sql)！"
            exit 1
        fi
        echo "⏳ 正在從最新的備份檔案還原: ${LATEST_BACKUP}..."
        cat "${LATEST_BACKUP}" | docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}
        echo "✅ 資料庫還原完成！"
        ;;
    *)
        echo "使用說明:"
        echo "  bash db-helper.sh backup  -> 執行資料庫備份"
        echo "  bash db-helper.sh restore -> 從最新紀錄還原資料庫"
        ;;
esac
