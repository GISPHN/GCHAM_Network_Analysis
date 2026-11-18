# -*- coding: utf-8 -*-
"""Small offline Japanese/English interface and output dictionary."""

UI_EN = {
    "G-CHAM Network Analysis": "G-CHAM Network Analysis",
    "解析の種類": "Analysis type", "最短距離ルート": "Shortest-distance route",
    "複数起点からの到達圏": "Multi-origin catchment", "複数チームで全訪問先を巡回": "Visit all destinations with multiple teams",
    "時間内で対応人数・優先度を最大化": "Maximize people served or priority within available time",
    "道路ネットワーク（ライン）": "Road network (line)", "起点レイヤ": "Origin layer",
    "起点リストに表示する名称カラム": "Name field shown for origins", "起点の指定": "Origin selection",
    "選択した地物のみを使用する": "Use selected features only", "選択状況": "Selection status",
    "選択中の地物：0件": "Selected features: 0", "選択中の地物：{}件": "Selected features: {}",
    "起点となる地点": "Starting point", "目的地レイヤ": "Destination layer",
    "目的地リストに表示する名称カラム": "Name field shown for destinations", "目的地となる地点": "Destination",
    "配送・巡回先の選択": "Visit destination selection", "選択した地物のみを訪問先にする": "Use selected features as destinations only",
    "対応対象人数のカラム": "People to serve field", "優先度の数値カラム": "Priority field (numeric)",
    "対応時間の設定方法": "Service time setting", "最適化する対応価値": "Objective to maximize",
    "対応人数を最大化": "Maximize people served", "優先度を加味した対応人数を最大化": "Maximize priority-weighted people served",
    "チーム数": "Number of teams", "1チームの人数（人）": "People per team",
    "チームごとの行動可能時間（時間）": "Available time per team (hours)", "チームごとの休憩時間（分）": "Break time per team (minutes)",
    "全訪問先共通の対応時間（分）": "Common service time for all destinations (minutes)",
    "対象者1人あたりの追加対応時間（分）": "Additional service time per person (minutes)", "帰着条件": "Return condition",
    "行動終了後に拠点へ戻る": "Return to base after the route", "到達圏の基準": "Catchment limit type",
    "距離": "Distance", "所要時間": "Travel time", "上限": "Limit", "複数起点の集計方法": "Multiple-origin aggregation",
    "起点ごとに個別": "Separate by origin", "全起点で統合（軽量）": "Combine all origins (lighter)",
    "ルート計算": "Routing method", "最短距離ルート（試作版）": "Shortest-distance route (prototype)",
    "複数チームの巡回計画（試作ヒューリスティック）": "Multi-team patrol plan (prototype heuristic)", "到達可能な道路区間を抽出": "Extract reachable road segments",
    "移動速度（速度と出典を選択）": "Travel speed (select speed and source)", "任意速度": "Custom speed",
    "自動車統計の地域": "Vehicle speed statistics: region", "自動車統計の道路種別": "Vehicle speed statistics: road type",
    "道路種別の選び方": "How to choose a road type", "自動車統計の時間帯": "Vehicle speed statistics: time period",
    "自動車統計の地域区分": "Vehicle speed statistics: area type", "自動車速度の適用について": "Applying vehicle speeds",
    "任意速度の根拠・メモ": "Custom speed rationale or note", "任意速度の出典URL": "Custom speed source URL",
    "速度の出典": "Speed source", "地点から道路までのずれを許す距離": "Maximum distance from point to road",
    "この設定について": "About this setting", "共通の出力先（.gpkg）": "Output GeoPackage",
    "出力ファイルについて": "Output files", "QGISに追加するレイヤ名": "Layer name in QGIS",
    "保存先を選択…": "Choose output…", "解析して結果を保存": "Run analysis and save results",
    "到達圏を解析して保存": "Analyze catchment and save", "巡回計画を作成して保存": "Create patrol plan and save",
    "閉じる": "Close", "実行ログ": "Run log", "根拠や設定理由（任意）": "Rationale or notes (optional)",
    "出典URL（任意）": "Source URL (optional)", "（統計地域を選択）": "(Select statistical region)",
    "（道路種別を選択）": "(Select road type)", "（レコード番号で表示）": "(Show record ID)",
    "（人数カラムを使わない）": "(Do not use a people field)", "（優先度を使わない）": "(Do not use a priority field)",
    "（訪問先共通の時間を使う）": "(Use common service time)", "（この条件に公表値なし）": "(No published value for this combination)",
    "対象者1人あたりの追加対応時間を設定したときだけ、対応時間の計算に使います。追加時間が0分の場合、チーム人数は所要時間に影響しません。": "Used only when additional service time per person is set. If the additional time is 0, team size does not affect service duration.",
    "初期設定では、すべての訪問先に同じ対応時間を適用します。対応時間カラムを選択した場合は、値が空欄の訪問先に使う代替時間です。": "By default, the same service time is used at every destination. If a service-time field is selected, this value is used when the field is blank.",
    "訪問先の人数 × この時間 ÷ 1チームの人数を、訪問先対応時間に加算します。チーム内で同時に対応できるという簡略化した仮定です。": "Adds people at a destination × this time ÷ team size to its service time. This assumes team members can serve people simultaneously.",
    "初期値は100 mです。解析前に起点・目的地すべてについて、道路ラインの頂点（交差点・端点）までの距離を確認します。超える地点があれば、全地点が接続できる最小距離を提示します。": "The default is 100 m. Before analysis, the distance from each origin and destination to the nearest road vertex is checked. If any point exceeds the limit, the minimum distance needed to connect all points is shown.",
    "ここで選ぶ地域は速度統計の集計地域です。解析範囲を切り抜く設定ではありません。選択した平均速度をネットワーク全体に一律適用し、道路区間ごとの速度差は扱いません。": "This region is the aggregation area of the speed statistics; it does not clip the analysis area. The selected mean speed is applied uniformly to the network, without road-segment-specific speeds.",
    "地域は選択中の時間帯・地域区分に公表値がある地域だけを表示します。道路種別は区分名の先頭に分類を表示し、公表値がない区分（表の「－」）は候補から除きます。": "Only regions with published values for the selected period and area type are shown. Road type labels include their category; types without published values are omitted.",
    "朝夕の混雑時（7–9時または17–19時）": "Peak periods (7–9 a.m. or 5–7 p.m.)",
    "昼間の非混雑時（9–17時）": "Off-peak daytime (9 a.m.–5 p.m.)", "昼間12時間平均（交通量加重）": "12-hour daytime mean (traffic-weighted)",
    "DID（商業地域）": "DID (commercial area)", "DID（商業地域を除く）": "DID (excluding commercial areas)",
    "その他の市街部": "Other urban area", "平地部": "Flatland", "山地部": "Mountainous area", "合計": "Total",
    "統合：全起点から届く道路区間を重複なく1つにまとめます。\n個別：起点ごとの到達道路を出力します。同じ道路が重複して記録されることがあります。":
        "Combined: merges reachable road segments from all origins without duplicates.\nSeparate: outputs reachable roads for each origin; the same road may appear more than once.",
    "例：C:/成果/route_results.gpkg": "Example: C:/results/route_results.gpkg",
    "解析を開始します。": "Analysis started.", "入力条件を確認しました。": "Input conditions validated.",
    "CSVを書き出しています。": "Writing CSV.", "GeoPackageレイヤを書き出しています。": "Writing GeoPackage layer.",
    "日本語サマリーExcelを書き出しました：{}": "Wrote summary workbook: {}",
    "キャンセル": "Cancel", "この条件で調整": "Adjust using these limits", "調整する": "Adjust",
    "自動調整する条件": "Automatic adjustment settings", "調整項目がありません": "No adjustment options selected",
    "少なくとも1つの項目を選んでください。": "Select at least one parameter to adjust.",
    "優先順位を確認してください": "Check adjustment priority", "調整する項目の優先順位は重複できません。": "Adjustment priority values must be unique.",
    "未訪問先があります": "Unvisited destinations remain", "現在の設定で出力": "Export with current settings",
    "設定を自動調整して全訪問先を回る": "Automatically adjust settings to visit all destinations",
    "訪問先が{}件": "{} destinations", "道路レイヤが{}地物": "{} road features",
    "全訪問先巡回の計算で、未訪問先が{}件残りました（全{}件）。\nこのまま結果を出力するか、設定を自動調整しますか？":
        "{} of {} destinations remain unvisited.\nExport with the current settings or automatically adjust the parameters?",
    "自動車／全国道路調査から地域・道路種別・時間帯を選択": "Vehicle / select region, road type, and time period from national road survey",
    "任意の速度を入力": "Enter a custom speed",
    "自動車／過去の概算設定値：30.0 km/h（8.33 m/s、官公庁の平均値ではありません）": "Vehicle / previous estimate: 30.0 km/h (8.33 m/s; not an official mean)",
    "国土交通省資料の徒歩平均速度4.7 km/h（1.3 m/s）。成人一般の基準値として設定。": "MLIT reference materials report an average walking speed of 4.7 km/h (1.3 m/s). Used here as a general adult reference.",
    "国土交通省掲載資料では75歳以上女性の歩行速度低下が著しく1.0 m/s以下と記載。1.0 m/sは集団平均ではなく、比較用の参考設定。": "An MLIT-hosted reference notes that walking speed declines substantially among women aged 75 and older, to 1.0 m/s or less. The 1.0 m/s value here is a comparison setting, not a group mean.",
    "津波避難計画の目安。老人自由歩行、群集歩行、地理不案内者等を想定した計画値。地域の訓練で検証が必要。": "A planning reference for tsunami evacuation, based on assumptions including older adults walking freely, crowd movement, and people unfamiliar with the area. Validate locally through drills.",
    "歩行困難者、身体障害者、乳幼児、重病人等を想定した計画上の参考値。個人差・介助方法・路面状況を反映した個別測定値ではない。": "A planning reference for people with walking difficulties, disabilities, infants, or serious illness. It is not an individual measurement and does not account for personal differences, assistance, or surface conditions.",
    "東日本大震災の津波避難実態調査で得られた徒歩避難全体の平均。地域・状況が異なる災害へそのまま一般化できる速度ではない。": "Mean walking speed observed during tsunami evacuation after the Great East Japan Earthquake. Do not generalize directly to disasters with different locations or conditions.",
    "東日本大震災時の津波避難実態調査における徒歩単独避難者の平均。": "Mean speed among people evacuating on foot alone in the Great East Japan Earthquake tsunami evacuation survey.",
    "東日本大震災時の津波避難実態調査における、歩行困難な同行者がいる徒歩避難者の平均。": "Mean speed among evacuees accompanied by someone with walking difficulties in the Great East Japan Earthquake tsunami evacuation survey.",
    "東日本大震災時の津波避難実態調査で、健常者20～50歳代の平均として整理された値。": "Mean speed reported for adults aged 20–59 without reported mobility impairments in the Great East Japan Earthquake tsunami evacuation survey.",
    "東日本大震災時の津波避難実態調査で、乳幼児や高齢者など歩行速度が遅い同行者がいた場合の平均。子ども単独の速度ではない。": "Mean speed when evacuees were accompanied by infants, older adults, or others who walk more slowly in the Great East Japan Earthquake survey. This is not a speed for children traveling alone.",
    "足立区の学校配置ガイドラインが通学距離の目安に用いる分速40 m。小学生全般の実測平均や全国基準ではなく、自治体の計画値。": "Adachi City's school planning guideline uses 40 m per minute as a school travel distance assumption for primary school pupils. This is a local planning value, not a measured national mean.",
    "足立区の学校配置ガイドラインが通学距離の目安に用いる分速60 m。中学生全般の実測平均や全国基準ではなく、自治体の計画値。": "Adachi City's school planning guideline uses 60 m per minute as a school travel distance assumption for junior high students. This is a local planning value, not a measured national mean.",
    "信号・交通量の影響を受けない試験走路での軽快車の平均自由旅行速度。": "Mean free-flow speed for a standard bicycle on a test course without traffic signals or traffic effects.",
    "東京都江東区の約5 km公道コースで、信号待ちを含む旅行速度。": "Travel speed on an approximately 5 km public-road course in Koto City, Tokyo, including signal delays.",
    "過去の会話で市街地・生活道路を含む保守的な操作的仮定として用いた値。官公庁の実測平均値ではありません。官公庁の参考値を使う場合は、国土交通省調査の30.5 km/h等を選択してください。": "A conservative operational assumption previously used for urban and local roads. It is not an official measured mean. For an official reference, select values such as the MLIT survey's 30.5 km/h.",
    "距離上限による到達圏解析のため、移動速度は使用していません。": "Travel speed was not used because this catchment analysis uses a distance limit.",
    "国土交通省の令和3年度全国道路・街路交通情勢調査の集計値。選択条件：{}、{}、{}、{}。選択した集計平均をネットワーク全体に一律適用します。道路区間ごとの実速度ではありません。": "Aggregate value from MLIT's FY2021 Road Traffic Census. Selected conditions: {}, {}, {}, {}. The selected mean is applied uniformly to the network; it is not a measured speed for each road segment.",
    "歩行・平時／一般成人：1.30 m/s（4.68 km/h）": "Walking / general adult, normal conditions: 1.30 m/s (4.68 km/h)",
    "歩行・平時／高齢者の参考値：1.00 m/s（3.60 km/h）": "Walking / older adult reference: 1.00 m/s (3.60 km/h)",
    "歩行・災害／避難計画の標準目安：1.00 m/s（3.60 km/h）": "Walking / evacuation planning reference: 1.00 m/s (3.60 km/h)",
    "歩行・災害／歩行困難者等：0.50 m/s（1.80 km/h）": "Walking / people with walking difficulty: 0.50 m/s (1.80 km/h)",
    "歩行・災害／東日本大震災時の徒歩避難全体：0.62 m/s（2.24 km/h）": "Walking / observed evacuation during the Great East Japan Earthquake: 0.62 m/s (2.24 km/h)",
    "歩行・災害／徒歩で単独避難：0.69 m/s（2.49 km/h）": "Walking / evacuation on foot alone: 0.69 m/s (2.49 km/h)",
    "歩行・災害／歩行困難な同行者あり：0.52 m/s（1.88 km/h）": "Walking / accompanied by a person with walking difficulty: 0.52 m/s (1.88 km/h)",
    "歩行・災害／健常者20～50歳代の避難平均：0.75 m/s（2.69 km/h）": "Walking / observed speed for adults aged 20–59: 0.75 m/s (2.69 km/h)",
    "歩行・災害／乳幼児・高齢者等の同行者あり：0.46 m/s（1.66 km/h）": "Walking / accompanied by an infant, older adult, or similar: 0.46 m/s (1.66 km/h)",
    "歩行・学童／小学生の通学距離基準（足立区）：0.67 m/s（2.40 km/h）": "Walking / primary school planning speed (Adachi City): 0.67 m/s (2.40 km/h)",
    "歩行・学童／中学生の通学距離基準（足立区）：1.00 m/s（3.60 km/h）": "Walking / junior high planning speed (Adachi City): 1.00 m/s (3.60 km/h)",
    "自転車／自由旅行速度：16.8 km/h（4.67 m/s）": "Cycling / free-flow speed: 16.8 km/h (4.67 m/s)",
    "自転車／公道での旅行速度：9.6 km/h（2.67 m/s）": "Cycling / public-road travel speed: 9.6 km/h (2.67 m/s)",
    "自動車／一般道路・昼間12時間平均（交通量加重）：30.5 km/h（8.47 m/s）": "Vehicle / all general roads, 12-hour traffic-weighted mean: 30.5 km/h (8.47 m/s)",
    "自動車／一般道路・朝夕混雑時：30.8 km/h（8.56 m/s）": "Vehicle / general roads, peak periods: 30.8 km/h (8.56 m/s)",
    "自動車／一般道路・昼間非混雑時：33.8 km/h（9.39 m/s）": "Vehicle / general roads, off-peak daytime: 33.8 km/h (9.39 m/s)",
    "自動車／過去の概算設定値：30.0 km/h（8.33 m/s、官公庁の平均値ではありません）": "Vehicle / previous estimate: 30.0 km/h (8.33 m/s; not an official mean)",
    "解析完了": "Analysis complete", "解析できませんでした": "Analysis failed",
    "到達圏解析完了": "Catchment analysis complete", "巡回計画の作成完了": "Patrol plan complete",
    "訪問先数の確認": "Confirm destination count", "道路への接続距離を確認": "Confirm point-to-road distance",
    "結果ファイルの保存先を選択": "Choose output file location", "自動調整の設定をキャンセルしました。": "Automatic adjustment was canceled.",
    "優先順位": "Priority", "調整する": "Adjust", "チーム数の上限": "Maximum teams",
    "行動可能時間の上限（時間）": "Maximum available time (hours)", "共通対応時間の下限（分）": "Minimum common service time (minutes)",
    "行動可能時間": "Available time", "全訪問先共通の対応時間": "Common service time for all destinations",
    "対応時間カラムが選択されているため、この項目は調整できません。": "This parameter cannot be adjusted because a service-time field is selected.",
    "目的地レイヤと目的地となる地点を選択してください。": "Select the destination layer and destination point.",
    "起点レイヤを選択してください。": "Select an origin layer.", "道路ラインレイヤを選択してください。": "Select a road line layer.",
    "共通の出力先（.gpkg）を指定してください。": "Choose an output GeoPackage.",
    "QGISに追加するレイヤ名を入力してください。": "Enter a layer name for QGIS.",
    "訪問予定：{} / {}件\n未訪問：{}件\n対応量：{} / {}{}\nCSV：{}\nサマリーCSV：{}\nサマリーExcel：{}\nGeoPackage：{}\n\nこれは道路距離に基づく試作ヒューリスティックの結果です。全体最適は保証されません。":
        "Planned visits: {} / {}\nNot visited: {}\nPeople / units served: {} / {} {}\nCSV: {}\nSummary CSV: {}\nSummary Excel: {}\nGeoPackage: {}\n\nThis result uses a prototype heuristic based on road distance. Global optimality is not guaranteed.",
    "到達可能な道路区間明細：{}件\nQGIS表示用ライン：{}地物\n区間CSV：{}\nサマリーCSV：{}\nGeoPackage：{}\n追加レイヤ名：{}{}{}":
        "Reachable road segments: {}\nAggregated features added to QGIS: {}\nSegment CSV: {}\nSummary CSV: {}\nGeoPackage: {}\nLayer name: {}{}{}",
    "{}件のルートを保存しました。\nCSV：{}\nGeoPackage：{}\n追加レイヤ名：{}": "Saved {} routes.\nCSV: {}\nGeoPackage: {}\nLayer name: {}",
    "1チームあたりの人数は固定し、選んだ項目を優先順に調整します。上限・下限に達したら次の項目へ進みます。": "Team size is fixed. Parameters are adjusted in priority order; once a bound is reached, the next parameter is considered.",
    "優先順位": "Priority", "チーム数の上限": "Maximum teams", "行動可能時間の上限（時間）": "Maximum available time (hours)",
    "共通対応時間の下限（分）": "Minimum common service time (minutes)", "行動可能時間": "Available time",
    "全訪問先共通の対応時間": "Common service time for all destinations",
    "対応時間カラムが選択されているため、この項目は調整できません。": "This parameter cannot be adjusted because a service-time field is selected.",
    "到達可能な道路区間明細：{}件\nQGIS表示用ライン：{}地物\n区間CSV：{}\nサマリーCSV：{}\nGeoPackage：{}\n追加レイヤ名：{}{}{}":
        "Reachable road segments: {}\nAggregated features added to QGIS: {}\nSegment CSV: {}\nSummary CSV: {}\nGeoPackage: {}\nLayer name: {}{}{}",
    "{}件のルートを保存しました。\nCSV：{}\nGeoPackage：{}\n追加レイヤ名：{}": "Saved {} routes.\nCSV: {}\nGeoPackage: {}\nLayer name: {}",
    "訪問予定：{} / {}件\n未訪問：{}件\n対応量：{} / {}{}\nCSV：{}\nサマリーCSV：{}\nサマリーExcel：{}\nGeoPackage：{}\n\nこれは道路距離に基づく試作ヒューリスティックの結果です。全体最適は保証されません。":
        "Planned visits: {} / {}\nNot visited: {}\nPeople / units served: {} / {} {}\nCSV: {}\nSummary CSV: {}\nSummary Excel: {}\nGeoPackage: {}\n\nThis result uses a prototype heuristic based on road distance. Global optimality is not guaranteed.",
}

