# JBoss EAP 8.1 on ECS (UBI 9.8) JMeter性能テスト向け JVM性能指標・ヒープメモリ収集 完全実践ガイド

---

## 1. はじめに：小学生にもわかる！「コンテナのメモリ」と「Javaのヒープ」のちがい

### 1.1 テーマパークの巨大レストランにたとえてみよう！
あなたが大人気テーマパーク（AWS ECS）の中にある**「超人気洋食レストラン（Javaアプリ）」**の店長さんだと想像してください。
いま、**「1000人の食いしん坊（JMeterの負荷テスト）」**が一気にお店にやってこようとしています！

```
+----------------------------------------------------------------------------------+
|                            AWS ECS タスク (プレハブ店舗)                          |
|                                                                                  |
|  +----------------------------------------------------------------------------+  |
|  |                フロント/バック コンテナ (UBI 9.8 / JBoss EAP 8.1)            |  |
|  |                                                                            |  |
|  |  +----------------------------------------------------------------------+  |  |
|  |  |                       JVM (巨人のシェフ)                              |  |  |
|  |  |                                                                      |  |  |
|  |  |   [作業テーブル: ヒープメモリ]           [レシピ置き場: Metaspace]    |  |  |
|  |  |   ┌──────────────┬──────────────┐                                    |  |  |
|  |  |   │ Young世代    │ Old世代      │                                    |  |  |
|  |  |   │ (新しい皿)   │ (古い鍋)     │        [お掃除小人: ガベージコレクタ] |  |  |
|  |  |   └──────────────┴──────────────┘          (お掃除中は全員ストップ!)  |  |  |
|  |  +----------------------------------------------------------------------+  |  |
|  |                                                                            |  |
|  |   × 非常階段(ポート9990): 厳重に施錠 (外から見えない!)                     |  |
|  +----------------------------------------------------------------------------+  |
|         │                                                                        |
|         │ ループバック通信 (localhost:4317 / gRPC)                               |
|         ▼                                                                        |
|  +----------------------------------------------------------------------------+  |
|  |              ADOT サイドカーコンテナ (隣に立つ記録係の小人さん)              |  |
|  |    受信: OTLP (トレース & メトリクス)                                      |  |
|  |    送信: CloudWatch Logs / Metrics (EMF), AWS X-Ray (Traces)               |  |
|  +----------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------+
```

このレストランには次のような特徴があります：
1. **プレハブの建物（コンテナ / UBI 9.8）**:
   外から見ると「プレハブ小屋」が1つ建っているように見えます。
2. **巨人のシェフ（Java / JBoss EAP 8.1）**:
   プレハブの中で、料理を作りまくる巨人のシェフが働いています。
3. **作業テーブル（ヒープメモリ）**:
   シェフが料理を盛り付けたり、お皿を一時的に置くための作業机です。机がいっぱいになると、新しい料理が作れなくなって倒れてしまいます（これを「OutOfMemoryError: メモリ枯渇」と呼びます）。
4. **お掃除ロボット（ガベージコレクション: GC）**:
   食べ終わったお皿を片付けるお掃除ロボットです。お掃除をするとき、シェフの手がぶつかると危ないので、**シェフに「ちょっとストップ！」と動きを止めさせます（これを「Stop-The-World: STW」と呼びます）**。もしお掃除が長引くと、待たされているお客さん（JMeter）は「料理が全然出てこないぞ！（レスポンス遅延・タイムアウト）」と大怒りします。
5. **非常階段の鉄の扉（ポート9990 / 管理コンソール）**:
   昔はこの扉から外の人が中を覗いて「テーブルはどれくらい散らかっているかな？」と見ていました。でも、泥棒が入ってきたら大変なので、**現在は頑丈な鍵をかけて絶対に開けないように塞いでいます（ポート9990外部接続不可）**。

---

### 1.2 なぜ「コンテナのメモリ（外壁の重さ）」を見るだけではダメなのか？
「AWSの管理画面（CloudWatch）を見れば、コンテナのメモリ使用率（%）がグラフで出ているから、それで十分じゃないの？」と思うかもしれません。
**ここが最大の落とし穴です！**

