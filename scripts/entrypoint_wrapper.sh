#!/bin/bash
# ==============================================================================
# Script Name: entrypoint_wrapper.sh
# Description: JBoss EAP 8.1 コンテナ起動ラッパースクリプト
#              JVMメトリクス採取スクリプトをバックグラウンド起動し、
#              JBoss EAP (standalone.sh) をフォアグラウンド実行して
#              ECSのSIGTERMシグナルを適切にトラップ・停止処理を行います。
# ==============================================================================

set -e

JBOSS_HOME="${JBOSS_HOME:-/opt/jboss/eap}"
SCRIPTS_DIR="${SCRIPTS_DIR:-/opt/jboss/scripts}"

# シグナルハンドラ（ECSタスク終了時のクレースフルシャットダウン用）
term_handler() {
    echo "[ENTRYPOINT] Caught SIGTERM/SIGINT signal. Shutting down gracefully..."
    if [ -n "$METRICS_PID" ] && kill -0 "$METRICS_PID" 2>/dev/null; then
        echo "[ENTRYPOINT] Stopping metrics collector (PID: $METRICS_PID)..."
        kill "$METRICS_PID" 2>/dev/null || true
    fi
    if [ -n "$JBOSS_PID" ] && kill -0 "$JBOSS_PID" 2>/dev/null; then
        echo "[ENTRYPOINT] Stopping JBoss EAP (PID: $JBOSS_PID)..."
        kill -15 "$JBOSS_PID" 2>/dev/null || true
        wait "$JBOSS_PID"
    fi
    echo "[ENTRYPOINT] Shutdown complete."
    exit 0
}

trap 'term_handler' SIGTERM SIGINT

# 1. メトリクス収集スクリプトの起動（有効化されている場合）
ENABLE_METRICS_DAEMON="${ENABLE_METRICS_DAEMON:-true}"
METRICS_PID=""

if [ "$ENABLE_METRICS_DAEMON" = "true" ] && [ -f "$SCRIPTS_DIR/jvm_metrics_collector.sh" ]; then
    echo "[ENTRYPOINT] Launching JVM metrics collector in background..."
    /bin/bash "$SCRIPTS_DIR/jvm_metrics_collector.sh" &
    METRICS_PID=$!
    echo "[ENTRYPOINT] Metrics collector started with PID: $METRICS_PID"
fi

# 2. JBoss EAP 8.1 の起動
echo "[ENTRYPOINT] Starting JBoss EAP 8.1 standalone server..."
"$JBOSS_HOME/bin/standalone.sh" -b 0.0.0.0 "$@" &
JBOSS_PID=$!

# JBossプロセスの終了待ち
wait "$JBOSS_PID"
EXIT_CODE=$?

# メトリクス収集デーモンの終了
if [ -n "$METRICS_PID" ] && kill -0 "$METRICS_PID" 2>/dev/null; then
    kill "$METRICS_PID" 2>/dev/null || true
fi

echo "[ENTRYPOINT] JBoss EAP exited with code $EXIT_CODE"
exit $EXIT_CODE