OUTPUT_EN = {
    "全チーム内": "Within all team time limits", "上限超過あり": "One or more teams exceed the limit",
    "合計": "Total", "日本語サマリーExcelを書き出しました：{}": "Wrote summary workbook: {}",
    "チーム別の移動距離と移動時間には、設定がオンの場合、最後の訪問先から拠点へ戻る分を含みます。訪問先一覧の移動時間は、直前の地点から各訪問先までです。":
        "Team travel distance and time include the return trip to base when that option is enabled. Travel time in the destination list is from the previous stop to each destination.",
    "移動時間＋訪問先での対応時間＋休憩時間です。移動時間は選択した速度をルート全体に一律適用した参考値です。":
        "Work time is travel time plus service time at destinations plus break time. Travel time is an estimate based on applying the selected speed uniformly across the route.",
    "初期設定と最終設定を全体サマリーに記録します。チーム人数は固定です。共通対応時間の調整は、訪問先ごとの対応時間カラムを選択していない場合に限ります。":
        "The overview records the initial and final settings. Team size is fixed. Common service time can be adjusted only when no destination-specific service-time field is selected.",
    "各訪問先は訪問するか訪問しないかの二択で扱い、訪問先内での部分的な対応人数配分は行いません。":
        "Each destination is either visited or not visited; partial allocation of service capacity within a destination is not modeled.",
    "巡回順は挿入法と2-optによる試作ヒューリスティックです。全体最適を保証しません。":
        "Visit order uses a prototype heuristic with insertion and 2-opt. Global optimality is not guaranteed.",
    "一方通行、車両通行規制、時間帯別の道路速度変化、交差点遅延は再現しません。":
        "One-way streets, vehicle access restrictions, time-dependent road speeds, and intersection delays are not modeled.",
    "チーム経路レイヤは、少なくとも1件を担当したチームのみ地物を作成します。未使用チームはチーム別集計に0件として表示します。":
        "The team route layer contains features only for teams assigned at least one destination. Unused teams appear with zero visits in the team summary.",
    "対応単位": "service units", "人": "people", "人／件": "people / destinations",
    "巡回計画の全体サマリー": "Patrol Plan Overview", "チーム別の実績": "Team Performance",
    "訪問先ごとの結果": "Results by Destination", "未訪問先の確認": "Unvisited Destinations",
    "集計項目の見方と注意点": "Definitions and Limitations",
    "チーム別実績": "Team Performance", "訪問先一覧": "Destination List",
    "未訪問先": "Unvisited Destinations", "見方・注意点": "Definitions and Limitations",
    "全体サマリー": "Overall Summary",
    "解析日時": "Run date and time", "分析種類": "Analysis type", "最短距離": "Shortest distance",
    "全訪問先を巡回": "Visit all destinations", "時間内で対応人数・優先度を最大化": "Maximize service within time limit",
    "訪問予定": "Planned", "未訪問": "Not visited", "全起点で統合": "Combined origins",
    "全起点を統合": "All origins combined", "起点ごとに個別": "Separate by origin",
    "起点別": "By origin", "帰属先別": "By assigned origin", "全体": "Overall",
    "距離": "Distance", "所要時間": "Travel time", "m": "m", "分": "min",
    "歩行（平時）": "Walking (normal conditions)", "歩行（災害）": "Walking (disaster conditions)",
    "歩行（災害・実態調査）": "Walking (observed disaster evacuation)", "歩行（学童・自治体基準）": "Walking (schoolchildren; local guideline)",
    "平成17年度大都市交通センサス関連資料": "FY2005 Metropolitan Transportation Census reference materials",
    "平成17年度大都市交通センサス関連資料 表II-8-1「交通手段別平均速度の設定」": "FY2005 Metropolitan Transportation Census, Table II-8-1, Mean speeds by travel mode",
    "歩行の科学・高齢者や身体障害者の歩行特性（国土交通省掲載資料）": "Walking science: walking characteristics of older adults and people with disabilities (MLIT-hosted reference)",
    "市町村における津波避難計画策定指針（令和8年改定）": "Municipal Tsunami Evacuation Plan Guideline (2026 revision)",
    "南海トラフ地震臨時情報 防災対応ガイドライン 参考資料「津波に対する避難検討」": "Nankai Trough Earthquake Advisory Disaster Response Guideline, reference: Tsunami Evacuation Planning",
    "足立区立小・中学校の適正規模・適正配置のガイドライン": "Adachi City Guideline for Appropriate Size and Placement of Municipal Elementary and Junior High Schools",
    "内閣府（資料内で国土交通省調査を引用）": "Cabinet Office (cites an MLIT survey)",
    "東京都足立区": "Adachi City, Tokyo",
    "内閣府・消防庁": "Cabinet Office and Fire and Disaster Management Agency",
    "国土交通省 国土技術政策総合研究所": "National Institute for Land and Infrastructure Management, MLIT",
    "自転車旅行速度に関する研究": "Study on bicycle travel speeds",
    "令和3年度全国道路・街路交通情勢調査 一般交通量調査 集計結果整理表 表5「旅行速度整理表」": "FY2021 Road Traffic Census, General Traffic Survey, Table 5: Travel Speeds",
    "令和3年度（2021）": "FY2021", "2008年資料": "2008 reference", "指針 p.24": "Guideline, p. 24",
    "表5「旅行速度整理表」": "Table 5: Travel Speeds", "表II-8-1「交通手段別平均速度の設定」": "Table II-8-1: Mean speeds by travel mode",
    "到達道路延長_m": "Reachable road length (m)", "到達道路延長_km": "Reachable road length (km)",
    "道路上距離_最小_m": "Network distance minimum (m)", "道路上距離_平均_m": "Network distance mean (m)",
    "道路上距離_最大_m": "Network distance maximum (m)",
    "施設別到達道路延長_最小_m": "By-origin road length minimum (m)", "施設別到達道路延長_平均_m": "By-origin road length mean (m)",
    "施設別到達道路延長_中央値_m": "By-origin road length median (m)", "施設別到達道路延長_最大_m": "By-origin road length maximum (m)",
    "施設別最大到達距離_最小_m": "By-origin maximum distance minimum (m)", "施設別最大到達距離_平均_m": "By-origin maximum distance mean (m)",
    "施設別最大到達距離_中央値_m": "By-origin maximum distance median (m)", "施設別最大到達距離_最大_m": "By-origin maximum distance maximum (m)",
    "施設別最大参考時間_最小_分": "By-origin maximum estimated time minimum (min)", "施設別最大参考時間_平均_分": "By-origin maximum estimated time mean (min)",
    "施設別最大参考時間_中央値_分": "By-origin maximum estimated time median (min)", "施設別最大参考時間_最大_分": "By-origin maximum estimated time maximum (min)",
    "自動車（全国道路・街路交通情勢調査）": "Vehicle (MLIT Road Traffic Census)", "自動車（操作的仮定）": "Vehicle (operational assumption)",
    "任意入力": "Custom input", "利用者入力": "User input", "国土交通省": "Ministry of Land, Infrastructure, Transport and Tourism (MLIT)",
    "国土交通省 道路局": "MLIT Road Bureau", "内閣府・消防庁": "Cabinet Office and Fire and Disaster Management Agency",
    "利用者設定速度": "User-defined speed", "設定理由の記載なし。": "No rationale provided.",
    "拠点に戻る": "Return to base", "拠点に戻らない": "Do not return to base",
    "人数カラム未指定：訪問先1件を1単位として集計": "No people field selected; each destination counted as one unit",
    "個別起点の値を合計。重複する道路区間は起点数分含まれる。": "Sum of individual-origin values; overlapping road segments are counted once per origin.",
    "到達可能道路の和集合。各起点行は、出力区間の帰属先別集計であり、施設単独の到達範囲ではない。": "Union of reachable roads. Each origin row reports segments assigned to that origin, not its individual catchment.",
    "施設単独の到達圏": "Individual-origin catchment", "統合出力の帰属先別内訳（施設単独の到達圏ではない）": "Combined output, by assigned origin (not an individual catchment)",
    "起点別到達圏（重複あり）": "Catchments by origin (overlaps included)", "到達可能道路の和集合（重複なし）": "Union of reachable roads (no duplicates)",
    "起点から道路区間上の位置までの最短距離（スナップ距離を含む）。": "Shortest network distance from origin to road segment (including snap distance).",
    "ライン頂点間を双方向接続。一方通行・通行規制・交差点遅延は未考慮。起終点スナップ線は直線距離。": "Road vertices are connected bidirectionally. One-way rules, access restrictions, and intersection delays are not modeled. Snap connectors are straight lines.",
    "試作ヒューリスティックのため、最適性や実行不可能性は証明しません。": "Prototype heuristic; it does not prove optimality or infeasibility.",
    "到達道路区間の凸包（内部がすべて到達可能とは限らない）": "Convex hull of reachable road segments (the interior is not necessarily reachable)",
    "起点別凸包と、各凸包の重なりを融合したレイヤを保存・追加する。": "Save and add origin-specific convex hulls and their union.",
    "全訪問先を割り当てました。": "All destinations were assigned.", "設定変更なし。": "No settings changed.",
    "対応人数": "People served", "対応単位": "service units", "上限内": "Within limit", "はい": "Yes", "いいえ": "No",
    "解析できませんでした": "Analysis failed", "解析完了": "Analysis complete", "到達圏解析完了": "Catchment analysis complete",
    "巡回計画の作成完了": "Patrol plan complete", "解析を開始します。": "Analysis started.",
    "入力条件を確認しました。": "Input conditions validated.", "実行ログ": "Run log", "速度の出典": "Speed source",
    "到達道路延長_m": "Reachable road length (m)", "到達道路延長_km": "Reachable road length (km)",
    "行の区分": "Row type", "集計対象": "Scope", "集計方法": "Aggregation method", "起点レイヤ": "Origin layer",
    "起点ID": "Origin ID", "起点名": "Origin name", "起点から道路までの距離_m": "Origin snap distance (m)",
    "起点数": "Number of origins", "出力区間数": "Output segment count", "上限基準": "Limit type", "上限値": "Limit value",
    "上限単位": "Limit unit", "速度_km_h": "Speed (km/h)", "速度出典機関": "Speed source organization",
    "速度出典資料": "Speed source title", "速度出典年": "Speed source year", "速度出典頁": "Speed source page",
    "速度出典URL": "Speed source URL", "参考時間_最小_分": "Estimated time minimum (min)",
    "参考時間_平均_分": "Estimated time mean (min)", "参考時間_最大_分": "Estimated time maximum (min)",
    "施設別時間統計の対象数": "Origins included in time statistics", "施設別距離統計の対象数": "Origins included in distance statistics",
    "解析の種類": "Analysis type", "解析日時": "Run date and time", "出発拠点": "Starting base", "道路ネットワーク": "Road network",
    "道路ネットワークの座標系": "Road network CRS", "移動速度": "Travel speed", "訪問先候補数": "Candidate destinations",
    "訪問予定数": "Planned visits", "未訪問数": "Not visited", "訪問率": "Visit rate", "設定チーム数（調整前→後）": "Teams (before → after adjustment)",
    "訪問を担当したチーム数": "Teams with assigned visits", "1チームあたりの人数": "People per team",
    "行動可能時間（調整前→後）": "Available time (before → after adjustment)", "チームごとの休憩時間": "Break per team",
    "共通対応時間（調整前→後）": "Common service time (before → after adjustment)", "訪問先の対応時間の集計方法": "Service time calculation",
    "移動距離の合計": "Total travel distance", "移動時間の合計": "Total travel time", "訪問対応時間の合計": "Total service time",
    "休憩時間の合計": "Total break time", "全チームの勤務時間合計": "Total team work time", "各チームの時間上限": "Team time limits",
    "自動調整の結果": "Automatic adjustment result", "出力レイヤ名": "Output layer name",
    "チーム別の実績": "Team performance", "チーム": "Team", "チーム人数": "Team size", "訪問先数": "Destinations visited",
    "訪問先構成比（%）": "Share of all visits (%)", "対応人数・単位": "People / units served", "優先度加重値": "Priority-weighted value",
    "移動距離（km・帰着含む）": "Travel distance (km, return included)", "移動時間（分・帰着含む）": "Travel time (min, return included)",
    "訪問対応時間（分）": "Service time (min)", "休憩時間（分）": "Break time (min)", "勤務時間（分）": "Work time (min)",
    "行動可能時間（分）": "Available time (min)", "残り時間（分）": "Remaining time (min)", "時間上限内": "Within time limit", "訪問順": "Visit order",
    "訪問先ごとの結果": "Results by destination", "状態": "Status", "訪問先名": "Destination name", "元レイヤの地物ID": "Source feature ID",
    "優先度": "Priority", "対応時間（分）": "Service time (min)", "直前地点からの移動時間（分）": "Travel time from previous stop (min)",
    "出発後の到着時刻（分）": "Arrival time after departure (min)", "対応終了時刻（分）": "Service completion after departure (min)",
    "未訪問の理由": "Reason not visited", "未訪問先の確認": "Unvisited destinations", "未訪問先はありません。": "There are no unvisited destinations.",
    "集計項目の見方と注意点": "Definitions and limitations", "項目": "Item", "説明": "Description",
    "移動距離・移動時間": "Travel distance and time", "勤務時間": "Work time", "対応人数・単位": "People / units served",
    "自動調整": "Automatic adjustment", "訪問先の割当": "Destination assignment", "最適性": "Optimality", "道路条件": "Road assumptions", "出力レイヤ": "Output layers",
    "訪問先の割り当て": "Destination assignment", "道路上の距離": "Road distance", "任意速度": "Custom speed",
    "巡回計画条件": "Patrol plan settings", "休憩": "break", "ルート": "route",
    "自動調整結果": "Automatic adjustment result", "調整": "Adjustment", "起点別の探索": "Exploring by origin",
    "_チーム経路": "_Team_Routes", "_訪問先": "_Destinations", "_区間明細": "_Segment_Details",
    "_到達道路別凸包": "_Reachable_Road_Hulls_By_Origin", "_起点別凸包": "_Origin_Hulls",
    "_全起点凸包融合": "_Union_Of_Origin_Hulls", "_到達可能道路": "_Reachable_Roads",
    "準備完了。出力先を1つ指定して解析を開始できます。": "Ready. Choose one output path to start the analysis.",
}