* **外から見た重さ（コンテナのメモリ / RSS）**:
  外の体重計（CloudWatchのECS標準メトリクス）に乗っかっている「プレハブ小屋全体の重さ」です。
  実はJavaのシェフ（JVM）は、最初に小屋に入った瞬間、**「俺は最大で4GBのテーブルを使う予定だから、4GB分のスペースを予約しておくぞ！」**と部屋を広く陣取ってしまいます。
  そのため、外の体重計から見ると**「常に80%くらい埋まっていて、ほとんど動かない」**ように見えてしまいます。
* **テーブルの上の本当の散らかり具合（Javaヒープメモリ）**:
  実際に作業机の上にお皿が何枚置かれているかは、**小屋の中に潜入してシェフの机を直接測らないと絶対にわかりません**。

1000人の食いしん坊（JMeter）が注文を連打したとき：
* お皿がどれくらいのスピードで積み上がっているか？（ヒープ使用量の急増）
* お掃除ロボットがどれくらいの時間シェフを止めているか？（GC停止時間によるレスポンス遅延）
* 食べた後のゴミ皿が片付かずに机に残ったままになっていないか？（メモリリーク）

これらを調べるためには、**「ポート9990を閉じたまま、プレハブの中から自動で測定結果を外に送り出す仕組み」**が必要になります。

---

## 2. 登場の歴史と背景：なぜこのアーキテクチャが必要になったのか？

なぜ昔のように簡単にメモリが見られなくなり、現在の「OpenTelemetry」や「サイドカー」という仕組みが生まれたのでしょうか？
その歴史の流れを振り返ると、今回の設計理由がはっきりと見えてきます。

```
【歴史の進化フロー】
[第1世代: 物理サーバー時代] ──> [第2世代: コンテナ黎明期] ──> [第3世代: クラウドネイティブ/現在]
・サーバーに直接ログイン         ・Docker登場、軽量化推進      ・Kubernetes / ECS Fargate
・JMX(9990)を直接叩く           ・ポート乱立、セキュリティ懸念 ・マルチテナント & ゼロトラスト
・VisualVMを画面で繋ぐ           ・ポート9990閉鎖の必然性       ・ADOT(サイドカー)によるプッシュ型
                                 ・cgroup制限による強制終了    ・OpenTelemetryによるメトリクス標準化
```

### 第1世代：物理サーバー・オンプレミス時代（直接接続の時代）
* **やり方**: 大きなサーバーマシンにJBossを直接インストール。エンジニアは自席のPCから「VisualVM」や「JConsole」というGUIツールを起動し、JBossの管理ポート（9990や1099など）に直接IPアドレスとポート番号でTCP接続（JMX接続）していました。
* **メリット**: 設定が簡単で、リアルタイムにヒープの折れ線グラフがビジュアルに見えた。
* **限界**: セキュリティがガバガバ。サーバーのポートを外部に開け放つ必要があり、万が一認証が突破されるとサーバーを遠隔操作されてしまう致命的な危険性がありました。

### 第2世代：Dockerコンテナ黎明期（ポート閉鎖とOOM Killerの悲劇）
* **変化**: システムが小さなコンテナ（Docker）に分割され、AWS ECS等のオーケストレーター上で動くようになりました。
* **課題1（セキュリティ）**: コンテナはインターネットや社内ネットワークに直接晒されるため、管理ポート（9990）を不用意に開けることはセキュリティポリシー上、厳格に禁止（閉塞）されるようになりました。
* **課題2（cgroupメモリ制限とOOM Killer）**:
  Java（JVM）は元々物理マシンの全メモリを見て動くように作られていたため、コンテナの「メモリ制限（例: 2GB）」を無視してホストOSのメモリ（例: 64GB）を基準にヒープを確保し、Linuxカーネルの**OOM Killer（強制終了部隊）に前触れなくSIGKILL（即死）させられる障害**が世界中で多発しました。

