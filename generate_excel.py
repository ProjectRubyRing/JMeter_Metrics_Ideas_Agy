# -*- coding: utf-8 -*-
"""
generate_excel.py
JMeter JVM性能指標収集 設計仕様書 (Excel) 自動生成スクリプト
Meiryo UIフォント、モノトーンベースの美しいデザイン、セル折り返し・幅・罫線を完全設定
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_specification_excel():
    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # スタイル定義 (Meiryo UI & モノトーン)
    # -------------------------------------------------------------
    font_name = "Meiryo UI"
    
    title_font = Font(name=font_name, size=14, bold=True, color="FFFFFF")
    section_font = Font(name=font_name, size=11, bold=True, color="FFFFFF")
    header_font = Font(name=font_name, size=10, bold=True, color="FFFFFF")
    bold_font = Font(name=font_name, size=9.5, bold=True, color="212529")
    regular_font = Font(name=font_name, size=9.5, color="212529")
    code_font = Font(name="Consolas", size=9, color="212529")
    note_font = Font(name=font_name, size=9, italic=True, color="495057")
    
    # モノトーンカラー
    title_fill = PatternFill(start_color="1E2227", end_color="1E2227", fill_type="solid")      # 超濃いダークグレー
    header_fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")     # チャコールグレー
    section_fill = PatternFill(start_color="495057", end_color="495057", fill_type="solid")   # スレートグレー
    sub_fill = PatternFill(start_color="6C757D", end_color="6C757D", fill_type="solid")       # ミディアムグレー
    zebra_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")     # 極薄グレー
    highlight_fill = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid") # 薄いグレー強調
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    
    # バッジ用
    badge_best_fill = PatternFill(start_color="212529", end_color="212529", fill_type="solid")
    badge_best_font = Font(name=font_name, size=9, bold=True, color="FFFFFF")
    badge_good_fill = PatternFill(start_color="E2E3E5", end_color="E2E3E5", fill_type="solid")
    badge_good_font = Font(name=font_name, size=9, bold=True, color="383D41")
    
    # 罫線
    thin_side = Side(style='thin', color="CED4DA")
    thick_bottom = Side(style='medium', color="343A40")
    double_bottom = Side(style='double', color="343A40")
    border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    border_header = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thick_bottom)
    border_summary = Border(left=thin_side, right=thin_side, top=thin_side, bottom=double_bottom)
    
    # 配置
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=True)
    align_title = Alignment(horizontal="left", vertical="center")

    # =========================================================================
    # Sheet 1: 方式比較 (Architecture & Approaches)
    # =========================================================================
    ws1 = wb.active
    ws1.title = "概要・方式比較"
    ws1.views.sheetView[0].showGridLines = True
    
    # タイトル
    ws1.merge_cells("A1:G1")
    ws1["A1"] = "JBoss EAP 8.1 on ECS (UBI9.8) JMeter性能テスト向け JVMメトリクス収集方式 比較・選定表"
    ws1["A1"].font = title_font
    ws1["A1"].fill = title_fill
    ws1["A1"].alignment = align_title
    ws1.row_dimensions[1].height = 36
    
    # 前提条件サマリ
    ws1.merge_cells("A2:G2")
    ws1["A2"] = "【前提条件】管理ポート9990閉塞 / UBI 9.8 / JBoss EAP 8.1 (Java 17/21) / ECSタスク内フロント・バック構成 / ADOTサイドカー稼働中(X-Rayトレースのみ)"
    ws1["A2"].font = bold_font
    ws1["A2"].fill = highlight_fill
    ws1["A2"].alignment = align_left
    ws1.row_dimensions[2].height = 24
    
    headers_s1 = ["方式 / アプローチ", "推奨度", "動作原理と連携ルート", "ポート9990閉塞時の対応", "リアルタイム性", "メリット", "留意点・追加実装"]
    for col_idx, h in enumerate(headers_s1, start=1):
        cell = ws1.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border_header
    ws1.row_dimensions[3].height = 28
    
    data_s1 = [
        [
            "方式1: ADOTサイドカー拡張\n(OTel Java Agent + EMF)",
            "◎ 最推奨\n(本命)",
            "JavaアプリにOpenTelemetry Java Agentを付与。タスク内localhost:4317(gRPC)で既存ADOTサイドカーにJVMメトリクスを送信。ADOTがCloudWatch EMF経由でCloudWatch Metricsに自動転送。",
            "外部ポート一切不要\n(タスク内awsvpcのlocalhostループバック通信のみで完結)",
            "高\n(1〜5秒間隔でCW Metricsにリアルタイムグラフ描画)",
            "・既存ADOTサイドカーの資産を100%活用可能\n・コード改修ゼロ(Java Agentのみ)\n・JMeter実行中にCloudWatchダッシュボードでヒープ、GC、スレッドをリアルタイム監視可能\n・X-RayトレースとJVMメトリクスの相関分析が可能",
            "・Dockerfileにopentelemetry-javaagent.jarの追加\n・ADOT Collector設定(YAML)にmetricsパイプラインとawsemfエクスポーターを追加\n・JBoss Modules競合回避フラグの付与"
        ],
        [
            "方式2: JVM Unified GC Logging\n+ CloudWatch Logs",
            "○ 併用推奨\n(精度最強)",
            "JDK 17/21の標準統一ログ機能(-Xlog:gc*)でGC詳細をファイルまたはstdoutに出力。stdout出力ならECS awslogsがCloudWatch Logsへ自動転送。ファイルならS3へ退避。",
            "外部ポート一切不要\n(JVM内部機能のみでログ出力)",
            "中〜低\n(テスト後の一括解析、またはCloudWatch Logs Insightsで集計)",
            "・オーバーヘッドが極小(1%未満)\n・GCの一時停止時間(STW)、Young/Old世代推移、ヒープ確保量をミリ秒単位で完全記録\n・GCEasyやGCViewer等の可視化ツールに投入し極めて精緻な診断が可能",
            "・standalone.confに-Xlogオプションを追記\n・CloudWatch Logsに出す場合はログ転送コスト(PutLogEvents)を考慮\n・リアルタイム監視というよりは事後詳細分析向き"
        ],
        [
            "方式3: コンテナ内定期診断スクリプト\n(jstat / jcmd / ps)",
            "○ 併用推奨\n(超軽量・確実)",
            "コンテナ起動時に軽量シェルスクリプトをバックグラウンド実行。5秒毎にjstat -gcutilやprocfs(/proc)を読み、JSON形式でstdoutに出力。CloudWatch Logsへ流す。",
            "外部ポート一切不要\n(コンテナローカル内のプロセス間通信・procfs読み取り)",
            "中\n(CloudWatch Logs Insightsでリアルタイム検索・グラフ化)",
            "・外部ライブラリやAgent追加が不要\n・コンテナ内のスクリプトのみで完結するため最も手軽\n・OSレベルのRSS(物理メモリ)とJVM内部ヒープを同時に1行のJSONで記録可能",
            "・Dockerfileにスクリプト配置とentrypointラッパーの実装\n・JDK(jstat/jcmd)がコンテナ内にインストールされている必要あり(JRE単体では不可)"
        ],
        [
            "方式4: Java Flight Recorder (JFR)\n+ S3自動アップロード",
            "○ 深堀り用\n(プロファイル)",
            "JDK組み込みの超低負荷プロファイラJFRをJMeter実行中に起動。テスト終了後にjcmdで.jfrバイナリをダンプし、S3バケットへアップロード。JDK Mission Control(JMC)で開く。",
            "外部ポート一切不要\n(ローカルファイル出力 & S3へのHTTPS外部送信)",
            "低 (事後分析)\nテスト終了後にJMCで深堀り",
            "・メソッド単位のCPU消費、メモリ割り当てのホットスポット、スレッドロック競合を完全可視化\n・本番環境でも稼働可能な商用レベルの低負荷\n・ヒープダンプと異なり数GBのメモリ停止を起こさない",
            "・S3アップロード用のIAMロール(PutObject)が必要\n・JFRの開始・停止を制御するスクリプトまたはECS Exec実行が必要\n・ファイルサイズが大きくなるため定期的なS3ライフサイクル管理が必要"
        ],
        [
            "方式5: JMX Prometheus Exporter\n+ ポート内部公開",
            "△ 非推奨\n(制約あり)",
            "JMX Exporter Java Agentを組み込み、ポート(例:9404)でPrometheus形式メトリクスを公開。ADOTサイドカーのPrometheusレシーバーでスクレイピング。",
            "ポート9990は不要だが、タスク内または別ポートの開放が必要",
            "高\n(Prometheus経由でリアルタイム収集)",
            "・Prometheus/Grafanaエコシステムと親和性が高い\n・JBoss EAPの管理MIBやDataSource JMXメトリクスを取得可能",
            "・方式1(OTel Agent)に比べて設定が複雑\n・JBoss EAP 8.1のJMX MBeanサーバーへのアクセス権限設定や認証が必要になる場合がある"
        ]
    ]
    
    current_row = 4
    for r_idx, row_data in enumerate(data_s1):
        for c_idx, val in enumerate(row_data):
            cell = ws1.cell(row=current_row, column=c_idx+1, value=val)
            cell.font = regular_font
            cell.border = border_cell
            
            # 推奨度カラムのバッジ装飾
            if c_idx == 1:
                cell.alignment = align_center
                if "最推奨" in val:
                    cell.fill = badge_best_fill
                    cell.font = badge_best_font
                else:
                    cell.fill = badge_good_fill
                    cell.font = badge_good_font
            elif c_idx in [0, 3]:
                cell.alignment = align_center
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            else:
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
        
        ws1.row_dimensions[current_row].height = 70
        current_row += 1

    # 結論・推奨組み合わせ
    ws1.merge_cells(f"A{current_row}:G{current_row}")
    rec_text = "【性能テスト推奨ベストプラクティス構成】\n" \
               "① リアルタイム監視・アラート: 【方式1】ADOTサイドカー拡張 (OTel Java Agent → ADOT → CloudWatch Metrics)\n" \
               "② GC詳細・ボトルネック分析: 【方式2】JVM Unified GC Logging (-Xlog:gc* → CloudWatch Logs / S3)\n" \
               "③ コードレベル深堀り: 性能劣化やメモリリーク発生時のみ【方式4】JFRをオンデマンド実行しS3へ退避"
    cell_rec = ws1.cell(row=current_row, column=1, value=rec_text)
    cell_rec.font = bold_font
    cell_rec.fill = highlight_fill
    cell_rec.alignment = align_left
    cell_rec.border = border_summary
    ws1.row_dimensions[current_row].height = 65

    # 列幅設定
    col_widths_s1 = [24, 14, 38, 22, 18, 36, 36]
    for i, w in enumerate(col_widths_s1, start=1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # Sheet 2: 取得必須メトリクス仕様 (Required Metrics)
    # =========================================================================
    ws2 = wb.create_sheet(title="取得必須メトリクス一覧")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells("A1:G1")
    ws2["A1"] = "JMeter負荷テスト時に必ず取得・監視すべき Java / JVM 性能指標一覧仕様"
    ws2["A1"].font = title_font
    ws2["A1"].fill = title_fill
    ws2["A1"].alignment = align_title
    ws2.row_dimensions[1].height = 36
    
    headers_s2 = ["カテゴリ", "性能指標名 (メトリクス)", "OpenTelemetry / 指標キー", "単位", "取得元 / ツール", "正常値の目安 / 閾値", "性能テストでの着眼点・トラブル兆候"]
    for col_idx, h in enumerate(headers_s2, start=1):
        cell = ws2.cell(row=2, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border_header
    ws2.row_dimensions[2].height = 28
    
    data_s2 = [
        # ヒープメモリ
        ["ヒープメモリ", "ヒープ使用量 (Used)", "jvm.memory.used (area=heap)", "Bytes / MB", "ADOT / jstat / GC Log", "最大ヒープ(-Xmx)の70〜80%以下で推移", "JMeter負荷に伴い右肩上がりに増加し、GC後も下がらない場合は『メモリリーク』の疑い。"],
        ["ヒープメモリ", "コミット済みヒープ (Committed)", "jvm.memory.committed (area=heap)", "Bytes / MB", "ADOT / jstat", "-Xms 〜 -Xmx の範囲", "OSからJVMへ物理的に割り当てられたメモリ。急激な拡張はOS側のページフォルトを誘発。"],
        ["ヒープメモリ", "最大ヒープ (Max)", "jvm.memory.max (area=heap)", "Bytes / MB", "ADOT / JVM引数", "固定値 (-Xmx)", "コンテナ割り当てメモリの60〜75%程度に抑え、Off-HeapやOS領域を残す。"],
        ["世代別ヒープ", "Eden領域使用率", "jvm.memory.used (id=G1 Eden Space)", "% / Bytes", "ADOT / jstat -gcutil", "鋸歯状 (のこぎり型) に変動", "オブジェクト生成が激しいとEdenが急速に枯渇し、Young GC頻度が増加してCPUを浪費。"],
        ["世代別ヒープ", "Survivor領域使用率", "jvm.memory.used (id=G1 Survivor Space)", "% / Bytes", "ADOT / jstat -gcutil", "閾値以下で推移", "短命オブジェクトがSurvivorからOld領域へ溢れ出る(Tenuring Threshold崩壊)原因を検知。"],
        ["世代別ヒープ", "Old (Tenured) 領域使用率", "jvm.memory.used (id=G1 Old Gen)", "% / Bytes", "ADOT / jstat -gcutil", "GC後に20〜50%程度まで回復すること", "Old領域がGC後も減少しない場合、セッション残留やキャッシュ肥大によるリークが発生。"],
        
        # ガベージコレクション (GC)
        ["GC (ガベージコレクタ)", "GC停止時間 (STW Pause Time)", "jvm.gc.duration", "Milliseconds", "ADOT / GC Log / JFR", "Young GC: 20〜50ms以下\n許容: 200ms以下", "JMeterのレスポンスタイムのスパイク(遅延急増)とGC停止時間の発生時刻が完全に一致するか検証。"],
        ["GC (ガベージコレクタ)", "GC実行頻度 / 回数", "jvm.gc.duration (count)", "回/分", "ADOT / jstat / GC Log", "Young GC: 毎分2〜6回程度", "頻繁なGC(毎秒複数回など)はスループット低下とCPU高騰の主因。オブジェクト大量生成を疑う。"],
        ["GC (ガベージコレクタ)", "Full GC (Stop-the-World)", "jvm.gc.duration (action=end of major gc)", "回数 / 秒", "ADOT / GC Log", "0回 (テスト期間中一切発生しないこと)", "G1GCでFull GCが発生するのはヒープ枯渇やメタスペース枯渇の危険信号。即座に対処必須。"],
        ["GC (ガベージコレクタ)", "GCスループットオーバーヘッド", "GC経過時間 / テスト総時間", "%", "GC Log / GCEasy", "2%未満 (理想は1%未満)", "全CPU時間のうちGCに費やされた割合。5%を超えるとシステム全体が詰まり始める。"],
        
        # 非ヒープ・メタスペース
        ["非ヒープメモリ", "Metaspace使用量", "jvm.memory.used (id=Metaspace)", "Bytes / MB", "ADOT / jstat", "起動後に安定し横ばい", "動的クラス生成(CGLIB, リフレクション)によるリーク。MaxMetaspaceSize未設定だとOOM Killer発動。"],
        ["非ヒープメモリ", "Direct Memory (オフヒープ)", "jvm.buffer.memory.used", "Bytes / MB", "ADOT / JMX", "MaxDirectMemorySize以内", "Netty(Undertow)やDBクライアントが使用するダイレクトバッファの枯渇・リーク検知。"],
        
        # スレッド・コンカレンシー
        ["スレッド", "JVM稼働スレッド数", "jvm.threads.count (state=live)", "個", "ADOT / procfs / JFR", "負荷に応じて増加後、上限で頭打ち", "スレッドが右肩上がりに増え続ける場合、外部APIやDB呼び出しのタイムアウト詰まりを疑う。"],
        ["スレッド", "ブロック中スレッド数", "jvm.threads.count (state=blocked)", "個", "ADOT / JFR", "極小 (0〜数個)", "同期化(synchronized)やロック競合によりスレッドが停止。JMeterのスループット頭打ちの原因。"],
        ["スレッド", "JBoss Undertow ワーカースレッド", "jboss.as:subsystem=io,worker=default", "個 / %", "JMX / JBoss CLI", "最大プールサイズ(max-threads)以下", "Webリクエスト受付スレッドが枯渇するとJMeter側でConnection Timeoutや503が発生。"],
        
        # コネクションプール & OS
        ["DB接続プール", "Active / In-use Connections", "jboss.as:subsystem=datasources...", "個", "JMX / JBoss CLI", "プール上限(max-pool-size)の80%以下", "DBコネクション枯渇はレスポンス遅延の最大要因。リークや返却漏れを検知。"],
        ["OS / プロセス", "プロセスメモリ (RSS)", "process.resident_memory / ps rss", "Bytes / MB", "ADOT / procfs / ps", "コンテナメモリ上限の85%以下", "JVMヒープ + Metaspace + スレッドスタック + ネイティブ領域の合算。コンテナOOM Killerを回避。"],
        ["OS / プロセス", "オープンファイルディスクリプタ数", "process.open_file_descriptors", "個", "ADOT / procfs", "ulimit (通常65535) 以内", "ソケットやファイルのClose漏れ(Too many open filesエラー)を検知。"]
    ]
    
    current_row = 3
    for r_idx, row_data in enumerate(data_s2):
        for c_idx, val in enumerate(row_data):
            cell = ws2.cell(row=current_row, column=c_idx+1, value=val)
            cell.font = regular_font
            cell.border = border_cell
            
            if c_idx in [0, 3]:
                cell.alignment = align_center
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            elif c_idx == 2:
                cell.font = code_font
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            else:
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
                
        ws2.row_dimensions[current_row].height = 36
        current_row += 1
        
    col_widths_s2 = [18, 26, 34, 14, 20, 28, 42]
    for i, w in enumerate(col_widths_s2, start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # Sheet 3: ADOT・CloudWatch連携仕様 (ADOT & CloudWatch Architecture)
    # =========================================================================
    ws3 = wb.create_sheet(title="ADOT・CloudWatch連携仕様")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3.merge_cells("A1:G1")
    ws3["A1"] = "既存ADOTサイドカー(X-Rayトレース)からJVMメトリクス拡張への移行アーキテクチャ仕様"
    ws3["A1"].font = title_font
    ws3["A1"].fill = title_fill
    ws3["A1"].alignment = align_title
    ws3.row_dimensions[1].height = 36
    
    headers_s3 = ["レイヤー / 対象", "コンポーネント", "設定項目 / パラメータ名", "設定値 / 推奨値", "通信プロトコル / ポート", "役割と動作原理", "備考・注意点"]
    for col_idx, h in enumerate(headers_s3, start=1):
        cell = ws3.cell(row=2, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border_header
    ws3.row_dimensions[2].height = 28
    
    data_s3 = [
        ["アプリ側 (Java)", "OTel Java Agent", "-javaagent:/path/to/opentelemetry-javaagent.jar", "JAVA_TOOL_OPTIONS等で付与", "JVM内インプロセス (0ms)", "Javaプロセスのバイトコードを起動時に改変し、JVMヒープ、GC、スレッド等のJMXメトリクスを自動計装。", "JBoss EAP 8.1ではJBoss Modulesとの競合を避けるためsystem.pkgs設定が必須。"],
        ["アプリ側 (Java)", "エクスポート先指定", "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317", "OTLP / gRPC (Port 4317)", "同一ECSタスク内のADOTサイドカーへループバック送信。外部ネットワークを経由しないため超高速・高セキュリティ。", "awsvpcネットワークモードのためlocalhostでサイドカーに到達可能。"],
        ["アプリ側 (Java)", "プロトコル設定", "OTEL_EXPORTER_OTLP_PROTOCOL", "grpc", "HTTP/2 (gRPC)", "低オーバーヘッドでシリアライズされたバイナリメトリクスパケットをストリーミング送信。", "ポート4318を使用する場合はhttp/protobufを指定。"],
        ["アプリ側 (Java)", "メトリクス収集間隔", "OTEL_METRIC_EXPORT_INTERVAL", "5000 (ミリ秒 = 5秒)", "-", "5秒間隔でヒープ使用量やGCカウンタをバッチ送信。JMeter実行中の細かな変動を捕捉可能。", "本番稼働時は60000(60秒)に緩和可能だが、負荷テスト時は5000〜10000が最適。"],
        ["サイドカー側", "ADOT Collector", "receivers::otlp", "grpc: 0.0.0.0:4317", "Port 4317 (タスク内公開)", "JavaコンテナからのOTLPメトリクスおよびトレースを受信。", "既存のawsxrayレシーバー(Port 2000/UDP)と共存可能。"],
        ["サイドカー側", "ADOT Collector", "processors::resourcedetection", "detectors: [ecs, env]", "-", "ECSメタデータ(ClusterName, TaskDefinitionFamily, ContainerName)をメトリクス属性に自動付加。", "CloudWatch上でタスクやコンテナごとの絞り込みが可能になる。"],
        ["サイドカー側", "ADOT Collector", "exporters::awsemf", "namespace: ECS/JVM/JBossEAP", "HTTPS / AWS API (Port 443)", "受信したJVMメトリクスをCloudWatch Embedded Metric Format(EMF)として非同期送信。CloudWatch Metricsに即座にグラフ化。", "PutMetricData APIを直接叩くより格段に低コストかつ高スループット。"],
        ["AWSサービス側", "CloudWatch Metrics", "カスタムメトリクス名前空間", "ECS/JVM/JBossEAP", "-", "JMeter実行中のヒープメモリ推移、GC停止時間、スレッド数をダッシュボードで統合表示。", "JMeterのEC2側から取得したスループットやレスポンスタイムと同一画面で時間軸を重ねて分析可能。"],
        ["AWSサービス側", "AWS X-Ray", "トレース (Traces)", "awsxray exporter", "HTTPS / AWS API (Port 443)", "（既存機能）分散トレーシング。遅延の発生したHTTPリクエストやDB SQLクエリを可視化。", "GC STW発生時間帯にX-Rayトレースで全体的なレスポンス遅延が記録されているか照合可能。"],
        ["AWSサービス側", "CloudWatch Logs", "ロググループ", "/aws/ecs/application/jvm-metrics", "HTTPS / AWS API (Port 443)", "EMFログデータの実体。生データのJSONが蓄積されており、CloudWatch Logs Insightsでクエリ可能。", "メトリクス集計前の秒単位の生データを後から再調査・集計可能。"]
    ]
    
    current_row = 3
    for r_idx, row_data in enumerate(data_s3):
        for c_idx, val in enumerate(row_data):
            cell = ws3.cell(row=current_row, column=c_idx+1, value=val)
            cell.font = regular_font
            cell.border = border_cell
            
            if c_idx in [0, 4]:
                cell.alignment = align_center
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            elif c_idx in [1, 2, 3]:
                cell.font = code_font if c_idx in [2, 3] else bold_font
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            else:
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
                
        ws3.row_dimensions[current_row].height = 42
        current_row += 1
        
    col_widths_s3 = [16, 20, 36, 26, 22, 38, 38]
    for i, w in enumerate(col_widths_s3, start=1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # Sheet 4: スクリプト＆JVM引数仕様 (Scripts & JVM Options)
    # =========================================================================
    ws4 = wb.create_sheet(title="スクリプト＆JVM引数仕様")
    ws4.views.sheetView[0].showGridLines = True
    
    ws4.merge_cells("A1:G1")
    ws4["A1"] = "コンテナ実装スクリプト一覧 & JBoss EAP 8.1 (Java 17/21) 推奨JVM引数仕様"
    ws4["A1"].font = title_font
    ws4["A1"].fill = title_fill
    ws4["A1"].alignment = align_title
    ws4.row_dimensions[1].height = 36
    
    headers_s4 = ["分類", "対象ファイル / スクリプト名", "パラメータ / 設定コード", "実行契機 / タイミング", "出力先 / 転送先", "機能説明", "設定の要点"]
    for col_idx, h in enumerate(headers_s4, start=1):
        cell = ws4.cell(row=2, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border_header
    ws4.row_dimensions[2].height = 28
    
    data_s4 = [
        ["スクリプト", "jvm_metrics_collector.sh", "INTERVAL=5 / pgrep jboss-modules / jstat -gcutil", "コンテナ起動時に常駐", "stdout (CloudWatch Logs)", "5秒周期でjstatおよび/procからヒープ・GC・スレッド・RSSをJSON形式で標準出力。", "ポート9990閉塞でもローカルで完結。ログドライバーが自動でCW Logsへ転送。"],
        ["スクリプト", "entrypoint_wrapper.sh", "trap 'term_handler' SIGTERM / & wait", "コンテナのENTRYPOINT", "コンテナプロセス制御", "メトリクス収集スクリプトを安全にバックグラウンド起動し、JBossをフォアグラウンド実行。SIGTERMを正常捕捉。", "コンテナ停止時のゾンビプロセス防止とグレースフルシャットダウンを保証。"],
        ["スクリプト", "export_jfr_to_s3.sh", "jcmd <PID> JFR.start / dump / stop", "JMeterテスト開始時 / 終了時", "S3バケット / /tmp/jfr", "JFR(Java Flight Recorder)を低負荷(1%未満)でオンデマンド記録し、テスト完了時にS3へバイナリ退避。", "ECS ExecまたはCI/CDパイプラインからキック。JMCで詳細プロファイリング可能。"],
        ["JVMオプション", "standalone.conf", "-Xms2048m -Xmx2048m", "JBoss起動時", "JVMヒープ", "ヒープの初期サイズと最大サイズを同一に固定。", "負荷テスト中の動的ヒープ拡張による停止・遅延を防ぎ、メモリフットプリントを安定化。"],
        ["JVMオプション", "standalone.conf", "-Xlog:gc*,gc+phases=debug:file=/var/log/jboss/gc-%t.log...", "JBoss起動時", "ファイル / stdout", "JDK 17/21の統一ガベージコレクションログ出力。", "G1GCの全フェーズとSTW停止時間をミリ秒・タイムスタンプ付きでローテーション記録。"],
        ["JVMオプション", "standalone.conf", "-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=...", "OOM発生時", "/var/log/jboss/oom.hprof", "万が一JMeter負荷でメモリ枯渇(OOM)が発生した際にヒープダンプを自動出力。", "Eclipse MAT等でメモリリークを引き起こしたオブジェクトインスタンスを完全特定可能。"],
        ["JVMオプション", "standalone.conf", "-Djboss.modules.system.pkgs=io.opentelemetry,...", "JBoss起動時", "JBoss Modules", "JBossのクラスローダー分離機構に対して、OpenTelemetryエージェントのパッケージアクセスを許可。", "これを設定しないとJBoss起動時にClassNotFoundException等のモジュールエラーが発生。"],
        ["JVMオプション", "standalone.conf", "-XX:+ExitOnOutOfMemoryError", "OOM発生時", "OSプロセス", "OOM発生時にゾンビ化を防ぎ、プロセスを直ちに異常終了させてECSに再起動させる。", "ハングアップしたコンテナにリクエストが振り分けられ続ける障害の連鎖を防止。"]
    ]
    
    current_row = 3
    for r_idx, row_data in enumerate(data_s4):
        for c_idx, val in enumerate(row_data):
            cell = ws4.cell(row=current_row, column=c_idx+1, value=val)
            cell.font = regular_font
            cell.border = border_cell
            
            if c_idx in [0, 3]:
                cell.alignment = align_center
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            elif c_idx in [1, 2]:
                cell.font = code_font if c_idx == 2 else bold_font
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            else:
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
                
        ws4.row_dimensions[current_row].height = 40
        current_row += 1
        
    col_widths_s4 = [16, 24, 38, 20, 24, 38, 38]
    for i, w in enumerate(col_widths_s4, start=1):
        ws4.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # Sheet 5: UBI9・EAP8.1・cgroupv2留意点 (OS & Container Deep Dive)
    # =========================================================================
    ws5 = wb.create_sheet(title="UBI9・EAP8.1・cgroupv2留意点")
    ws5.views.sheetView[0].showGridLines = True
    
    ws5.merge_cells("A1:G1")
    ws5["A1"] = "Red Hat UBI 9.8 / JBoss EAP 8.1 / cgroup v2 / ECS 環境特有の設計考慮事項"
    ws5["A1"].font = title_font
    ws5["A1"].fill = title_fill
    ws5["A1"].alignment = align_title
    ws5.row_dimensions[1].height = 36
    
    headers_s5 = ["カテゴリ / 観点", "項目 / 技術要素", "発生しうる事象・課題", "技術的背景・根本原因", "推奨対策・実装方針", "動作検証方法", "重要度"]
    for col_idx, h in enumerate(headers_s5, start=1):
        cell = ws5.cell(row=2, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border_header
    ws5.row_dimensions[2].height = 28
    
    data_s5 = [
        ["OS / cgroup", "cgroup v2 メモリ制限認識", "JVMがコンテナ制限ではなくホストOS全体のメモリを参照してしまう危険", "UBI 9.8(RHEL 9)はデフォルトでcgroup v2を採用。古いJDKではcgroup v2のメモリパス(/sys/fs/cgroup/memory.max)を誤認識する。", "Java 17/21(OpenJDK)はcgroup v2にネイティブ対応済み。明示的に-XX:+UseContainerSupportを付与。", "コンテナ内で java -XshowSettings:system -version を実行し、Container Metricsが正しく制限値を認識しているか確認。", "最重要 (OOM Killer防止)"],
        ["コンテナ設計", "タスクメモリとヒープの比率", "ヒープをタスク上限ギリギリに設定してコンテナが前触れなくSIGKILLされる", "コンテナ全体のメモリ(RSS)には、JVMヒープ以外にMetaspace、スレッドスタック、ダイレクトバッファ、JITコード、OSライブラリが含まれる。", "ECSタスクメモリの60〜70%をヒープ(-Xmx)とし、残りの30〜40%をOff-Heap・OS領域として確保。", "ps -o rss,vsz や CloudWatchのMemoryUtilizationとJVM Used Heapの差分をモニタリング。", "最重要 (安定性)"],
        ["ミドルウェア", "JBoss Modules クラス分離", "Java Agentを導入した際にJBoss起動時にClassNotFoundやNoClassDefFoundError", "JBoss EAP 8.1はモジュール型クラスローダーを採用しており、ブートストラップクラスパス以外のパッケージを分離する。", "-Djboss.modules.system.pkgs=io.opentelemetry,org.jboss.byteman を起動引数に設定してシステムクラスとして解放。", "JBoss起動ログ(server.log)にAgent初期化成功ログ([otel.javaagent])が出ていることを確認。", "重要 (Agent起動必須)"],
        ["セキュリティ", "非rootユーザー実行 (UID 185)", "スクリプトやJFRファイル、GCログの書き込み権限エラー (Permission Denied)", "UBIおよびRed Hat JBoss標準ではセキュリティのためUID 185(jboss)でコンテナを実行する。/var/log等の権限に注意。", "Dockerfile内で事前に対象ディレクトリ(/var/log/jboss, /opt/jboss/scripts)の所有者をchown -R jboss:jbossに設定。", "ビルド後のコンテナで su -s /bin/bash jboss 相当でスクリプトが問題なく書き込めるかテスト。", "重要 (権限エラー防止)"],
        ["JDK選定", "JRE vs JDK (develパッケージ)", "jstatやjcmdが見つからず、スクリプト実行時に'command not found'エラー", "コンテナ軽量化のためHeadless JRE(java-17-openjdk-headless)のみを入れると、JDK診断コマンドが含まれない。", "Dockerfileでjava-17-openjdk-develをインストールするか、JDKツールバイナリを含める。", "コンテナ内で which jstat && which jcmd を実行し存在を確認。", "重要 (スクリプト動作)"],
        ["ネットワーク", "ECS awsvpc と localhost", "ADOTサイドカーへのOTLPメトリクス送信がタイムアウトする", "同一タスク内のコンテナ間通信はawsvpcモードによりlocalhostで通信するが、バインドアドレスが127.0.0.1以外だと不達。", "ADOT CollectorのOTLPレシーバーendpointを 0.0.0.0:4317 に設定し、アプリからは localhost:4317 を指定。", "アプリコンテナから curl -v http://localhost:4318/v1/metrics やncで接続確認。", "重要 (通信確立)"]
    ]
    
    current_row = 3
    for r_idx, row_data in enumerate(data_s5):
        for c_idx, val in enumerate(row_data):
            cell = ws5.cell(row=current_row, column=c_idx+1, value=val)
            cell.font = regular_font
            cell.border = border_cell
            
            if c_idx in [0, 6]:
                cell.alignment = align_center
                if "最重要" in val:
                    cell.fill = badge_best_fill
                    cell.font = badge_best_font
                else:
                    cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            elif c_idx == 1:
                cell.font = bold_font
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
            else:
                cell.alignment = align_left
                cell.fill = zebra_fill if r_idx % 2 == 1 else white_fill
                
        ws5.row_dimensions[current_row].height = 48
        current_row += 1
        
    col_widths_s5 = [16, 24, 32, 36, 38, 34, 18]
    for i, w in enumerate(col_widths_s5, start=1):
        ws5.column_dimensions[get_column_letter(i)].width = w

    # 保存
    output_filename = "JMeter_JVM_Metrics_Specification.xlsx"
    wb.save(output_filename)
    print(f"Excel file successfully generated: {output_filename}")

if __name__ == "__main__":
    build_specification_excel()