PREFECTURES = {
    "北海道":"Hokkaido", "青森県":"Aomori", "岩手県":"Iwate", "宮城県":"Miyagi", "秋田県":"Akita", "山形県":"Yamagata", "福島県":"Fukushima",
    "茨城県":"Ibaraki", "栃木県":"Tochigi", "群馬県":"Gunma", "埼玉県":"Saitama", "千葉県":"Chiba", "東京都":"Tokyo", "神奈川県":"Kanagawa",
    "新潟県":"Niigata", "富山県":"Toyama", "石川県":"Ishikawa", "福井県":"Fukui", "山梨県":"Yamanashi", "長野県":"Nagano", "岐阜県":"Gifu",
    "静岡県":"Shizuoka", "愛知県":"Aichi", "三重県":"Mie", "滋賀県":"Shiga", "京都府":"Kyoto", "大阪府":"Osaka", "兵庫県":"Hyogo",
    "奈良県":"Nara", "和歌山県":"Wakayama", "鳥取県":"Tottori", "島根県":"Shimane", "岡山県":"Okayama", "広島県":"Hiroshima", "山口県":"Yamaguchi",
    "徳島県":"Tokushima", "香川県":"Kagawa", "愛媛県":"Ehime", "高知県":"Kochi", "福岡県":"Fukuoka", "佐賀県":"Saga", "長崎県":"Nagasaki",
    "熊本県":"Kumamoto", "大分県":"Oita", "宮崎県":"Miyazaki", "鹿児島県":"Kagoshima", "沖縄県":"Okinawa",
}