### 第3世代（現在）：クラウドネイティブと可観測性（OpenTelemetry & サイドカー）
* **解決策**:
  1. **プル型（外から覗きに行く）からプッシュ型（中から送り出す）への転換**:
     外からポートを開けて覗くのをやめ、コンテナ内部から外部の監視基盤へ**「一方通行（アウトバウンド）」でデータを投げつける方式**に進化しました。これなら受信用のポート（9990）を一切開ける必要がありません。
  2. **サイドカーパターン（隣の小人さん）の確立**:
     アプリコンテナの中に重たい監視処理を詰め込むとアプリが遅くなるため、**同じ部屋（ECSタスク）の隣に監視専用の軽量コンテナ（ADOT Collector）を並走**させるアーキテクチャが業界標準になりました。
  3. **OpenTelemetryの標準化**:
     Google、Microsoft、AWS、Red Hatなどが共同で策定した世界標準規格「OpenTelemetry（OTel）」により、トレースだけでなくメトリクスやログも単一の仕組みで扱えるようになりました。

---

## 3. 既存のAWS資産（CloudWatch, S3, ADOT）の徹底活用可否

「すでに動いている CloudWatch Logs、S3、CloudWatchメトリクス、ADOTサイドカー（X-Rayトレース出力中）は今回のヒープメモリ測定に使えるのか？」
結論から言うと、**すべての既存資産を100%フル活用できます！**

| 既存資産 | 現状の用途 | 今回の性能テストでの活用方法 | 判定 |
| :--- | :--- | :--- | :---: |
| **ADOTサイドカー** | X-Rayへトレース情報のみ送信 | **【本命】メトリクスパイプラインを追加し、JVMヒープ・GC・スレッドをCloudWatch Metricsにリアルタイム送信** | **◎ 即座に活用可能** |
| **CloudWatch Logs** | アプリログ・標準出力の集約 | **JDK統一GCログ（-Xlog:gc*）および診断スクリプトのJSON出力を集約し、Insightsでクエリ・グラフ化** | **◎ 即座に活用可能** |
| **S3 バケット** | 静的ファイル・バックアップ | **テスト中のJFR（低負荷プロファイラバイナリ）やOOM発生時のヒープダンプ（.hprof）の退避保存先** | **◎ 即座に活用可能** |
| **CloudWatch標準メトリクス** | ECS CPU/メモリ使用率 | **コンテナ全体の物理メモリ（RSS）とJVMヒープ使用率の乖離（Off-Heap肥大化）の比較対照** | **○ 併用活用** |

---

### 3.1 【最重要】ADOTサイドカーの真価：なぜメトリクスも取れるのか？
現在、ADOTサイドカーはX-Rayトレースのためだけに動いています。
しかし、ADOT（AWS Distro for OpenTelemetry）の実体は、オープンソースの**OpenTelemetry Collector**そのものです。

Collectorの内部には3つの部屋（パイプライン）があります：
1. **Receivers（受取口）**: トレースだけでなく、**メトリクス（OTLP Metrics）も最初から受け取れる口を持っています**。
2. **Processors（加工場）**: 届いたデータに「どのECSタスクか」「どのコンテナか」のタグを自動で貼り付けます。
3. **Exporters（出荷口）**: トレース用の `awsxray` の隣に、**メトリクス用の `awsemf`（AWS Embedded Metric Format）**を並べるだけで、自動的にCloudWatch Metricsにカスタムメトリクスとしてグラフを描画できます。

```
[フロント/バック Javaコンテナ]
    │
    │  OpenTelemetry Java Agent がJVMヒープ・GC・スレッドを自動収集
    │  (内部ループバック: http://localhost:4317 gRPC)  ※外部ポート9990は不要！
    ▼
[ADOT サイドカーコンテナ (同一ECSタスク内)]
    ├── Receivers: otlp (4317/4318) ──> トレースとメトリクスを両方受信
    ├── Processors: batch, resourcedetection ──> ECSメタデータを付加
    └── Exporters:
          ├── awsxray ──> 【既存】AWS X-Ray (分散トレース)
          └── awsemf  ──> 【新規】CloudWatch Metrics (JVMヒープ/GC/スレッド)
```

この設定を追加するだけで、**ポート9990を閉じたまま、JMeter実行中にCloudWatch上でリアルタイムにヒープの推移を監視**できるようになります。

---

## 4. 4大アプローチの比較選定表

JMeter実行時にJavaアプリのヒープ・性能指標を取得するアプローチを比較します。

