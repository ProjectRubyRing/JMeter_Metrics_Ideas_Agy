#!/bin/bash
# ==============================================================================
# Script Name: jvm_metrics_collector.sh
# Description: JBoss EAP 8.1 (Java 17/21) on UBI 9.8 用 軽量JVMメトリクス定期採取スクリプト
#              外部ポート(9990)閉塞環境でも、コンテナ内部からローカルソケット/jcmd/jstat
#              を用いてヒープメモリやスレッド状態を定期採取し、JSON形式で標準出力(stdout)に出力。
#              ECSの awslogs ドライバー経由で CloudWatch Logs に自動集約されます。
# ==============================================================================

set -u

# 収集間隔（秒）。JMeter実行中は5秒〜10秒が推奨
INTERVAL="${METRICS_INTERVAL:-5}"

# ログ出力用プレフィックス
LOG_PREFIX="[JVM-METRICS]"

# JBoss EAPのプロセスID (PID) を検索・特定
get_jboss_pid() {
    # 1. jpsコマンドが使える場合
    if command -v jps >/dev/null 2>&1; then
        jps -l | grep -E "jboss-modules.jar|org.jboss.as.standalone" | awk '{print $1}' | head -n 1
        return
    fi
    # 2. psコマンドから検索
    pgrep -f "jboss-modules.jar" | head -n 1
}

echo "$LOG_PREFIX Starting JVM Metrics Collector daemon (Interval: ${INTERVAL}s)..."

# JBossプロセスの起動待ち（最大120秒）
WAIT_COUNT=0
JBOSS_PID=""
while [ -z "$JBOSS_PID" ]; do
    JBOSS_PID=$(get_jboss_pid)
    if [ -n "$JBOSS_PID" ]; then
        break
    fi
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ "$WAIT_COUNT" -ge 24 ]; then
        echo "$LOG_PREFIX WARNING: JBoss EAP process not found after 120s. Retrying..."
        WAIT_COUNT=0
    fi
    sleep 5
done

echo "$LOG_PREFIX Target JBoss EAP process detected (PID: ${JBOSS_PID})."

# JDKツールのパス確認
JSTAT_CMD=$(command -v jstat || echo "")
JCMD_CMD=$(command -v jcmd || echo "")

if [ -z "$JSTAT_CMD" ]; then
    echo "$LOG_PREFIX WARNING: 'jstat' command not found. Please ensure JDK (not just headless JRE) is installed."
fi

# メインループ
while true; do
    # プロセス生存確認
    if ! kill -0 "$JBOSS_PID" 2>/dev/null; then
        echo "$LOG_PREFIX JBoss EAP process (PID: ${JBOSS_PID}) terminated. Searching for new PID..."
        JBOSS_PID=$(get_jboss_pid)
        if [ -z "$JBOSS_PID" ]; then
            sleep "$INTERVAL"
            continue
        fi
    fi

    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    EPOCH_MS=$(date +%s%3N 2>/dev/null || date +%s000)

    # 1. OSレベルのプロセスメモリ・CPU (cgroup/procfs)
    # RSS (Resident Set Size) in KB
    PROC_STAT=$(ps -p "$JBOSS_PID" -o %cpu,%mem,rss,vsz --no-headers 2>/dev/null || echo "0 0 0 0")
    CPU_UTIL=$(echo "$PROC_STAT" | awk '{print $1}')
    MEM_UTIL=$(echo "$PROC_STAT" | awk '{print $2}')
    RSS_KB=$(echo "$PROC_STAT" | awk '{print $3}')
    VSZ_KB=$(echo "$PROC_STAT" | awk '{print $4}')

    # 2. jstat によるヒープ使用率・GC統計 (パーセント及び回数)
    # S0C, S1C, S0U, S1U, EC, EU, OC, OU, MC, MU, CCSC, CCSU, YGC, YGCT, FGC, FGCT, GCT
    JSTAT_OUTPUT=""
    S0U_PCT=0; S1U_PCT=0; EC_PCT=0; OC_PCT=0; MC_PCT=0; CCS_PCT=0
    YGC_CNT=0; YGC_TIME=0; FGC_CNT=0; FGC_TIME=0; GCT_TOTAL=0

    if [ -n "$JSTAT_CMD" ]; then
        # -gcutil は各領域の使用率(%)とGC回数/時間を1行で返す
        JSTAT_RAW=$("$JSTAT_CMD" -gcutil "$JBOSS_PID" 2>/dev/null | tail -n 1)
        if [ -n "$JSTAT_RAW" ]; then
            # 出力例: S0     S1     E      O      M     CCS    YGC     YGCT    FGC    FGCT    CGC    CGCT     GCT
            S0U_PCT=$(echo "$JSTAT_RAW" | awk '{print $1}')
            S1U_PCT=$(echo "$JSTAT_RAW" | awk '{print $2}')
            EC_PCT=$(echo "$JSTAT_RAW" | awk '{print $3}')
            OC_PCT=$(echo "$JSTAT_RAW" | awk '{print $4}')
            MC_PCT=$(echo "$JSTAT_RAW" | awk '{print $5}')
            CCS_PCT=$(echo "$JSTAT_RAW" | awk '{print $6}')
            YGC_CNT=$(echo "$JSTAT_RAW" | awk '{print $7}')
            YGC_TIME=$(echo "$JSTAT_RAW" | awk '{print $8}')
            FGC_CNT=$(echo "$JSTAT_RAW" | awk '{print $9}')
            FGC_TIME=$(echo "$JSTAT_RAW" | awk '{print $10}')
            GCT_TOTAL=$(echo "$JSTAT_RAW" | awk '{print $NF}')
        fi
    fi

    # 3. スレッド数の取得 (/proc/<pid>/status または ps)
    THREAD_COUNT=0
    if [ -f "/proc/$JBOSS_PID/status" ]; then
        THREAD_COUNT=$(grep "^Threads:" "/proc/$JBOSS_PID/status" | awk '{print $2}')
    else
        THREAD_COUNT=$(ps -T -p "$JBOSS_PID" --no-headers 2>/dev/null | wc -l)
    fi

    # 4. JSON形式で構造化ログ出力（CloudWatch Logs Insightsで直接パース可能）
    cat <<EOF
$LOG_PREFIX {"timestamp":"$TIMESTAMP","epoch_ms":$EPOCH_MS,"pid":$JBOSS_PID,"os":{"cpu_pct":$CPU_UTIL,"mem_pct":$MEM_UTIL,"rss_kb":$RSS_KB,"vsz_kb":$VSZ_KB},"jvm":{"threads":$THREAD_COUNT,"heap_usage_pct":{"eden":$EC_PCT,"old":$OC_PCT,"survivor0":$S0U_PCT,"survivor1":$S1U_PCT},"non_heap_usage_pct":{"metaspace":$MC_PCT,"class_space":$CCS_PCT},"gc":{"young_count":$YGC_CNT,"young_time_sec":$YGC_TIME,"full_count":$FGC_CNT,"full_time_sec":$FGC_TIME,"total_time_sec":$GCT_TOTAL}}}
EOF

    sleep "$INTERVAL"
done
