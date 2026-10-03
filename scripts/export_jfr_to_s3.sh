#!/bin/bash
# ==============================================================================
# Script Name: export_jfr_to_s3.sh
# Description: Java Flight Recorder (JFR) をオンデマンドで開始/停止し、
#              結果の .jfr ファイルを S3 バケットへ自動アップロードするスクリプト。
#              JMeter 実行中の詳細プロファイリング（ヒープ割り当て、メソッド遅延、
#              スレッド競合）をオーバーヘッド 1% 未満でピンポイント採取可能です。
# Usage:
#   ./export_jfr_to_s3.sh start [DURATION_MINUTES]
#   ./export_jfr_to_s3.sh stop
#   ./export_jfr_to_s3.sh dump
# ==============================================================================

set -euo pipefail

ACTION="${1:-dump}"
DURATION="${2:-10}" # 分単位（デフォルト10分）
JFR_DIR="/tmp/jfr"
S3_BUCKET="${METRICS_S3_BUCKET:-my-jmeter-performance-bucket}"
S3_PREFIX="${METRICS_S3_PREFIX:-jfr-recordings}"

mkdir -p "$JFR_DIR"

get_jboss_pid() {
    pgrep -f "jboss-modules.jar" | head -n 1
}

JBOSS_PID=$(get_jboss_pid)
if [ -z "$JBOSS_PID" ]; then
    echo "ERROR: JBoss EAP process not found."
    exit 1
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="jfr_recording_${HOSTNAME}_${TIMESTAMP}.jfr"
FILEPATH="${JFR_DIR}/${FILENAME}"

case "$ACTION" in
    start)
        echo "Starting JFR continuous recording for ${DURATION}m (PID: ${JBOSS_PID})..."
        # disk=true, maxsize=500m, dumponexit=true
        jcmd "$JBOSS_PID" JFR.start name="JMeter_Test_${TIMESTAMP}" settings=profile duration="${DURATION}m" filename="$FILEPATH"
        echo "JFR started. File will be written to: $FILEPATH"
        ;;
    dump)
        echo "Dumping current JFR recording (PID: ${JBOSS_PID})..."
        jcmd "$JBOSS_PID" JFR.dump filename="$FILEPATH"
        echo "JFR dumped to: $FILEPATH"
        
        if command -v aws >/dev/null 2>&1; then
            echo "Uploading $FILEPATH to s3://${S3_BUCKET}/${S3_PREFIX}/${FILENAME}..."
            aws s3 cp "$FILEPATH" "s3://${S3_BUCKET}/${S3_PREFIX}/${FILENAME}"
            echo "Upload complete: s3://${S3_BUCKET}/${S3_PREFIX}/${FILENAME}"
        else
            echo "AWS CLI not found. File remains at: $FILEPATH"
        fi
        ;;
    stop)
        echo "Stopping JFR recordings (PID: ${JBOSS_PID})..."
        jcmd "$JBOSS_PID" JFR.stop
        echo "JFR stopped."
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Usage: $0 {start|dump|stop} [duration_minutes]"
        exit 1
        ;;
esac