| アプローチ | 推奨度 | ポート9990閉塞時の可否 | リアルタイム性 | メリット | 留意点・追加実装 |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **方式1: ADOT拡張 (OTel Java Agent + EMF)** | **◎ 最推奨 (本命)** | **完全対応** (タスク内localhostのみ) | **極めて高い** (1〜5秒間隔) | ・既存ADOTサイドカーをフル活用<br>・コード変更ゼロ（Java Agent付与のみ）<br>・CloudWatchでJMeter負荷とヒープを同一画面監視可能 | ・DockerfileにAgent jar配置<br>・ADOT Collector設定にmetrics追加<br>・JBoss Modules競合回避引数の付与 |
| **方式2: JVM Unified GC Logging + CW Logs** | **○ 併用推奨 (精度最高)** | **完全対応** (ファイルまたはstdout) | **中〜低** (事後詳細分析) | ・オーバーヘッドが極小（1%未満）<br>・GC停止時間（STW）をミリ秒単位で完全記録<br>・GCEasyやGCViewerで極めて精緻な診断が可能 | ・standalone.confに-Xlog追記<br>・CloudWatch Logs転送量/コスト考慮 |
| **方式3: コンテナ内定期診断スクリプト** | **○ 併用推奨 (超軽量・手軽)** | **完全対応** (コンテナ内procfs/jstat) | **中** (5秒毎のJSONログ) | ・外部ライブラリ/Agent追加不要<br>・OS物理メモリ(RSS)とJVMヒープを1つのJSONに統合出力可能 | ・entrypointラッパースクリプト作成<br>・JDKツール(jstat, jcmd)のインストール必須 |
| **方式4: Java Flight Recorder (JFR) + S3** | **○ 深堀り用 (最強プロファイラ)** | **完全対応** (S3直接アップロード) | **低** (テスト後分析) | ・メモリ割り当て箇所やメソッド遅延、ロック競合をピンポイント特定<br>・本番稼働可能な超低オーバーヘッド | ・S3書き込み用IAM権限が必要<br>・テスト前後のjcmd実行制御スクリプトが必要 |

---

## 5. 性能テストで絶対に取得すべき「Java性能指標」一覧

JMeter負荷テストの合否判定およびボトルネック調査で必須となる指標です。

### 5.1 ヒープメモリ系指標
1. **JVM Used Heap (`jvm.memory.used`, area=heap)**:
   * **概要**: 実際にオブジェクトが占有しているメモリ量。
   * **判定基準**: 負荷をかけ続けても、GC実行後に一定のベースライン（最大ヒープの50%以下など）まで戻っていれば健全。右肩上がりに増え続け、GC後も下がらなければ**「メモリリーク（Memory Leak）」**と断定できます。
2. **JVM Committed Heap (`jvm.memory.committed`, area=heap)**:
   * **概要**: OSからJVMに物理的に割り当てられたメモリ領域。`-Xms` と `-Xmx` を同値に設定していれば一定値を保ちます。
3. **Eden / Survivor / Old Generation 使用率**:
   * **Eden**: 新しく生成されたインスタンスが置かれる場所。JMeterの秒間リクエスト数に比例して激しく増減します。
   * **Old**: 長生きしているオブジェクトの領域。ここが増え続けると、大規模なGC（Concurrent MarkやFull GC）が誘発されます。

### 5.2 ガベージコレクション（GC）系指標
1. **GC Pause Time (STW停止時間) (`jvm.gc.duration`)**:
   * **概要**: GCのためにJavaアプリの全スレッドが完全停止していた時間。
   * **判定基準**: G1GCの場合、通常**50ms以下（最大でも200ms以内）**に収まるのが理想。
   * **JMeterとの相関**: **「JMeterのレスポンスタイムが急に1秒跳ねた瞬間」と「GC Pause Timeの発生時刻」が完全に一致**する場合、性能劣化の原因はアプリのロジックではなくGCの停止時間にあると特定できます。
2. **GC Overhead (GC CPU専有率)**:
   * **概要**: 全稼働時間のうち、GCのお掃除に奪われた時間の割合。
   * **判定基準**: **2%未満**が健全。5%を超えるとシステム全体が詰まり始めます。