def translate_region_label(text, language="ja"):
    if language != "en" or not isinstance(text, str):
        return text
    for jp, en in PREFECTURES.items():
        if text.startswith(jp):
            suffix = text[len(jp):]
            suffix = suffix.replace("全域", " (entire prefecture)").replace("（", " (").replace("）", ")")
            suffix = suffix.replace("合計", "Total").replace("地域", "area")
            suffix = suffix.replace("北部", " northern area").replace("南部", " southern area")
            suffix = suffix.replace("東部", " eastern area").replace("西部", " western area")
            return en + suffix
    return translate_text(text, language)


def translate_text(text, language="ja"):
    """Translate known UI/output phrases while preserving user layer/field names."""
    if not isinstance(text, str):
        return text
    import re
    if language != "en":
        reverse = {value: key for key, value in {**OUTPUT_EN, **UI_EN}.items()}
        if text in reverse:
            return reverse[text]
        if re.fullmatch(r"Team \d+", text):
            return "チーム" + text.split()[-1]
        return text
    translated = UI_EN.get(text, OUTPUT_EN.get(text, text))
    if translated != text:
        return translated
    for jp, en in PREFECTURES.items():
        if text.startswith(jp):
            suffix = text[len(jp):]
            suffix = suffix.replace("全域", " (entire prefecture)")
            suffix = suffix.replace("北部", " northern area").replace("南部", " southern area")
            suffix = suffix.replace("東部", " eastern area").replace("西部", " western area")
            return en + suffix
    if re.fullmatch(r"チーム\d+", text):
        return "Team " + text[3:]
    # Dynamic automatic-adjustment details have a fixed schema. Translate only
    # those known labels so that user-provided place and layer names are intact.
    if text.startswith("全訪問先を割り当てました。"):
        result = text.replace("全訪問先を割り当てました。", "All destinations were assigned.")
        for jp, en in (("調整：", " Adjustments: "), ("チーム数", "teams"),
                        ("行動可能時間", "available time"), ("共通対応時間を", "common service time set to "),
                        ("分、", " min, "), ("分に設定", " min"),
                        ("試作ヒューリスティックのため、最適性や実行不可能性は証明しません。",
                         "Prototype heuristic; optimality and infeasibility are not proven.")):
            result = result.replace(jp, en)
        result = re.sub(r"(\d+)→(\d+)", r"\1 to \2", result)
        result = re.sub(r"(\d+(?:\.\d+)?)→(\d+(?:\.\d+)?)", r"\1 to \2", result)
        return result
    return text


