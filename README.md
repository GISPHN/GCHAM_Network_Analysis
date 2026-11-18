# G-CHAM Network Analysis

QGIS 3系・4系に対応した、道路ネットワークを使う経路・到達圏解析と保健師チーム巡回計画のプラグインです。

## 主な機能

- 道路網に沿った最短距離ルートと参考所要時間の算出
- 距離または所要時間による到達圏解析（起点ごと、全起点の統合）
- 複数チームによる訪問先巡回計画
- 未訪問先がある場合の、チーム数・行動可能時間・共通対応時間の自動調整
- 歩行、自転車、自動車統計、任意速度の選択
- CSV、Excelサマリー、GeoPackageへの出力
- 日本語・英語の画面表示と出力

到達圏の区間明細はCSVとGeoPackageに保存し、QGISには集約した表示用レイヤを追加します。大規模な統合ラインは初回描画の負荷を抑えるため、非表示で追加されます。

## インストール

QGISの「プラグイン」→「プラグインの管理とインストール」→「ZIPからインストール」から、配布ZIPを指定してください。

## 入力データと注意点

道路ネットワークは、交差点で分割・接続されたメートル単位の投影座標系のラインレイヤを使用してください。起点・目的地にはポイントレイヤを使用します。

このプラグインは入力された道路形状と選択速度を用いた参考解析です。一方通行、車両や歩行者の通行規制、交差点待ち、時間帯による速度変化などを完全には再現しません。巡回計画は試作ヒューリスティックによる計画であり、全体最適を保証しません。結果を実務に使う場合は、入力データ、設定、未訪問先、経路を確認してください。

詳しい操作手順、速度の出典、結果の解釈、制約事項は[日本語ガイド](README_ja.txt)をご覧ください。

## 引用

研究等で本プラグインを使用した場合は、実際に使用したバージョンを明記して引用してください。以下はバージョン0.4.13の例です。ほかのバージョンを使用した場合は、バージョン番号と公開年を実際のリリースに合わせてください。引用文は各コード欄のコピー機能でコピーできます。

APA第7版：

```text
GISPHN (Ryo Horiike). (2026). G-CHAM Network Analysis (Version 0.4.13) [Computer software]. GitHub. https://github.com/GISPHN/GCHAM_Network_Analysis
```

Vancouver形式：

```text
GISPHN (Ryo Horiike). G-CHAM Network Analysis [computer software]. Version 0.4.13. GitHub; 2026 [cited 2026 Nov 18]. Available from: https://github.com/GISPHN/GCHAM_Network_Analysis
```

BibTeX：

```bibtex
@software{Horiike2026GCHAMNetworkAnalysis,
  author = {{GISPHN (Ryo Horiike)}},
  title = {{G-CHAM Network Analysis}},
  version = {0.4.13},
  year = {2026},
  url = {https://github.com/GISPHN/GCHAM_Network_Analysis},
  note = {QGIS plugin}
}
```

GitHubの引用機能向けメタデータは[CITATION.cff](CITATION.cff)に掲載しています。引用形式と利用上の注意は[CITATION.md](CITATION.md)もご覧ください。

## 対応環境

- QGIS 3.28以降およびQGIS 4系
- MITライセンス

## 作者・問い合わせ

GISPHN (Ryo Horiike)  
[課題・不具合の報告](https://github.com/GISPHN/GCHAM_Network_Analysis/issues)