### 5.3 スレッド・リソース系指標
1. **Active Threads / Blocked Threads (`jvm.threads.count`)**:
   * **Blockedスレッド数**: ロック（`synchronized` やリソース競合）で停止しているスレッドの数。これがスパイクすると、JMeterのスループット（TPS）が急落します。
2. **JBoss Undertow ワーカースレッド使用率**:
   * **概要**: HTTPリクエストを受け付けるスレッドプールの枯渇状況。上限に達するとJMeter側でConnection Timeoutが発生します。
3. **プロセス物理メモリ (RSS: Resident Set Size)**:
   * **概要**: OSから見たJavaコンテナの総メモリ消費。コンテナのハードリミット（ECSメモリ制限）の80%を超えないよう監視します。

---

## 6. 実装手順とコード解説

本環境（UBI 9.8 / JBoss EAP 8.1 / ECS / 既存ADOTサイドカー）における具体的な実装内容です。

```
【コンテナ実装資材の配置構成】
/opt/jboss/
  ├── eap/ (JBoss EAP 8.1 本体)
  │    └── bin/
  │         └── standalone.conf (JVM引数・GCログ設定追記)
  ├── otel/
  │    └── opentelemetry-javaagent.jar (OTel Java Agent)
  └── scripts/
       ├── entrypoint_wrapper.sh (起動・シグナル制御)
       ├── jvm_metrics_collector.sh (定期メトリクス採取)
       └── export_jfr_to_s3.sh (JFRオンデマンドS3転送)
```

### 6.1 実装1: Dockerfileの追加修正 (`docker/Dockerfile.eap81_metrics`)
UBI 9.8コンテナにJDK診断ツール、OpenTelemetry Java Agent、各種スクリプトを組み込みます。

```dockerfile
FROM registry.access.redhat.com/ubi9/ubi:9.8

# 1. JDK診断ツール(jstat, jcmd)を含むパッケージをインストール
RUN dnf update -y && \
    dnf install -y --nodocs \
        java-17-openjdk-devel \
        procps-ng \
        findutils \
        tar gzip curl shadow-utils && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# 2. ディレクトリ構成とJBossユーザー(UID: 185)の設定
ENV JBOSS_USER=jboss \
    JBOSS_UID=185 \
    JBOSS_HOME=/opt/jboss/eap \
    SCRIPTS_DIR=/opt/jboss/scripts \
    OTEL_DIR=/opt/jboss/otel

RUN groupadd -r jboss -g ${JBOSS_UID} && \
    useradd -u ${JBOSS_UID} -r -g jboss -m -d /opt/jboss -s /sbin/nologin jboss && \
    mkdir -p ${JBOSS_HOME} ${SCRIPTS_DIR} ${OTEL_DIR} /var/log/jboss

# 3. OpenTelemetry Java Agent を配置
ARG OTEL_AGENT_VERSION="2.1.0"
RUN curl -Lo ${OTEL_DIR}/opentelemetry-javaagent.jar \
    https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v${OTEL_AGENT_VERSION}/opentelemetry-javaagent.jar && \
    chmod 644 ${OTEL_DIR}/opentelemetry-javaagent.jar

# 4. スクリプト群の配置
COPY --chown=jboss:jboss scripts/jvm_metrics_collector.sh ${SCRIPTS_DIR}/jvm_metrics_collector.sh
COPY --chown=jboss:jboss scripts/entrypoint_wrapper.sh ${SCRIPTS_DIR}/entrypoint_wrapper.sh
COPY --chown=jboss:jboss scripts/export_jfr_to_s3.sh ${SCRIPTS_DIR}/export_jfr_to_s3.sh

RUN chmod +x ${SCRIPTS_DIR}/*.sh && \
    chown -R jboss:jboss /opt/jboss /var/log/jboss

# 5. 環境変数設定（JBoss Modules競合回避フラグを含む）
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk \
    PATH=$PATH:/usr/lib/jvm/java-17-openjdk/bin:${SCRIPTS_DIR} \
    OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317" \
    OTEL_EXPORTER_OTLP_PROTOCOL="grpc" \
    OTEL_METRICS_EXPORTER="otlp" \
    OTEL_TRACES_EXPORTER="otlp" \
    OTEL_METRIC_EXPORT_INTERVAL="5000" \
    JAVA_TOOL_OPTIONS="-javaagent:${OTEL_DIR}/opentelemetry-javaagent.jar -Djboss.modules.system.pkgs=io.opentelemetry,jdk.internal.perf,sun.misc"

# 6. ポートは8080のみ公開（管理ポート9990はEXPOSEしない）
EXPOSE 8080

USER 185
WORKDIR ${JBOSS_HOME}
ENTRYPOINT ["/opt/jboss/scripts/entrypoint_wrapper.sh"]
```