ROAD_LABELS_EN = {
    "高速道路｜高速自動車国道": "Expressway | National expressway",
    "高速道路｜一般国道の自動車専用道路": "Expressway | National highway motor road",
    "高速道路｜高規格幹線道路": "Expressway | High-standard arterial road",
    "高速道路｜都市高速道路": "Expressway | Urban expressway",
    "高速道路｜計": "Expressway | Total",
    "高速道路｜計（一般国道の自動車専用道路を除く）": "Expressway | Total (excluding national highway motor roads)",
    "一般国道｜直轄": "National highway | Directly managed",
    "一般国道｜その他": "National highway | Other",
    "一般国道｜計": "National highway | Total",
    "地方道｜主要地方道（都道府県道）": "Local road | Major prefectural road",
    "地方道｜主要地方道（指定市道）": "Local road | Major designated-city road",
    "地方道｜主要地方道計": "Local road | Major roads total",
    "地方道｜一般都道府県道": "Local road | General prefectural road",
    "地方道｜計": "Local road | Total",
    "一般道路｜計": "General roads | Total",
    "全道路種別｜合計": "All road types | Total",
    "市道｜指定市の一般市道": "Municipal road | General road in designated city",
}


def translate_road_label(text, language="en"):
    if language == "en":
        return ROAD_LABELS_EN.get(text, text)
    reverse = {value: key for key, value in ROAD_LABELS_EN.items()}
    return reverse.get(text, text)