---

### 6.2 実装2: JBoss EAP `standalone.conf` のチューニング (`config/standalone.conf.snippet`)
Java 17/21の統一ガベージコレクションログと、G1GC最適化、OOM対策を設定します。

```bash
# ヒープメモリ設定 (コンテナ制限の60〜70%を割り当て)
JAVA_OPTS="$JAVA_OPTS -Xms2048m -Xmx2048m -XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=512m"

# G1GC 最適化設定
JAVA_OPTS="$JAVA_OPTS -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:InitiatingHeapOccupancyPercent=45"

# JDK 17/21 統一JVMガベージコレクションログ (ローテーション付き)
JAVA_OPTS="$JAVA_OPTS -Xlog:gc*,gc+phases=debug:file=/var/log/jboss/gc-%t.log:time,uptime,pid,level,tags:filecount=5,filesize=50M"

# 万が一のOOM発生時に対策
JAVA_OPTS="$JAVA_OPTS -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/log/jboss/heapdump.hprof -XX:+ExitOnOutOfMemoryError"

# JBoss Modules と Java Agent のパッケージ隔離解除
JAVA_OPTS="$JAVA_OPTS -Djboss.modules.system.pkgs=org.jboss.byteman,io.opentelemetry,jdk.internal.perf,sun.misc"

# コンテナリソース自動認識 (cgroup v2対応)
JAVA_OPTS="$JAVA_OPTS -XX:+UseContainerSupport"

export JAVA_OPTS
```

---

### 6.3 実装3: ADOTサイドカー設定の拡張 (`config/adot-collector-ecs-config.yaml`)
既存のX-Rayトレースパイプラインに加えて、**メトリクスパイプラインと `awsemf` エクスポーターを追加**します。

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  awsxray:
    endpoint: 0.0.0.0:2000
    transport: udp

processors:
  batch:
    timeout: 5s
    send_batch_size: 256
  resourcedetection:
    detectors: [ecs, env]
    timeout: 2s

exporters:
  # 既存: X-Ray トレース
  awsxray:
    region: ap-northeast-1

  # 【新規追加】CloudWatch EMF エクスポーター (JVMメトリクスをCloudWatch Metricsへ転送)
  awsemf:
    region: ap-northeast-1
    log_group_name: "/aws/ecs/application/jvm-metrics"
    log_stream_name: "{TaskId}"
    namespace: "ECS/JVM/JBossEAP"
    dimension_rollup_option: "NoDimensionRollup"
    metric_declarations:
      - dimensions: [[ClusterName, TaskDefinitionFamily, area]]
        metric_name_selectors:
          - "jvm.memory.used"
          - "jvm.memory.committed"
          - "jvm.memory.max"
      - dimensions: [[ClusterName, TaskDefinitionFamily, gc]]
        metric_name_selectors:
          - "jvm.gc.duration"
      - dimensions: [[ClusterName, TaskDefinitionFamily, state]]
        metric_name_selectors:
          - "jvm.threads.count"

service:
  pipelines:
    traces:
      receivers: [otlp, awsxray]
      processors: [batch, resourcedetection]
      exporters: [awsxray]
    metrics:
      receivers: [otlp]
      processors: [batch, resourcedetection]
      exporters: [awsemf]
```

---

### 6.4 実装4: コンテナ内定期メトリクス採取スクリプト (`scripts/jvm_metrics_collector.sh`)
外部ポートに頼らず、コンテナローカルで `jstat` と `/proc` を使って5秒毎にJSON形式で標準出力に出力します。

```bash
# (抜粋) 5秒毎にJSON形式で出力
cat <<EOF
[JVM-METRICS] {"timestamp":"$TIMESTAMP","epoch_ms":$EPOCH_MS,"pid":$JBOSS_PID,"os":{"cpu_pct":$CPU_UTIL,"mem_pct":$MEM_UTIL,"rss_kb":$RSS_KB},"jvm":{"threads":$THREAD_COUNT,"heap_usage_pct":{"eden":$EC_PCT,"old":$OC_PCT,"survivor":$S0U_PCT},"gc":{"young_count":$YGC_CNT,"young_time_sec":$YGC_TIME,"full_count":$FGC_CNT,"total_time_sec":$GCT_TOTAL}}}
EOF
```

このログはECSの `awslogs` ログドライバーによってCloudWatch Logsへ自動転送されます。
**CloudWatch Logs Insights** を使えば、以下のようなクエリで即座に時系列集計・グラフ化が可能です：

```sql
fields @timestamp, jvm.heap_usage_pct.old as OldGenPct, jvm.threads as Threads, os.rss_kb / 1024 as RSS_MB
| filter @message like /\[JVM-METRICS\]/
| sort @timestamp asc
| limit 1000
```

---

## 7. JMeterテスト実施時の相関分析シナリオ（トラブル診断フロー）

JMeterで負荷をかけている最中、以下の3ステップで相関分析を行います。

```
[ステップ1: JMeter結果]      [ステップ2: CloudWatch Metrics]      [ステップ3: X-Ray & GCログ]
レスポンス遅延スパイク発生 ──> JVM GC Pause Time が同刻に急増 ──> X-Rayで該当リクエストを特定
(例: 14:15:30 に10秒遅延)     (例: 14:15:30 にSTW 8000ms)          GCログでOld領域溢れを確認
                                                                  └─> 根本原因: メモリ不足/GC詰まり
```

1. **メモリリークの診断**:
   * JMeterの負荷シナリオを「一定負荷で30分間」実行。
   * CloudWatchの `jvm.memory.used`（area=heap）を監視。
   * **正常**: 鋸歯状（のこぎり型）に上下を繰り返し、GC後の最低値が一定。
   * **異常（リーク）**: GCが発生してもOld領域の使用量が右肩上がりに上昇。最終的にFull GCが連発し、スループットがゼロに落ちる。
2. **レスポンス遅延（スパイク）の診断**:
   * JMeterで「最大レスポンスタイム」が異常値を示した時刻を記録。
   * ADOT経由で収集された `jvm.gc.duration` の最大値グラフと突き合わせる。
   * 完全一致していれば、アプリのDBクエリ遅延等ではなく「GCのStop-The-World」が原因と特定可能。

---

## 8. まとめと納品物一覧

管理ポート9990を外部に一切開けることなく、既存のADOTサイドカーとCloudWatch基盤を活用して最高精度の性能測定が実現できます。

* **Excel仕様書**: [JMeter_JVM_Metrics_Specification.xlsx](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/JMeter_JVM_Metrics_Specification.xlsx)
  * フォント: `Meiryo UI`
  * デザイン: 洗練されたモノトーンベース（チャコール/スレート/ライトグレー）
  * シート構成: 概要・方式比較、取得必須メトリクス一覧、ADOT・CloudWatch連携仕様、スクリプト＆JVM引数仕様、UBI9・EAP8.1・cgroupv2留意点
* **コンテナ実装スクリプト**:
  * [scripts/jvm_metrics_collector.sh](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/scripts/jvm_metrics_collector.sh)
  * [scripts/entrypoint_wrapper.sh](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/scripts/entrypoint_wrapper.sh)
  * [scripts/export_jfr_to_s3.sh](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/scripts/export_jfr_to_s3.sh)
* **設定ファイル・Dockerfile**:
  * [docker/Dockerfile.eap81_metrics](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/docker/Dockerfile.eap81_metrics)
  * [config/standalone.conf.snippet](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/config/standalone.conf.snippet)
  * [config/adot-collector-ecs-config.yaml](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/config/adot-collector-ecs-config.yaml)
  * [config/ecs-task-definition-snippet.json](file:///C:/Users/taka_/Agy/JMeter_Metrics_Ideas_Agy/config/ecs-task-definition-snippet.json)
