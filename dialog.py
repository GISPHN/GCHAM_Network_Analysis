# -*- coding: utf-8 -*-
import csv
import gc
import hashlib
import html
import heapq
import math
import statistics
from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtCore import QEventLoop, QMetaType, Qt
from qgis.PyQt.QtGui import QColor, QDoubleValidator
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QSpinBox, QDoubleSpinBox, QVBoxLayout, QWidget, QPlainTextEdit,
)
from qgis.core import (
    QgsCoordinateTransform, QgsFeature, QgsField, QgsGeometry,
    QgsFields, QgsPointXY, QgsProject, QgsRectangle, QgsUnitTypes, QgsVectorFileWriter, QgsVectorLayer,
    QgsWkbTypes, QgsSpatialIndex, QgsFeatureRequest, Qgis, QgsLineSymbol,
    QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer, QgsPalLayerSettings,
    QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsFillSymbol,
    QgsMultiLineString,
)
from .route_planning import plan_routes
from .excel_summary import write_patrol_summary
from .localization import translate_text, translate_region_label, translate_road_label


OUTPUT_LANGUAGE = "ja"


def _translate_road_label(text):
    return translate_road_label(text, "en")


def _localized_value(value):
    if not isinstance(value, str):
        return value
    if OUTPUT_LANGUAGE == "en":
        translated_region = translate_region_label(value, "en")
        if translated_region != value:
            return translated_region
        translated_road = _translate_road_label(ROAD_TYPE_DISPLAY.get(value, value))
        if translated_road != ROAD_TYPE_DISPLAY.get(value, value):
            return translated_road
    return translate_text(value, OUTPUT_LANGUAGE)


def _localized_row(row):
    if OUTPUT_LANGUAGE != "en":
        return row
    return {translate_text(key, "en"): _localized_value(value) for key, value in row.items()}

try:
    MESSAGE_YES = QMessageBox.StandardButton.Yes
    MESSAGE_NO = QMessageBox.StandardButton.No
except AttributeError:
    MESSAGE_YES = QMessageBox.Yes
    MESSAGE_NO = QMessageBox.No


# PyQt5 (QGIS 3) and PyQt6 (QGIS 4) expose Qt enum members differently.
try:
    RICH_TEXT_FORMAT = Qt.TextFormat.RichText
except AttributeError:
    RICH_TEXT_FORMAT = Qt.RichText

try:
    EXCLUDE_USER_INPUT_EVENTS = QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
except AttributeError:
    EXCLUDE_USER_INPUT_EVENTS = QEventLoop.ExcludeUserInputEvents

# QGIS 4 uses scoped QMetaType and Qgis enums. QGIS 3.28+ also exposes these
# enums, while the older names below keep the declared minimum version usable.
try:
    FIELD_STRING = QMetaType.Type.QString
    FIELD_DOUBLE = QMetaType.Type.Double
except AttributeError:
    try:
        FIELD_STRING = QMetaType.QString
        FIELD_DOUBLE = QMetaType.Double
    except AttributeError:
        from qgis.PyQt.QtCore import QVariant
        FIELD_STRING = QVariant.String
        FIELD_DOUBLE = QVariant.Double

try:
    LINE_WKB_TYPE = Qgis.WkbType.LineString
except AttributeError:
    LINE_WKB_TYPE = QgsWkbTypes.LineString

try:
    POINT_WKB_TYPE = Qgis.WkbType.Point
except AttributeError:
    POINT_WKB_TYPE = QgsWkbTypes.Point

try:
    MULTILINE_WKB_TYPE = Qgis.WkbType.MultiLineString
except AttributeError:
    MULTILINE_WKB_TYPE = QgsWkbTypes.MultiLineString

try:
    MULTIPOLYGON_WKB_TYPE = Qgis.WkbType.MultiPolygon
except AttributeError:
    MULTIPOLYGON_WKB_TYPE = QgsWkbTypes.MultiPolygon

PREFECTURE_ORDER = (
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
)

ROAD_TYPE_DISPLAY = {
    "高速自動車国道": "高速道路｜高速自動車国道",
    "一般国道の自動車専用道路": "高速道路｜一般国道の自動車専用道路",
    "高規格幹線道路": "高速道路｜高規格幹線道路",
    "都市高速道路": "高速道路｜都市高速道路",
    "高速道路計": "高速道路｜計",
    "高速道路計（一般国道の自動車専用道路を除く）":
        "高速道路｜計（一般国道の自動車専用道路を除く）",
    "一般国道（直轄）": "一般国道｜直轄",
    "一般国道（その他）": "一般国道｜その他",
    "一般国道計": "一般国道｜計",
    "主要地方道（都道府県道）": "地方道｜主要地方道（都道府県道）",
    "主要地方道（指定市道）": "地方道｜主要地方道（指定市道）",
    "主要地方道計": "地方道｜主要地方道計",
    "一般都道府県道": "地方道｜一般都道府県道",
    "地方道計": "地方道｜計",
    "一般道路計": "一般道路｜計",
    "合計": "全道路種別｜合計",
    "指定市の一般市道": "市道｜指定市の一般市道",
}

try:
    LINE_GEOMETRY_TYPE = Qgis.GeometryType.Line
    POINT_GEOMETRY_TYPE = Qgis.GeometryType.Point
    POLYGON_GEOMETRY_TYPE = Qgis.GeometryType.Polygon
except AttributeError:
    LINE_GEOMETRY_TYPE = QgsWkbTypes.LineGeometry
    POINT_GEOMETRY_TYPE = QgsWkbTypes.PointGeometry
    POLYGON_GEOMETRY_TYPE = QgsWkbTypes.PolygonGeometry

try:
    NO_GEOMETRY_FLAG = Qgis.FeatureRequestFlag.NoGeometry
except AttributeError:
    NO_GEOMETRY_FLAG = QgsFeatureRequest.NoGeometry

try:
    DISTANCE_METERS = Qgis.DistanceUnit.Meters
except AttributeError:
    DISTANCE_METERS = QgsUnitTypes.DistanceUnit.Meters


SPEED_PRESETS = {
    "walk_adult": {
        "label": "歩行・平時／一般成人：1.30 m/s（4.68 km/h）",
        "kmh": 4.68,
        "category": "歩行（平時）",
        "definition": "国土交通省資料の徒歩平均速度4.7 km/h（1.3 m/s）。成人一般の基準値として設定。",
        "issuer": "国土交通省",
        "title": "平成17年度大都市交通センサス関連資料 表II-8-1「交通手段別平均速度の設定」",
        "year": "平成17年度大都市交通センサス関連資料",
        "page": "236",
        "url": "https://www.mlit.go.jp/common/000020723.pdf",
    },
    "walk_elderly": {
        "label": "歩行・平時／高齢者の参考値：1.00 m/s（3.60 km/h）",
        "kmh": 3.6,
        "category": "歩行（平時）",
        "definition": "国土交通省掲載資料では75歳以上女性の歩行速度低下が著しく1.0 m/s以下と記載。1.0 m/sは集団平均ではなく、比較用の参考設定。",
        "issuer": "国土交通省",
        "title": "歩行の科学・高齢者や身体障害者の歩行特性（国土交通省掲載資料）",
        "year": "2008年資料",
        "page": "24–25",
        "url": "https://www.mlit.go.jp/common/000022956.pdf",
    },
    "walk_disaster_plan": {
        "label": "歩行・災害／避難計画の標準目安：1.00 m/s（3.60 km/h）",
        "kmh": 3.6,
        "category": "歩行（災害）",
        "definition": "津波避難計画の目安。老人自由歩行、群集歩行、地理不案内者等を想定した計画値。地域の訓練で検証が必要。",
        "issuer": "内閣府・消防庁",
        "title": "市町村における津波避難計画策定指針（令和8年改定）",
        "year": "2026",
        "page": "指針 p.24",
        "url": "https://www.fdma.go.jp/laws/tutatsu/items/20260116_bousai2.pdf",
    },
    "walk_disaster_support": {
        "label": "歩行・災害／歩行困難者等：0.50 m/s（1.80 km/h）",
        "kmh": 1.8,
        "category": "歩行（災害）",
        "definition": "歩行困難者、身体障害者、乳幼児、重病人等を想定した計画上の参考値。個人差・介助方法・路面状況を反映した個別測定値ではない。",
        "issuer": "内閣府・消防庁",
        "title": "市町村における津波避難計画策定指針（令和8年改定）",
        "year": "2026",
        "page": "指針 p.24",
        "url": "https://www.fdma.go.jp/laws/tutatsu/items/20260116_bousai2.pdf",
    },
    "walk_disaster_observed": {
        "label": "歩行・災害／東日本大震災時の徒歩避難全体：0.62 m/s（2.24 km/h）",
        "kmh": 2.24,
        "category": "歩行（災害・実態調査）",
        "definition": "東日本大震災の津波避難実態調査で得られた徒歩避難全体の平均。地域・状況が異なる災害へそのまま一般化できる速度ではない。",
        "issuer": "内閣府（資料内で国土交通省調査を引用）",
        "title": "南海トラフ地震臨時情報 防災対応ガイドライン 参考資料「津波に対する避難検討」",
        "year": "2025年改訂版",
        "page": "159",
        "url": "https://www.bousai.go.jp/jishin/nankai/pdf/honbun_guideline2.pdf",
    },
    "walk_disaster_single": {
        "label": "歩行・災害／徒歩で単独避難：0.69 m/s（2.49 km/h）",
        "kmh": 2.49,
        "category": "歩行（災害・実態調査）",
        "definition": "東日本大震災時の津波避難実態調査における徒歩単独避難者の平均。",
        "issuer": "内閣府（資料内で国土交通省調査を引用）",
        "title": "南海トラフ地震臨時情報 防災対応ガイドライン 参考資料「津波に対する避難検討」",
        "year": "2025年改訂版",
        "page": "159",
        "url": "https://www.bousai.go.jp/jishin/nankai/pdf/honbun_guideline2.pdf",
    },
    "walk_disaster_impaired_companion": {
        "label": "歩行・災害／歩行困難な同行者あり：0.52 m/s（1.88 km/h）",
        "kmh": 1.88,
        "category": "歩行（災害・実態調査）",
        "definition": "東日本大震災時の津波避難実態調査における、歩行困難な同行者がいる徒歩避難者の平均。",
        "issuer": "内閣府（資料内で国土交通省調査を引用）",
        "title": "南海トラフ地震臨時情報 防災対応ガイドライン 参考資料「津波に対する避難検討」",
        "year": "2025年改訂版",
        "page": "159",
        "url": "https://www.bousai.go.jp/jishin/nankai/pdf/honbun_guideline2.pdf",
    },
    "walk_disaster_adult": {
        "label": "歩行・災害／健常者20～50歳代の避難平均：0.75 m/s（2.69 km/h）",
        "kmh": 2.69,
        "category": "歩行（災害・実態調査）",
        "definition": "東日本大震災時の津波避難実態調査で、健常者20～50歳代の平均として整理された値。",
        "issuer": "内閣府（資料内で国土交通省調査を引用）",
        "title": "南海トラフ地震臨時情報 防災対応ガイドライン 参考資料「津波に対する避難検討」",
        "year": "2025年改訂版",
        "page": "159",
        "url": "https://www.bousai.go.jp/jishin/nankai/pdf/honbun_guideline2.pdf",
    },
    "walk_disaster_slow_companions": {
        "label": "歩行・災害／乳幼児・高齢者等の同行者あり：0.46 m/s（1.66 km/h）",
        "kmh": 1.66,
        "category": "歩行（災害・実態調査）",
        "definition": "東日本大震災時の津波避難実態調査で、乳幼児や高齢者など歩行速度が遅い同行者がいた場合の平均。子ども単独の速度ではない。",
        "issuer": "内閣府（資料内で国土交通省調査を引用）",
        "title": "南海トラフ地震臨時情報 防災対応ガイドライン 参考資料「津波に対する避難検討」",
        "year": "2025年改訂版",
        "page": "159",
        "url": "https://www.bousai.go.jp/jishin/nankai/pdf/honbun_guideline2.pdf",
    },
    "walk_school_primary": {
        "label": "歩行・学童／小学生の通学距離基準（足立区）：0.67 m/s（2.40 km/h）",
        "kmh": 2.4,
        "category": "歩行（学童・自治体基準）",
        "definition": "足立区の学校配置ガイドラインが通学距離の目安に用いる分速40 m。小学生全般の実測平均や全国基準ではなく、自治体の計画値。",
        "issuer": "東京都足立区",
        "title": "足立区立小・中学校の適正規模・適正配置のガイドライン",
        "year": "2025",
        "page": "第2章",
        "url": "https://www.city.adachi.tokyo.jp/documents/34902/gaido.pdf",
    },
    "walk_school_middle": {
        "label": "歩行・学童／中学生の通学距離基準（足立区）：1.00 m/s（3.60 km/h）",
        "kmh": 3.6,
        "category": "歩行（学童・自治体基準）",
        "definition": "足立区の学校配置ガイドラインが通学距離の目安に用いる分速60 m。中学生全般の実測平均や全国基準ではなく、自治体の計画値。",
        "issuer": "東京都足立区",
        "title": "足立区立小・中学校の適正規模・適正配置のガイドライン",
        "year": "2025",
        "page": "第2章",
        "url": "https://www.city.adachi.tokyo.jp/documents/34902/gaido.pdf",
    },
    "free": {
        "label": "自転車／自由旅行速度：16.8 km/h（4.67 m/s）",
        "kmh": 16.8,
        "category": "自転車",
        "definition": "信号・交通量の影響を受けない試験走路での軽快車の平均自由旅行速度。",
        "issuer": "国土交通省 国土技術政策総合研究所",
        "title": "自転車旅行速度に関する研究",
        "year": "2012",
        "page": "72",
        "url": "https://www.nilim.go.jp/lab/bcg/siryou/2012report/2012nilim39.pdf",
    },
    "road": {
        "label": "自転車／公道での旅行速度：9.6 km/h（2.67 m/s）",
        "kmh": 9.6,
        "category": "自転車",
        "definition": "東京都江東区の約5 km公道コースで、信号待ちを含む旅行速度。",
        "issuer": "国土交通省 国土技術政策総合研究所",
        "title": "自転車旅行速度に関する研究",
        "year": "2012",
        "page": "72",
        "url": "https://www.nilim.go.jp/lab/bcg/siryou/2012report/2012nilim39.pdf",
    },
    "car_general_weighted": {
        "label": "自動車／一般道路・昼間12時間平均（交通量加重）：30.5 km/h（8.47 m/s）",
        "kmh": 30.5,
        "category": "自動車",
        "definition": "全国道路・街路交通情勢調査の一般道路計における昼間12時間平均旅行速度（時間帯別交通量による加重平均）。特定地域・特定道路の速度ではなく、全国集計の参考値。",
        "issuer": "国土交通省 道路局",
        "title": "令和3年度全国道路・街路交通情勢調査 一般交通量調査 集計結果整理表 表5「旅行速度整理表」",
        "year": "2021",
        "page": "表5-12、全国・一般道路計、昼間12時間平均・合計",
        "url": "https://www.mlit.go.jp/road/census/r3/data/pdf/syuukei05.pdf",
    },
    "car_general_peak": {
        "label": "自動車／一般道路・朝夕混雑時：30.8 km/h（8.56 m/s）",
        "kmh": 30.8,
        "category": "自動車",
        "definition": "全国道路・街路交通情勢調査の一般道路計における朝夕旅行速度（混雑時旅行速度）の全国合計。",
        "issuer": "国土交通省 道路局",
        "title": "令和3年度全国道路・街路交通情勢調査 一般交通量調査 集計結果整理表 表5「旅行速度整理表」",
        "year": "2021",
        "page": "表5-12、全国・一般道路計、朝夕・合計",
        "url": "https://www.mlit.go.jp/road/census/r3/data/pdf/syuukei05.pdf",
    },
    "car_general_offpeak": {
        "label": "自動車／一般道路・昼間非混雑時：33.8 km/h（9.39 m/s）",
        "kmh": 33.8,
        "category": "自動車",
        "definition": "全国道路・街路交通情勢調査の一般道路計における昼間旅行速度（非混雑時旅行速度）の全国合計。",
        "issuer": "国土交通省 道路局",
        "title": "令和3年度全国道路・街路交通情勢調査 一般交通量調査 集計結果整理表 表5「旅行速度整理表」",
        "year": "2021",
        "page": "表5-12、全国・一般道路計、昼間・合計",
        "url": "https://www.mlit.go.jp/road/census/r3/data/pdf/syuukei05.pdf",
    },
    "car_previous_estimate": {
        "label": "自動車／過去の概算設定値：30.0 km/h（8.33 m/s、官公庁の平均値ではありません）",
        "kmh": 30.0,
        "category": "自動車（操作的仮定）",
        "definition": "過去の会話で市街地・生活道路を含む保守的な操作的仮定として用いた値。官公庁の実測平均値ではありません。官公庁の参考値を使う場合は、国土交通省調査の30.5 km/h等を選択してください。",
        "issuer": "過去の解析設定（利用者向け参考値）",
        "title": "市街地・生活道路を想定した操作的仮定（公的統計値ではない）",
        "year": "2026",
        "page": "",
        "url": "",
    },
}


def _parts(geom):
    if geom.isMultipart():
        parts = geom.asMultiPolyline()
        if parts:
            return parts
    line = geom.asPolyline()
    if line:
        return [line]
    # Rectangle clipping can produce a geometry collection for multipart input.
    parts = []
    try:
        for component in geom.asGeometryCollection():
            parts.extend(_parts(component))
    except (AttributeError, TypeError):
        pass
    return parts


def _point_label(feature, name_field=None, number=None):
    if name_field:
        val = feature.attribute(name_field)
        if val not in (None, ""):
            return "{}（候補{}）".format(val, number) if number is not None else str(val)
    if number is not None:
        return "地点（レコード番号 {}）".format(feature.id())
    return "選択地点（レコード番号 {}）".format(feature.id())


class AccessibilityDialog(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.language = "ja"
        self.car_census_data = {}
        self.car_census_road_types = {}
        self.car_census_regions = []
        self._load_car_census_data()
        self.setWindowTitle("G-CHAM Network Analysis")
        self.layer_combo = QComboBox()
        self.analysis_mode_combo = QComboBox()
        self.analysis_mode_combo.addItem("最短距離ルート", "route")
        self.analysis_mode_combo.addItem("複数起点からの到達圏", "catchment")
        self.analysis_mode_combo.addItem("複数チームで全訪問先を巡回", "team_all")
        self.analysis_mode_combo.addItem("時間内で対応人数・優先度を最大化", "team_coverage")
        self.catchment_limit_combo = QComboBox()
        self.catchment_limit_combo.addItem("距離", "distance")
        self.catchment_limit_combo.addItem("所要時間", "time")
        self.catchment_limit_value = QDoubleSpinBox()
        self.catchment_limit_value.setRange(0.01, 10000000.0)
        self.catchment_limit_value.setDecimals(1)
        self.catchment_limit_value.setValue(1000.0)
        self.catchment_limit_unit = QLabel("m")
        self.catchment_mode_combo = QComboBox()
        self.catchment_mode_combo.addItem("起点ごとに個別", "individual")
        self.catchment_mode_combo.addItem("全起点で統合（軽量）", "combined")
        self.catchment_mode_combo.setCurrentIndex(1)
        self.catchment_mode_combo.setToolTip(
            "統合：全起点から届く道路区間を重複なく1つにまとめます。\n"
            "個別：起点ごとの到達道路を出力します。同じ道路が重複して記録されることがあります。"
        )
        self.origin_layer_combo = QComboBox()
        self._selection_layer = None
        self.origin_name_field_combo = QComboBox()
        self.origin_point_combo = QComboBox()
        self.selected_origins_check = QCheckBox("選択した地物のみを使用する")
        self.selected_origins_check.setChecked(False)
        self.selected_origins_count = QLabel("選択中の地物：0件")
        self.dest_layer_combo = QComboBox()
        self.dest_name_field_combo = QComboBox()
        self.dest_point_combo = QComboBox()
        self.dest_people_field_combo = QComboBox()
        self.dest_priority_field_combo = QComboBox()
        self.dest_service_field_combo = QComboBox()
        self.plan_selected_destinations_check = QCheckBox("選択した地物のみを訪問先にする")
        self.plan_selected_destinations_check.setChecked(False)
        self.plan_team_count = QSpinBox()
        self.plan_team_count.setRange(1, 100)
        self.plan_team_count.setValue(4)
        self.plan_team_size = QSpinBox()
        self.plan_team_size.setRange(1, 50)
        self.plan_team_size.setValue(3)
        self.plan_team_size.setToolTip(
            "対象者1人あたりの追加対応時間を設定したときだけ、対応時間の計算に使います。"
            "追加時間が0分の場合、チーム人数は所要時間に影響しません。"
        )
        self.plan_shift_hours = QDoubleSpinBox()
        self.plan_shift_hours.setRange(0.25, 24.0)
        self.plan_shift_hours.setDecimals(2)
        self.plan_shift_hours.setValue(8.0)
        self.plan_break_minutes = QSpinBox()
        self.plan_break_minutes.setRange(0, 240)
        self.plan_break_minutes.setValue(60)
        self.plan_service_minutes = QDoubleSpinBox()
        self.plan_service_minutes.setRange(0.0, 1440.0)
        self.plan_service_minutes.setDecimals(1)
        self.plan_service_minutes.setValue(30.0)
        self.plan_service_minutes.setToolTip(
            "初期設定では、すべての訪問先に同じ対応時間を適用します。"
            "対応時間カラムを選択した場合は、値が空欄の訪問先に使う代替時間です。"
        )
        self.plan_per_person_minutes = QDoubleSpinBox()
        self.plan_per_person_minutes.setRange(0.0, 240.0)
        self.plan_per_person_minutes.setDecimals(1)
        self.plan_per_person_minutes.setValue(0.0)
        self.plan_per_person_minutes.setToolTip(
            "訪問先の人数 × この時間 ÷ 1チームの人数を、訪問先対応時間に加算します。"
            "チーム内で同時に対応できるという簡略化した仮定です。"
        )
        self.plan_return_to_base = QCheckBox("行動終了後に拠点へ戻る")
        self.plan_return_to_base.setChecked(True)
        self.plan_reward_combo = QComboBox()
        self.plan_reward_combo.addItem("対応人数を最大化", "people")
        self.plan_reward_combo.addItem("優先度を加味した対応人数を最大化", "weighted")
        self.objective_label = QLabel("最短距離ルート（試作版）")
        self.speed_combo = QComboBox()
        for key in ("walk_adult", "walk_elderly"):
            self.speed_combo.addItem(SPEED_PRESETS[key]["label"], key)
        self.speed_combo.insertSeparator(self.speed_combo.count())
        for key in ("walk_disaster_plan", "walk_disaster_support"):
            self.speed_combo.addItem(SPEED_PRESETS[key]["label"], key)
        self.speed_combo.insertSeparator(self.speed_combo.count())
        for key in (
            "walk_disaster_observed", "walk_disaster_single",
            "walk_disaster_impaired_companion", "walk_disaster_adult",
            "walk_disaster_slow_companions",
        ):
            self.speed_combo.addItem(SPEED_PRESETS[key]["label"], key)
        self.speed_combo.insertSeparator(self.speed_combo.count())
        for key in ("walk_school_primary", "walk_school_middle"):
            self.speed_combo.addItem(SPEED_PRESETS[key]["label"], key)
        self.speed_combo.insertSeparator(self.speed_combo.count())
        for key in ("free", "road"):
            self.speed_combo.addItem(SPEED_PRESETS[key]["label"], key)
        self.speed_combo.insertSeparator(self.speed_combo.count())
        self.speed_combo.addItem("自動車／全国道路調査から地域・道路種別・時間帯を選択", "car_census")
        self.speed_combo.addItem(SPEED_PRESETS["car_previous_estimate"]["label"], "car_previous_estimate")
        self.speed_combo.insertSeparator(self.speed_combo.count())
        self.speed_combo.addItem("任意の速度を入力", "custom")
        self.custom_speed_value = QDoubleSpinBox()
        self.custom_speed_value.setRange(0.01, 10000.0)
        self.custom_speed_value.setDecimals(2)
        self.custom_speed_value.setValue(4.68)
        self.custom_speed_unit_combo = QComboBox()
        self.custom_speed_unit_combo.addItem("km/h", "kmh")
        self.custom_speed_unit_combo.addItem("m/s", "mps")
        self.custom_speed_equivalent = QLabel()
        self.custom_speed_note = QLineEdit()
        self.custom_speed_note.setPlaceholderText("根拠や設定理由（任意）")
        self.custom_speed_url = QLineEdit()
        self.custom_speed_url.setPlaceholderText("出典URL（任意）")
        self.car_census_region_combo = QComboBox()
        self.car_census_region_combo.addItem("（統計地域を選択）", "")
        for region in self.car_census_regions:
            self.car_census_region_combo.addItem(
                self._car_census_region_label(region), region
            )
        self.car_census_road_combo = QComboBox()
        self.car_census_road_combo.addItem("（道路種別を選択）", "")
        self.car_census_period_combo = QComboBox()
        self.car_census_period_combo.addItem("朝夕の混雑時（7–9時または17–19時）", "peak")
        self.car_census_period_combo.addItem("昼間の非混雑時（9–17時）", "daytime")
        self.car_census_period_combo.addItem("昼間12時間平均（交通量加重）", "weighted")
        self.car_census_period_combo.setCurrentIndex(2)
        self.car_census_area_combo = QComboBox()
        self.car_census_area_combo.addItem("DID（商業地域）", 0)
        self.car_census_area_combo.addItem("DID（商業地域を除く）", 1)
        self.car_census_area_combo.addItem("その他の市街部", 2)
        self.car_census_area_combo.addItem("平地部", 3)
        self.car_census_area_combo.addItem("山地部", 4)
        self.car_census_area_combo.addItem("合計", 5)
        self.car_census_area_combo.setCurrentIndex(5)
        self.car_census_note = QLabel(
            "ここで選ぶ地域は速度統計の集計地域です。解析範囲を切り抜く設定ではありません。"
            "選択した平均速度をネットワーク全体に一律適用し、道路区間ごとの速度差は扱いません。"
        )
        self.car_census_note.setWordWrap(True)
        self.car_census_note.setStyleSheet("color: #555;")
        self.car_census_road_help = QLabel(
            "地域は選択中の時間帯・地域区分に公表値がある地域だけを表示します。"
            "道路種別は区分名の先頭に分類を表示し、公表値がない区分（表の「－」）は候補から除きます。"
        )
        self.car_census_road_help.setWordWrap(True)
        self.car_census_road_help.setStyleSheet("color: #555;")
        self.source_label = QLabel()
        self.source_label.setWordWrap(True)
        self.source_label.setTextFormat(RICH_TEXT_FORMAT)
        self.source_label.setOpenExternalLinks(True)
        self.snap_spin = QSpinBox()
        self.snap_spin.setRange(1, 500)
        self.snap_spin.setValue(100)
        self.snap_spin.setSuffix(" m")
        self.snap_help = QLabel(
            "初期値は100 mです。解析前に起点・目的地すべてについて、道路ラインの頂点（交差点・端点）までの距離を確認します。超える地点があれば、全地点が接続できる最小距離を提示します。"
        )
        self.snap_help.setWordWrap(True)
        self.snap_help.setStyleSheet("color: #555;")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("例：C:/成果/route_results.gpkg")
        self.output_edit.setMinimumWidth(120)
        self.output_browse_button = QPushButton("保存先を選択…")
        self.output_browse_button.setMinimumWidth(112)
        self.output_browse_button.clicked.connect(self.choose_output)
        self.result_layer_name_edit = QLineEdit("G-CHAM Network Analysis 結果")
        self.run_button = QPushButton("解析して結果を保存")
        self.cancel_button = QPushButton("閉じる")
        self.language_button = QPushButton("English")
        self.language_button.setToolTip("Switch the plugin interface to English")
        self.language_button.clicked.connect(self.toggle_language)
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumBlockCount(2000)
        self.log_edit.setMinimumHeight(115)
        self.run_button.clicked.connect(self.run_analysis)
        self.cancel_button.clicked.connect(self.reject)
        self.speed_combo.currentIndexChanged.connect(self.update_source_label)
        self.speed_combo.currentIndexChanged.connect(self.update_custom_speed_controls)
        self.speed_combo.currentIndexChanged.connect(self.update_car_census_controls)
        self.car_census_region_combo.currentIndexChanged.connect(self.update_car_census_road_types)
        self.car_census_road_combo.currentIndexChanged.connect(self.update_source_label)
        self.car_census_period_combo.currentIndexChanged.connect(self.update_car_census_regions)
        self.car_census_area_combo.currentIndexChanged.connect(self.update_car_census_regions)
        self.custom_speed_value.valueChanged.connect(self.update_source_label)
        self.custom_speed_value.valueChanged.connect(self.update_custom_speed_equivalent)
        self.custom_speed_unit_combo.currentIndexChanged.connect(self.update_source_label)
        self.custom_speed_unit_combo.currentIndexChanged.connect(self.update_custom_speed_equivalent)
        self.custom_speed_note.textChanged.connect(self.update_source_label)
        self.custom_speed_url.textChanged.connect(self.update_source_label)
        self.analysis_mode_combo.currentIndexChanged.connect(self.update_custom_speed_controls)
        self.catchment_limit_combo.currentIndexChanged.connect(self.update_custom_speed_controls)
        self.origin_layer_combo.currentIndexChanged.connect(self.refresh_origin_inputs)
        self.origin_name_field_combo.currentIndexChanged.connect(self.refresh_origin_points)
        self.dest_layer_combo.currentIndexChanged.connect(self.refresh_dest_inputs)
        self.dest_name_field_combo.currentIndexChanged.connect(self.refresh_dest_points)
        self.dest_layer_combo.currentIndexChanged.connect(self.refresh_plan_fields)
        self.selected_origins_check.toggled.connect(self.update_origin_controls)
        self.analysis_mode_combo.currentIndexChanged.connect(self.update_analysis_controls)
        self.catchment_limit_combo.currentIndexChanged.connect(self.update_catchment_limit_unit)
        self._load_layers()
        form = QFormLayout()
        try:
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        except AttributeError:
            form.setRowWrapPolicy(QFormLayout.WrapLongRows)
            form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        compact_combos = (
            self.layer_combo, self.analysis_mode_combo, self.catchment_limit_combo,
            self.catchment_mode_combo, self.origin_layer_combo,
            self.origin_name_field_combo, self.origin_point_combo,
            self.dest_layer_combo, self.dest_name_field_combo,
            self.dest_point_combo, self.dest_people_field_combo,
            self.dest_priority_field_combo, self.dest_service_field_combo,
            self.plan_reward_combo, self.speed_combo,
            self.custom_speed_unit_combo, self.car_census_region_combo,
            self.car_census_road_combo, self.car_census_period_combo,
            self.car_census_area_combo,
        )
        try:
            combo_policy = QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        except AttributeError:
            combo_policy = QComboBox.AdjustToMinimumContentsLengthWithIcon
        for combo in compact_combos:
            combo.setMinimumContentsLength(12)
            combo.setSizeAdjustPolicy(combo_policy)
        form.addRow("解析の種類", self.analysis_mode_combo)
        form.addRow("道路ネットワーク（ライン）", self.layer_combo)
        form.addRow("起点レイヤ", self.origin_layer_combo)
        form.addRow("起点リストに表示する名称カラム", self.origin_name_field_combo)
        form.addRow("起点の指定", self.selected_origins_check)
        form.addRow("選択状況", self.selected_origins_count)
        form.addRow("起点となる地点", self.origin_point_combo)
        form.addRow("目的地レイヤ", self.dest_layer_combo)
        form.addRow("目的地リストに表示する名称カラム", self.dest_name_field_combo)
        form.addRow("目的地となる地点", self.dest_point_combo)
        form.addRow("配送・巡回先の選択", self.plan_selected_destinations_check)
        form.addRow("対応対象人数のカラム", self.dest_people_field_combo)
        form.addRow("優先度の数値カラム", self.dest_priority_field_combo)
        form.addRow("対応時間の設定方法", self.dest_service_field_combo)
        form.addRow("最適化する対応価値", self.plan_reward_combo)
        form.addRow("チーム数", self.plan_team_count)
        form.addRow("1チームの人数（人）", self.plan_team_size)
        form.addRow("チームごとの行動可能時間（時間）", self.plan_shift_hours)
        form.addRow("チームごとの休憩時間（分）", self.plan_break_minutes)
        form.addRow("全訪問先共通の対応時間（分）", self.plan_service_minutes)
        form.addRow("対象者1人あたりの追加対応時間（分）", self.plan_per_person_minutes)
        form.addRow("帰着条件", self.plan_return_to_base)
        form.addRow("到達圏の基準", self.catchment_limit_combo)
        catchment_limit_row = QHBoxLayout()
        catchment_limit_row.addWidget(self.catchment_limit_value)
        catchment_limit_row.addWidget(self.catchment_limit_unit)
        form.addRow("上限", catchment_limit_row)
        form.addRow("複数起点の集計方法", self.catchment_mode_combo)
        form.addRow("ルート計算", self.objective_label)
        form.addRow("移動速度（速度と出典を選択）", self.speed_combo)
        custom_speed_row = QHBoxLayout()
        custom_speed_row.addWidget(self.custom_speed_value)
        custom_speed_row.addWidget(self.custom_speed_unit_combo)
        custom_speed_row.addWidget(self.custom_speed_equivalent)
        form.addRow("任意速度", custom_speed_row)
        form.addRow("自動車統計の地域", self.car_census_region_combo)
        form.addRow("自動車統計の道路種別", self.car_census_road_combo)
        form.addRow("道路種別の選び方", self.car_census_road_help)
        form.addRow("自動車統計の時間帯", self.car_census_period_combo)
        form.addRow("自動車統計の地域区分", self.car_census_area_combo)
        form.addRow("自動車速度の適用について", self.car_census_note)
        form.addRow("任意速度の根拠・メモ", self.custom_speed_note)
        form.addRow("任意速度の出典URL", self.custom_speed_url)
        form.addRow("速度の出典", self.source_label)
        form.addRow("地点から道路までのずれを許す距離", self.snap_spin)
        form.addRow("この設定について", self.snap_help)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit)
        output_row.addWidget(self.output_browse_button)
        output_row.setStretch(0, 1)
        form.addRow("共通の出力先（.gpkg）", output_row)
        self.output_note = QLabel("同じフォルダ・同じ名前で .csv と .gpkg を作成します。到達圏では施設別・全体のサマリーCSVも作成します。既存ファイルがある場合は日時を付けて別名保存します。")
        self.output_note.setWordWrap(True)
        form.addRow("出力ファイルについて", self.output_note)
        form.addRow("QGISに追加するレイヤ名", self.result_layer_name_edit)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.cancel_button)
        note = QLabel(
            "「選択した地物のみを使用する」は任意設定で、初期状態はオフです。オンにすると、起点レイヤで選択中の地物をすべて起点として使います。"
            "最短距離ルートでは複数起点から1か所の目的地まで計算できます。到達圏では起点レイヤ上で複数地点を選択し、距離または所要時間内に道路網上で到達できる道路区間を出力します。結果はCSVとGeoPackageに保存し、GeoPackageのレイヤをQGISへ追加します。\n"
            "到達圏の「全起点で統合」は、いずれかの起点から届く道路区間の和集合を重複なく出力します。「起点ごとに個別」は起点別に計算し、重複区間も起点ごとに出力します。個別モードではサマリーCSVに施設別の到達道路延長・到達距離・参考時間を記録します。統合モードの施設別行は出力区間の帰属先別集計で、個々の施設単独の到達圏ではありません。\n"
            "到達圏の道路を囲む凸包ポリゴンもGeoPackageに追加します。個別モードは起点別凸包とその融合範囲、統合モードは統合到達区間の帰属先別凸包を出力します。統合モードの凸包は各起点単独の到達圏ではありません。凸包の内部がすべて到達可能とは限りません。\n"
            "巡回計画では拠点1か所から複数チームが出発し、全訪問先の分担、または指定時間内の対応人数・優先度の最大化を試算できます。人数・訪問時間・休憩・チーム人数を設定し、訪問先レイヤの属性を選べます。\n"
            "巡回計画は道路上の距離行列を用いる試作ヒューリスティックで、全体最適を保証しません。訪問先が多い場合は計算に時間がかかります。時間帯指定や複数拠点は未対応です。\n"
            "試作版の前提：道路ラインは交差点で分割・接続済み、投影座標系（メートル）を使用。"
            "一方通行、歩行・自転車・自動車の通行規制、信号ごとの待ち時間はまだ扱いません。"
        )
        self._information_note_japanese = note.text()
        self.information_note = note
        note.setWordWrap(True)
        note.setStyleSheet("color: #555; padding: 6px;")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addLayout(form)
        content_layout.addWidget(note)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        try:
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        except AttributeError:
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        layout = QVBoxLayout(self)
        language_row = QHBoxLayout()
        language_row.addStretch(1)
        language_row.addWidget(self.language_button)
        layout.addLayout(language_row)
        layout.addWidget(scroll, 1)
        layout.addWidget(QLabel("実行ログ"))
        layout.addWidget(self.log_edit)
        layout.addLayout(buttons)
        self.resize(680, 820)
        self.update_custom_speed_controls()
        self.update_car_census_controls()
        self.update_car_census_regions()
        self.update_custom_speed_equivalent()
        self.update_source_label()
        self.update_origin_controls()
        self.update_analysis_controls()
        self.update_catchment_limit_unit()
        self._log("準備完了。出力先を1つ指定して解析を開始できます。")

    def _text(self, value):
        return translate_text(value, self.language)

    def toggle_language(self):
        global OUTPUT_LANGUAGE
        self.language = "en" if self.language == "ja" else "ja"
        OUTPUT_LANGUAGE = self.language
        self.language_button.setText("日本語" if self.language == "en" else "English")
        self.language_button.setToolTip(
            "Switch the plugin interface to Japanese" if self.language == "en"
            else "Switch the plugin interface to English"
        )
        default_names = {"G-CHAM Network Analysis 結果", "G-CHAM Network Analysis Results"}
        if self.result_layer_name_edit.text() in default_names:
            self.result_layer_name_edit.setText(
                "G-CHAM Network Analysis Results" if self.language == "en"
                else "G-CHAM Network Analysis 結果"
            )
        self.log_edit.clear()
        self._apply_language()
        self.update_source_label()
        self.update_custom_speed_equivalent()
        self.update_selected_origins_count()
        self._log("Language switched to English." if self.language == "en" else "日本語表示に切り替えました。")

    def _apply_language(self, root=None):
        """Translate static control text while keeping layer and field names intact."""
        from qgis.PyQt.QtWidgets import QAbstractButton, QAbstractSpinBox, QLineEdit
        root = root or self
        source_data_combos = {
            self.layer_combo, self.origin_layer_combo, self.origin_name_field_combo,
            self.origin_point_combo, self.dest_layer_combo, self.dest_name_field_combo,
            self.dest_point_combo, self.dest_people_field_combo,
            self.dest_priority_field_combo, self.dest_service_field_combo,
        }
        if root is self and self.language == "en":
            self.setWindowTitle("G-CHAM Network Analysis")
            self.language_button.setText("日本語")
        elif root is self:
            self.setWindowTitle("G-CHAM Network Analysis")
            self.language_button.setText("English")
        for widget in root.findChildren(QWidget):
            if widget is self.language_button:
                continue
            if isinstance(widget, QComboBox):
                if widget in source_data_combos:
                    continue
                for index in range(widget.count()):
                    item = widget.itemText(index)
                    if not item:
                        continue
                    if widget is self.car_census_region_combo:
                        region = widget.itemData(index)
                        translated = translate_region_label(region, self.language) if region else self._text(item)
                    elif widget is self.car_census_road_combo:
                        road_type = widget.itemData(index)
                        base = ROAD_TYPE_DISPLAY.get(road_type, road_type or item)
                        translated = self._text(base)
                    else:
                        translated = self._text(item)
                    if translated == item and self.language == "en":
                        # Human readable labels for official traffic census categories.
                        translated = _translate_road_label(item)
                    widget.setItemText(index, translated)
            elif isinstance(widget, QAbstractButton):
                widget.setText(self._text(widget.text()))
            elif isinstance(widget, QLabel):
                widget.setText(self._text(widget.text()))
            if widget.toolTip():
                widget.setToolTip(self._text(widget.toolTip()))
            if isinstance(widget, QLineEdit) and widget.placeholderText():
                widget.setPlaceholderText(self._text(widget.placeholderText()))
            if isinstance(widget, QAbstractSpinBox) and widget.suffix():
                widget.setSuffix(self._text(widget.suffix()))
        if hasattr(self, "output_note"):
            self.output_note.setText(
                "Creates a CSV and GeoPackage with the same base name. Catchment analysis also creates a summary CSV. Existing files are saved under a timestamped name."
                if self.language == "en" else
                "同じフォルダ・同じ名前で .csv と .gpkg を作成します。到達圏では施設別・全体のサマリーCSVも作成します。既存ファイルがある場合は日時を付けて別名保存します。"
            )
        if hasattr(self, "information_note"):
            self.information_note.setText(
                "Use the selected-features option to limit origins or destinations to features selected in QGIS. For catchments, all origin points are used when the option is off. Catchment limits can be based on distance or estimated travel time. Results include road segments, aggregated lines, and convex hulls. Convex hull interiors are not guaranteed to be reachable.\n\n"
                "Patrol planning assigns destinations to teams from one base. It supports plans to visit all destinations and plans that maximize people served or priority within a time limit. The route order uses a prototype heuristic and is not guaranteed to be globally optimal. Large road networks and many destinations can require substantial processing time.\n\n"
                "Road lines should be split and connected at intersections and use a projected CRS in meters. One-way rules, access restrictions, and intersection delays are not modeled."
                if self.language == "en" else self._information_note_japanese
            )


    def _project_layers(self):
        return list(QgsProject.instance().mapLayers().values())

    def _car_census_region_parent(self, region):
        for prefecture in PREFECTURE_ORDER:
            if region.startswith(prefecture):
                return prefecture
        for prefecture in PREFECTURE_ORDER:
            for grouped_region in self.car_census_regions:
                if not grouped_region.startswith(prefecture + "（"):
                    continue
                excluded = grouped_region[len(prefecture) + 1:].split("を除く）", 1)[0]
                cities = [name.strip() for name in excluded.split("、")]
                if region in cities:
                    return prefecture
        return "全国"

    def _car_census_region_sort_key(self, region):
        parent = self._car_census_region_parent(region)
        try:
            prefecture_index = PREFECTURE_ORDER.index(parent)
        except ValueError:
            return (len(PREFECTURE_ORDER), 0, region)
        if region == parent or region == parent + "全域":
            group_order = 0
        elif region.startswith(parent + "（"):
            group_order = 1
        elif parent != region:
            group_order = 2
        else:
            group_order = 3
        return (prefecture_index, group_order, region)

    def _car_census_region_label(self, region):
        parent = self._car_census_region_parent(region)
        if parent == "全国":
            label = "全国｜合計" if region == "合計" else region
            return translate_region_label(label, self.language)
        if region == parent:
            return translate_region_label(region, self.language)
        if region.startswith(parent):
            return translate_region_label(region, self.language)
        return translate_region_label("{}｜{}".format(parent, region), self.language)

    @staticmethod
    def _has_numeric_census_value(value):
        try:
            return math.isfinite(float(str(value).strip()))
        except (TypeError, ValueError):
            return False

    def _load_car_census_data(self):
        """同梱した国土交通省の令和3年度CSVを読み込む。"""
        data_path = Path(__file__).parent / "data" / "mlit_r3_syuukei05.csv"
        current_region = ""
        try:
            with data_path.open("r", encoding="cp932", newline="") as handle:
                reader = csv.reader(handle)
                next(reader, None)
                for row in reader:
                    if len(row) < 20:
                        continue
                    if row[0].strip():
                        current_region = row[0].strip()
                        if current_region not in self.car_census_regions:
                            self.car_census_regions.append(current_region)
                            self.car_census_road_types[current_region] = []
                    road_type = row[1].strip()
                    if not current_region or not road_type:
                        continue
                    values = row[2:20]
                    if not any(self._has_numeric_census_value(value) for value in values):
                        continue
                    self.car_census_data[(current_region, road_type)] = values
                    if road_type not in self.car_census_road_types[current_region]:
                        self.car_census_road_types[current_region].append(road_type)
            self.car_census_regions = [
                region for region in self.car_census_regions
                if self.car_census_road_types.get(region)
            ]
            self.car_census_regions.sort(key=self._car_census_region_sort_key)
        except (OSError, UnicodeError, csv.Error):
            self.car_census_data = {}
            self.car_census_road_types = {}
            self.car_census_regions = []

    def _load_layers(self):
        origin_was_blocked = self.origin_layer_combo.blockSignals(True)
        dest_was_blocked = self.dest_layer_combo.blockSignals(True)
        try:
            for layer in self._project_layers():
                # QgsProject.mapLayers()にはラスターレイヤーも含まれる。
                # geometryType()はベクターレイヤー専用なので、先に型を限定する。
                if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
                    continue
                if layer.geometryType() == LINE_GEOMETRY_TYPE:
                    self.layer_combo.addItem(layer.name(), layer.id())
                elif layer.geometryType() == POINT_GEOMETRY_TYPE:
                    self.origin_layer_combo.addItem(layer.name(), layer.id())
                    self.dest_layer_combo.addItem(layer.name(), layer.id())
        finally:
            self.origin_layer_combo.blockSignals(origin_was_blocked)
            self.dest_layer_combo.blockSignals(dest_was_blocked)
        self.refresh_origin_inputs()
        self.refresh_dest_inputs()

    def _layer(self, combo):
        layer_id = combo.currentData()
        return QgsProject.instance().mapLayer(layer_id) if layer_id else None

    @staticmethod
    def _populate_name_fields(combo, layer):
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("（レコード番号で表示）", "")
        preferred = ("name", "名称", "施設名", "施設名称", "地名", "NAME")
        if layer:
            field_names = [field.name() for field in layer.fields()]
            for field_name in field_names:
                combo.addItem(field_name, field_name)
            for name in preferred:
                idx = layer.fields().indexFromName(name)
                if idx >= 0:
                    combo.setCurrentIndex(idx + 1)
                    break
        combo.blockSignals(False)

    def refresh_origin_inputs(self):
        layer = self._layer(self.origin_layer_combo)
        self._populate_name_fields(self.origin_name_field_combo, layer)
        self.refresh_origin_points()
        if self.language == "en":
            self._apply_language()

    def refresh_dest_inputs(self):
        layer = self._layer(self.dest_layer_combo)
        self._populate_name_fields(self.dest_name_field_combo, layer)
        self.refresh_dest_points()
        self.refresh_plan_fields()
        if self.language == "en":
            self._apply_language()

    def refresh_plan_fields(self, *_args):
        layer = self._layer(self.dest_layer_combo)
        field_sets = (
            (self.dest_people_field_combo, "（人数カラムを使わない）",
             ("対象人数", "人数", "人口", "需要", "population", "people")),
            (self.dest_priority_field_combo, "（優先度を使わない）",
             ("優先度", "priority", "順位")),
            (self.dest_service_field_combo, "（訪問先共通の時間を使う）",
             ("対応時間", "訪問時間", "service", "時間")),
        )
        for combo, placeholder, preferred_names in field_sets:
            previous = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(placeholder, "")
            field_names = [field.name() for field in layer.fields()] if layer else []
            for field_name in field_names:
                combo.addItem(field_name, field_name)
            selected = combo.findData(previous) if previous else -1
            if selected < 0:
                lower_names = {name.lower(): name for name in field_names}
                for preferred in preferred_names:
                    match = next(
                        (name for name in field_names
                         if preferred.lower() in name.lower()),
                        lower_names.get(preferred.lower()),
                    )
                    if match:
                        selected = combo.findData(match)
                        break
            combo.setCurrentIndex(selected if selected >= 0 else 0)
            combo.blockSignals(False)
        if self.language == "en":
            self._apply_language()

    def _populate_points(self, combo, layer, name_field):
        combo.clear()
        if not layer:
            return
        request = QgsFeatureRequest()
        request.setFlags(NO_GEOMETRY_FLAG)
        if name_field:
            request.setSubsetOfAttributes([name_field], layer.fields())
        for number, feature in enumerate(layer.getFeatures(request), 1):
            combo.addItem(_point_label(feature, name_field, number), int(feature.id()))

    def refresh_origin_points(self):
        layer = self._layer(self.origin_layer_combo)
        self._populate_points(
            self.origin_point_combo, layer, self.origin_name_field_combo.currentData()
        )
        if self._selection_layer is not None:
            try:
                self._selection_layer.selectionChanged.disconnect(self.update_selected_origins_count)
            except (TypeError, RuntimeError):
                pass
        self._selection_layer = layer
        if layer is not None:
            layer.selectionChanged.connect(self.update_selected_origins_count)
        self.update_selected_origins_count()

    def refresh_dest_points(self):
        self._populate_points(
            self.dest_point_combo, self._layer(self.dest_layer_combo),
            self.dest_name_field_combo.currentData()
        )

    def update_origin_controls(self):
        use_selected = self.selected_origins_check.isChecked()
        catchment = self.analysis_mode_combo.currentData() == "catchment"
        self.origin_point_combo.setEnabled(not use_selected and not catchment)
        self.update_selected_origins_count()

    def update_analysis_controls(self, *_args):
        mode = self.analysis_mode_combo.currentData()
        catchment = mode == "catchment"
        planning = mode in ("team_all", "team_coverage")
        # Patrol plans use one base, which may be picked from the origin
        # layer selection just like other analysis modes.
        self.selected_origins_check.setEnabled(True)
        for widget in (self.dest_layer_combo, self.dest_name_field_combo):
            widget.setEnabled(not catchment)
        self.dest_point_combo.setEnabled(not catchment and not planning)
        for widget in (self.catchment_limit_combo, self.catchment_limit_value, self.catchment_mode_combo):
            widget.setEnabled(catchment)
        self.objective_label.setText(
            "到達可能な道路区間を抽出" if catchment else
            "複数チームの巡回計画（試作ヒューリスティック）" if planning else
            "最短距離ルート（試作版）"
        )
        plan_widgets = (
            self.plan_selected_destinations_check, self.dest_people_field_combo,
            self.dest_priority_field_combo, self.dest_service_field_combo,
            self.plan_team_count, self.plan_team_size, self.plan_shift_hours,
            self.plan_break_minutes, self.plan_service_minutes,
            self.plan_per_person_minutes,
            self.plan_return_to_base,
        )
        for widget in plan_widgets:
            widget.setEnabled(planning)
        self.plan_reward_combo.setEnabled(planning and mode == "team_coverage")
        distance_only = catchment and self.catchment_limit_combo.currentData() == "distance"
        for widget in (self.speed_combo, self.custom_speed_value, self.custom_speed_unit_combo,
                       self.custom_speed_note, self.custom_speed_url):
            widget.setEnabled(not distance_only)
        self.source_label.setEnabled(not distance_only)
        self.run_button.setText(
            "到達圏を解析して保存" if catchment else
            "巡回計画を作成して保存" if planning else
            "解析して結果を保存"
        )
        self.update_car_census_controls()
        self.update_origin_controls()
        if self.language == "en":
            self._apply_language()

    def update_car_census_controls(self, *_args):
        distance_only = (
            self.analysis_mode_combo.currentData() == "catchment"
            and self.catchment_limit_combo.currentData() == "distance"
        )
        enabled = self.speed_combo.currentData() == "car_census" and not distance_only
        for widget in (
            self.car_census_region_combo, self.car_census_road_combo,
            self.car_census_period_combo, self.car_census_area_combo,
        ):
            widget.setEnabled(enabled)
        self.car_census_note.setEnabled(enabled)

    def update_car_census_regions(self, *_args):
        """Show only regions with values for the selected period and area."""
        period = self.car_census_period_combo.currentData()
        area_index = self.car_census_area_combo.currentData()
        offsets = {"peak": 0, "daytime": 6, "weighted": 12}
        offset = offsets.get(period)
        previous = self.car_census_region_combo.currentData()
        available_regions = []
        if offset is not None and area_index is not None:
            value_index = offset + int(area_index)
            for region in self.car_census_regions:
                if any(
                    value_index < len(values)
                    and self._has_numeric_census_value(values[value_index])
                    for (data_region, _road), values in self.car_census_data.items()
                    if data_region == region
                ):
                    available_regions.append(region)

        was_blocked = self.car_census_region_combo.blockSignals(True)
        self.car_census_region_combo.clear()
        self.car_census_region_combo.addItem("（統計地域を選択）", "")
        for region in available_regions:
            self.car_census_region_combo.addItem(
                self._car_census_region_label(region), region
            )
        selected = self.car_census_region_combo.findData(previous) if previous else -1
        self.car_census_region_combo.setCurrentIndex(selected if selected >= 0 else 0)
        self.car_census_region_combo.blockSignals(was_blocked)
        self.update_car_census_road_types()

    def update_car_census_road_types(self, *_args):
        region = self.car_census_region_combo.currentData()
        period = self.car_census_period_combo.currentData()
        area_index = self.car_census_area_combo.currentData()
        offsets = {"peak": 0, "daytime": 6, "weighted": 12}
        offset = offsets.get(period)
        was_blocked = self.car_census_road_combo.blockSignals(True)
        previous = self.car_census_road_combo.currentData()
        self.car_census_road_combo.clear()
        self.car_census_road_combo.addItem("（道路種別を選択）", "")
        available = []
        if region:
            for road_type in self.car_census_road_types.get(region, []):
                values = self.car_census_data.get((region, road_type), [])
                value_index = (
                    offset + int(area_index)
                    if offset is not None and area_index is not None else None
                )
                if (value_index is not None and value_index < len(values)
                        and self._has_numeric_census_value(values[value_index])):
                    available.append(road_type)
                    label = self._text(ROAD_TYPE_DISPLAY.get(road_type, road_type))
                    self.car_census_road_combo.addItem(label, road_type)
            selected = self.car_census_road_combo.findData(previous) if previous else -1
            if selected < 0:
                for preferred_type in ("一般道路計", "合計"):
                    selected = self.car_census_road_combo.findData(preferred_type)
                    if selected >= 0:
                        break
            if selected < 0 and available:
                selected = 1
            if selected >= 0:
                self.car_census_road_combo.setCurrentIndex(selected)
            elif not available:
                self.car_census_road_combo.addItem("（この条件に公表値なし）", "")
        self.car_census_road_combo.blockSignals(was_blocked)
        self.update_source_label()
        if self.language == "en":
            self._apply_language()

    def update_catchment_limit_unit(self, *_args):
        self.catchment_limit_unit.setText(
            "m" if self.catchment_limit_combo.currentData() == "distance"
            else ("min" if self.language == "en" else "分")
        )
        self.catchment_limit_value.setValue(
            1000.0 if self.catchment_limit_combo.currentData() == "distance" else 15.0
        )
        self.update_analysis_controls()

    def update_selected_origins_count(self, *_args):
        layer = self._layer(self.origin_layer_combo)
        count = len(layer.selectedFeatureIds()) if layer else 0
        if (self.analysis_mode_combo.currentData() == "catchment"
                and not self.selected_origins_check.isChecked() and layer):
            self.selected_origins_count.setText(
                self._text("使用する起点：レイヤ内の全地点（{}件）").format(layer.featureCount())
            )
        else:
            self.selected_origins_count.setText(self._text("選択中の地物：{}件").format(count))

    def update_custom_speed_controls(self, *_args):
        distance_only = (
            self.analysis_mode_combo.currentData() == "catchment"
            and self.catchment_limit_combo.currentData() == "distance"
        )
        enabled = self.speed_combo.currentData() == "custom" and not distance_only
        self.custom_speed_value.setEnabled(enabled)
        self.custom_speed_unit_combo.setEnabled(enabled)
        self.custom_speed_note.setEnabled(enabled)
        self.custom_speed_url.setEnabled(enabled)

    def update_custom_speed_equivalent(self, *_args):
        value = self.custom_speed_value.value()
        if self.custom_speed_unit_combo.currentData() == "mps":
            self.custom_speed_equivalent.setText("= {:.2f} km/h".format(value * 3.6))
        else:
            self.custom_speed_equivalent.setText("= {:.2f} m/s".format(value / 3.6))

    def _selected_car_census_speed(self):
        region = self.car_census_region_combo.currentData()
        road_type = self.car_census_road_combo.currentData()
        period = self.car_census_period_combo.currentData()
        area_index = self.car_census_area_combo.currentData()
        if not region:
            raise ValueError("自動車の速度統計で都道府県・地域を選択してください。")
        if not road_type:
            raise ValueError("自動車の速度統計で道路種別を選択してください。")
        values = self.car_census_data.get((region, road_type))
        if values is None or area_index is None:
            raise ValueError("選択した自動車速度データが見つかりません。")
        period_offsets = {"peak": 0, "daytime": 6, "weighted": 12}
        period_names = {
            "peak": "朝夕旅行速度（混雑時）",
            "daytime": "昼間旅行速度（非混雑時）",
            "weighted": "昼間12時間平均旅行速度（時間帯別交通量による加重平均）",
        }
        period_offset = period_offsets[period]
        raw_speed = values[period_offset + int(area_index)].strip()
        area_label = self.car_census_area_combo.currentText()
        period_label = period_names[period]
        if raw_speed in ("", "-", "－"):
            raise ValueError(
                "選択した組合せ（{}／{}／{}／{}）の旅行速度は公表表にありません。"
                .format(region, road_type, period_label, area_label)
            )
        speed_kmh = float(raw_speed)
        pdf_url = "https://www.mlit.go.jp/road/census/r3/data/pdf/syuukei05.pdf"
        display_region = translate_region_label(region, self.language)
        display_road = _translate_road_label(ROAD_TYPE_DISPLAY.get(road_type, road_type)) if self.language == "en" else road_type
        display_period = {
            "peak": "Peak-period travel speed",
            "daytime": "Off-peak daytime travel speed",
            "weighted": "12-hour traffic-weighted daytime mean speed",
        }.get(period, period_label) if self.language == "en" else period_label
        display_area = self._text(area_label)
        if self.language == "en":
            label = "Vehicle / {} / {} / {} / {}: {:.1f} km/h ({:.2f} m/s)".format(
                display_region, display_road, display_period, display_area, speed_kmh, speed_kmh / 3.6
            )
            definition = (
                "Aggregate value from MLIT's FY2021 Road Traffic Census. Selected conditions: "
                "{}, {}, {}, {}. The selected mean is applied uniformly to the network; "
                "it is not a measured speed for each road segment."
            ).format(display_region, display_road, display_period, display_area)
        else:
            label = "自動車／{}／{}／{}／{}：{:.1f} km/h（{:.2f} m/s）".format(
                region, road_type, period_label, area_label, speed_kmh, speed_kmh / 3.6
            )
            definition = (
                "国土交通省の令和3年度全国道路・街路交通情勢調査の集計値。選択条件：{}、{}、{}、{}。"
                "選択した集計平均をネットワーク全体に一律適用します。道路区間ごとの実速度ではありません。"
            ).format(region, road_type, period_label, area_label)
        return {
            "label": label,
            "kmh": speed_kmh,
            "category": "自動車（全国道路・街路交通情勢調査）",
            "definition": definition,
            "issuer": "国土交通省 道路局",
            "title": "令和3年度全国道路・街路交通情勢調査 一般交通量調査 集計結果整理表 表5「旅行速度整理表」",
            "year": "令和3年度（2021）",
            "page": "表5「旅行速度整理表」",
            "url": pdf_url,
            "speed_region": region,
            "speed_road_type": road_type,
            "speed_time_period": period_label,
            "speed_area_category": area_label,
        }

    def _selected_speed(self):
        key = self.speed_combo.currentData()
        if key == "car_census":
            return self._selected_car_census_speed()
        if key != "custom":
            item = dict(SPEED_PRESETS.get(key, SPEED_PRESETS["walk_adult"]))
            item.setdefault("speed_region", "")
            item.setdefault("speed_road_type", "")
            item.setdefault("speed_time_period", "")
            item.setdefault("speed_area_category", "")
            if self.language == "en":
                for field in ("label", "category", "definition", "issuer", "title", "year", "page"):
                    item[field] = translate_text(item.get(field, ""), "en")
            return item
        entered = self.custom_speed_value.value()
        if self.custom_speed_unit_combo.currentData() == "mps":
            speed_mps = entered
            speed_kmh = entered * 3.6
        else:
            speed_kmh = entered
            speed_mps = entered / 3.6
        note = self.custom_speed_note.text().strip()
        source_url = self.custom_speed_url.text().strip()
        unit = self.custom_speed_unit_combo.currentData()
        entered_unit = "m/s" if unit == "mps" else "km/h"
        if self.language == "en":
            return {
                "label": "Custom input: {:.2f} {} ({:.2f} km/h, {:.2f} m/s)".format(
                    entered, entered_unit, speed_kmh, speed_mps
                ),
                "kmh": speed_kmh,
                "category": "Custom input",
                "definition": "User-entered speed: {:.4f} {}. {}".format(
                    entered, entered_unit, note or "No rationale provided."
                ),
                "issuer": "User input", "title": note or "User-defined speed",
                "year": "User input", "page": "", "url": source_url,
                "speed_region": "", "speed_road_type": "",
                "speed_time_period": "", "speed_area_category": "",
            }
        return {
            "label": "任意入力：{:.2f} {}（{:.2f} km/h、{:.2f} m/s）".format(
                entered, entered_unit, speed_kmh, speed_mps
            ),
            "kmh": speed_kmh,
            "category": "任意入力",
            "definition": "利用者が任意入力した速度。入力値：{:.4f} {}。{}".format(
                entered, entered_unit, note or "設定理由の記載なし。"
            ),
            "issuer": "利用者入力",
            "title": note or "利用者設定速度",
            "year": "利用者入力",
            "page": "",
            "url": source_url,
            "speed_region": "",
            "speed_road_type": "",
            "speed_time_period": "",
            "speed_area_category": "",
        }

    def update_source_label(self, *_args):
        try:
            item = self._selected_speed()
        except ValueError as exc:
            self.source_label.setText(html.escape(str(exc)))
            return
        speed_mps = item["kmh"] / 3.6
        issuer = html.escape(self._text(item["issuer"]))
        title = html.escape(self._text(item["title"]))
        year = html.escape(self._text(item["year"]))
        page = html.escape(self._text(item["page"]))
        definition = html.escape(self._text(item["definition"]))
        source_url = html.escape(item["url"], quote=True)
        source_line = (
            "{}, {}, {}{}".format(issuer, title, year, (", p.{}".format(page) if page else ""))
            if self.language == "en" else
            "{}、{}、{}{}".format(issuer, title, year, ("、p.{}".format(page) if page else ""))
        )
        link_line = (
            "<a href=\"{}\">{}</a>".format(source_url, "Open source" if self.language == "en" else "出典資料を開く")
            if source_url else ("Source URL: not provided" if self.language == "en" else "出典URL：未設定")
        )
        self.source_label.setText(
            "{}<br>{}<br>Speed: {:.2f} km/h ({:.2f} m/s)<br>{}".format(
                source_line, definition, item["kmh"], speed_mps, link_line
            ) if self.language == "en" else
            "{}<br>{}<br>速度：{:.2f} km/h（{:.2f} m/s）<br>{}".format(
                source_line, definition, item["kmh"], speed_mps, link_line
            )
        )

    def _log(self, message):
        stamp = datetime.now().astimezone().strftime("%H:%M:%S")
        self.log_edit.appendPlainText("[{}] {}".format(stamp, self._text(message)))
        QApplication.processEvents(EXCLUDE_USER_INPUT_EVENTS)

    def choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "結果ファイルの保存先を選択", "network_analysis_results.gpkg",
            "GeoPackage (*.gpkg)"
        )
        if path:
            selected_path = Path(path)
            if selected_path.suffix.lower() != ".gpkg":
                selected_path = selected_path.with_suffix(".gpkg") if selected_path.suffix else Path(str(selected_path) + ".gpkg")
            self.output_edit.setText(str(selected_path))

    def _get_point(self, layer, feature_id, network_layer):
        if layer is None or feature_id is None:
            raise ValueError("地点レイヤと地点を選択してください。")
        feature = layer.getFeature(int(feature_id))
        if not feature.isValid() or feature.geometry().isEmpty():
            raise ValueError("選択した地点に有効なポイント形状がありません。")
        geom = QgsGeometry(feature.geometry())
        if geom.isMultipart():
            raise ValueError("複数地点をまとめた形状には対応していません。各地点が別々のポイントであるレイヤを選んでください。")
        transform = QgsCoordinateTransform(layer.crs(), network_layer.crs(), QgsProject.instance())
        geom.transform(transform)
        pt = geom.asPoint()
        return QgsPointXY(pt.x(), pt.y()), int(feature.id()), layer.name()

    def _start_points(self, network_layer):
        layer = self._layer(self.origin_layer_combo)
        if layer is None:
            raise ValueError("起点レイヤを選択してください。")
        if self.selected_origins_check.isChecked():
            ids = sorted(layer.selectedFeatureIds())
            if not ids:
                raise ValueError("起点レイヤ上で地点を選択してください。地図上で選んだ地点を複数使えます。")
        elif self.analysis_mode_combo.currentData() == "catchment":
            request = QgsFeatureRequest()
            request.setFlags(NO_GEOMETRY_FLAG)
            ids = [int(feature.id()) for feature in layer.getFeatures(request)]
            if not ids:
                raise ValueError("起点レイヤに地点がありません。ポイントレイヤを選択してください。")
        else:
            value = self.origin_point_combo.currentData()
            if value is None:
                raise ValueError("起点となる地点を選択してください。")
            ids = [int(value)]
        results = []
        for feature_id in ids:
            point, fid, layer_name = self._get_point(layer, feature_id, network_layer)
            feature = layer.getFeature(fid)
            label = _point_label(
                feature, self.origin_name_field_combo.currentData() or None
            )
            results.append((point, fid, layer_name, label))
        return results

    def _planning_destinations(self, network_layer, analysis_mode):
        layer = self._layer(self.dest_layer_combo)
        if layer is None:
            raise ValueError("巡回先のポイントレイヤを選択してください。")
        if self.plan_selected_destinations_check.isChecked():
            ids = sorted(layer.selectedFeatureIds())
            if not ids:
                raise ValueError("巡回先レイヤ上で訪問先を選択してください。")
        else:
            ids = [int(feature.id()) for feature in layer.getFeatures()]
        if not ids:
            raise ValueError("巡回先レイヤにポイントがありません。")

        transform = QgsCoordinateTransform(
            layer.crs(), network_layer.crs(), QgsProject.instance()
        )
        people_field = self.dest_people_field_combo.currentData() or ""
        priority_field = self.dest_priority_field_combo.currentData() or ""
        service_field = self.dest_service_field_combo.currentData() or ""
        name_field = self.dest_name_field_combo.currentData() or ""
        if analysis_mode == "team_coverage" and not people_field:
            raise ValueError("対応人数を最大化するには、対応対象人数の数値カラムを選択してください。")
        if (analysis_mode == "team_coverage"
                and self.plan_reward_combo.currentData() == "weighted"
                and not priority_field):
            raise ValueError("優先度を加味するには、優先度の数値カラムを選択してください。")
        fixed_service = float(self.plan_service_minutes.value())
        per_person_service = float(self.plan_per_person_minutes.value())
        team_size = int(self.plan_team_size.value())
        weighted = self.plan_reward_combo.currentData() == "weighted"
        results = []

        def numeric(feature, field_name, default, description):
            if not field_name:
                return default
            raw = feature.attribute(field_name)
            if raw in (None, ""):
                return default
            try:
                value = float(raw)
            except (TypeError, ValueError):
                raise ValueError(
                    "巡回先「{}」の{}カラム「{}」が数値ではありません。"
                    .format(_point_label(feature, name_field or None), description, field_name)
                )
            if not math.isfinite(value):
                raise ValueError("{}カラムに有限の数値以外があります。".format(description))
            return value

        for feature_id in ids:
            feature = layer.getFeature(feature_id)
            if not feature.isValid() or feature.geometry().isEmpty():
                raise ValueError("巡回先に無効なポイント形状があります（ID {}）。".format(feature_id))
            geometry = QgsGeometry(feature.geometry())
            if geometry.isMultipart():
                raise ValueError("巡回先には複数地点形状を使えません。各地点を別地物にしてください。")
            geometry.transform(transform)
            point = geometry.asPoint()
            people = numeric(feature, people_field, 1.0, "対応人数")
            priority = numeric(feature, priority_field, 1.0, "優先度")
            service = numeric(feature, service_field, fixed_service, "対応時間")
            if people < 0 or priority < 0 or service < 0:
                raise ValueError("対応人数、優先度、対応時間は0以上にしてください。")
            service += people * per_person_service / team_size
            results.append({
                "point": QgsPointXY(point.x(), point.y()),
                "record_id": int(feature.id()),
                "layer": layer.name(),
                "label": _point_label(feature, name_field or None),
                "people": people,
                "priority": priority,
                "service_minutes": service,
                "base_service_component": (
                    service - fixed_service if not service_field else None
                ),
                "reward": people * (priority if weighted else 1.0),
                "source_feature": feature,
            })
        return results

    @staticmethod
    def _network_distance_row(source_node, target_nodes, adjacency, progress_callback=None):
        """Dijkstra search stopped after all candidate visit nodes are reached."""
        remaining = set(target_nodes)
        remaining.discard(source_node)
        distances = {source_node: 0.0}
        queue = [(0.0, source_node)]
        visited = 0
        while queue and remaining:
            distance, node = heapq.heappop(queue)
            if distance != distances.get(node):
                continue
            if node in remaining:
                remaining.remove(node)
                if not remaining:
                    break
            visited += 1
            if progress_callback and visited % 500000 == 0:
                progress_callback("訪問先間の道路距離探索：{}地点を確認".format(visited))
            for neighbor, length_m in adjacency[node]:
                candidate = distance + length_m
                if candidate < distances.get(neighbor, float("inf")):
                    distances[neighbor] = candidate
                    heapq.heappush(queue, (candidate, neighbor))
        return distances

    @staticmethod
    def _network_path(source_node, target_node, nodes, adjacency, progress_callback=None):
        """Return one shortest path as graph node ids and its road length."""
        if source_node == target_node:
            return [source_node], 0.0
        distances = {source_node: 0.0}
        previous = {}
        queue = [(0.0, source_node)]
        visited = 0
        while queue:
            distance, node = heapq.heappop(queue)
            if distance != distances.get(node):
                continue
            if node == target_node:
                break
            visited += 1
            if progress_callback and visited % 500000 == 0:
                progress_callback("経路形状を復元中：{}地点を確認".format(visited))
            for neighbor, length_m in adjacency[node]:
                candidate = distance + length_m
                if candidate < distances.get(neighbor, float("inf")):
                    distances[neighbor] = candidate
                    previous[neighbor] = node
                    heapq.heappush(queue, (candidate, neighbor))
        if target_node not in distances:
            raise ValueError("道路ネットワーク上で訪問先間の経路が見つかりません。")
        path = [target_node]
        while path[-1] != source_node:
            path.append(previous[path[-1]])
        path.reverse()
        return path, distances[target_node]

    def _execute_team_plan(
        self, network, base, destinations, snap_limit, preset,
        gpkg_path, csv_path, summary_path, summary_xlsx_path, layer_name, analysis_mode,
    ):
        team_count = int(self.plan_team_count.value())
        team_size = int(self.plan_team_size.value())
        shift_minutes = float(self.plan_shift_hours.value()) * 60.0
        requested_team_count = team_count
        requested_shift_minutes = shift_minutes
        requested_service_minutes = float(self.plan_service_minutes.value())
        break_minutes = float(self.plan_break_minutes.value())
        return_to_base = self.plan_return_to_base.isChecked()
        stop_count = len(destinations)
        network_feature_count = network.featureCount()
        if stop_count > 50 or network_feature_count > 100000:
            warning_reasons = []
            if stop_count > 50:
                warning_reasons.append("訪問先が{}件".format(stop_count))
            if network_feature_count > 100000:
                warning_reasons.append("道路レイヤが{}地物".format(network_feature_count))
            answer = QMessageBox.question(
                self, "訪問先数の確認",
                "{}のため、道路全体のグラフ構築と訪問先間の最短経路計算を行います。"
                "道路網や訪問先が大きい場合は、処理に時間がかかり、メモリを多く使うことがあります。"
                "選択した訪問先だけで先に試すことをおすすめします。続けますか？"
                .format("、".join(warning_reasons)),
                MESSAGE_YES | MESSAGE_NO, MESSAGE_NO,
            )
            if answer != MESSAGE_YES:
                self._log("訪問先数の確認でキャンセルされました。")
                return

        speed_m_per_minute = preset["kmh"] * 1000.0 / 60.0
        if speed_m_per_minute <= 0:
            raise ValueError("巡回計画には0より大きい移動速度が必要です。")
        self._log(
            "巡回計画条件：{}チーム、1チーム{}人、行動可能{}分、休憩{}分、訪問先{}件。"
            .format(team_count, team_size, shift_minutes, break_minutes, stop_count)
        )
        self._log("道路上の距離を比較するため、選択した道路ネットワーク全域を読み込みます。")
        nodes, adjacency, spatial_index, index_id_to_node = self._build_graph(
            network, self._log
        )
        locations = [base] + destinations
        graph_nodes = []
        snap_distances = []
        for index, location in enumerate(locations):
            graph_node, snap_distance = self._nearest_node(
                location["point"] if isinstance(location, dict) else location[0],
                nodes, spatial_index, index_id_to_node,
            )
            if snap_distance > snap_limit:
                label = "拠点" if index == 0 else location["label"]
                raise ValueError(
                    "「{}」を道路に接続できません。道路まで{:.1f} m（許容距離{:.1f} m）。"
                    .format(label, snap_distance, snap_limit)
                )
            graph_nodes.append(graph_node)
            snap_distances.append(snap_distance)
        del spatial_index, index_id_to_node
        self._log("拠点と訪問先{}件を道路グラフに接続しました。".format(stop_count))

        target_nodes = set(graph_nodes)
        distance_matrix_m = [[float("inf")] * (stop_count + 1) for _ in range(stop_count + 1)]
        for source_index, source_node in enumerate(graph_nodes):
            row = self._network_distance_row(
                source_node, target_nodes, adjacency, self._log
            )
            for target_index, target_node in enumerate(graph_nodes):
                road_distance = row.get(target_node, float("inf"))
                if source_index == target_index:
                    road_distance = 0.0
                if math.isfinite(road_distance):
                    distance_matrix_m[source_index][target_index] = (
                        road_distance + snap_distances[source_index] + snap_distances[target_index]
                        if source_index != target_index else 0.0
                    )
            if (source_index + 1) % max(1, stop_count // 40) == 0 or source_index == stop_count:
                self._log(
                    "訪問先間の道路移動時間を計算中：{} / {}地点"
                    .format(source_index + 1, stop_count + 1)
                )
        time_matrix = [
            [distance / speed_m_per_minute for distance in row]
            for row in distance_matrix_m
        ]
        service_minutes = [item["service_minutes"] for item in destinations]
        rewards = [item["reward"] for item in destinations]
        plan_mode = "all" if analysis_mode == "team_all" else "coverage"
        self._log(
            "巡回順を作成中：{}。全体最適を保証しない試作ヒューリスティックを使います。"
            .format("全訪問先を割当" if plan_mode == "all" else "対応価値を最大化")
        )
        routes, unassigned, route_work_minutes = plan_routes(
            time_matrix, service_minutes, rewards, team_count,
            shift_minutes, break_minutes, return_to_base, plan_mode,
        )

        adjustment_summary = "自動調整なし"
        if plan_mode == "all" and unassigned:
            action = self._choose_unvisited_action(len(unassigned), stop_count)
            if action == "cancel":
                self._log("未訪問先の確認でキャンセルされました。")
                return
            if action == "auto":
                service_adjustable = not bool(self.dest_service_field_combo.currentData())
                adjustment = self._configure_auto_adjustment(
                    team_count, shift_minutes, service_adjustable
                )
                if adjustment is None:
                    self._log("自動調整の設定をキャンセルしました。")
                    return
                adjusted = self._auto_adjust_plan(
                    time_matrix, destinations, rewards, team_count, shift_minutes,
                    break_minutes, return_to_base, adjustment, service_adjustable,
                )
                routes, unassigned, route_work_minutes = adjusted["routes"]
                team_count = adjusted["team_count"]
                shift_minutes = adjusted["shift_minutes"]
                service_minutes = adjusted["service_minutes"]
                for destination, service in zip(destinations, service_minutes):
                    destination["service_minutes"] = service
                adjustment_summary = adjusted["summary"]
                self._log("自動調整結果：{}".format(adjustment_summary))
                if unassigned:
                    answer = QMessageBox.question(
                        self, "未訪問先が残っています",
                        "指定された調整範囲の中では全訪問先を割り当てられませんでした。\n"
                        "現在の調整結果（訪問{}件、未訪問{}件）を出力しますか？\n\n{}"
                        .format(stop_count - len(unassigned), len(unassigned), adjustment_summary),
                        MESSAGE_YES | MESSAGE_NO, MESSAGE_NO,
                    )
                    if answer != MESSAGE_YES:
                        self._log("調整結果の出力をキャンセルしました。")
                        return
                self.plan_team_count.setValue(team_count)
                self.plan_shift_hours.setValue(shift_minutes / 60.0)
                if service_adjustable:
                    self.plan_service_minutes.setValue(adjusted["common_service_minutes"])
            else:
                self._log("未訪問先がある状態で、現在の設定のまま出力します。")

        assigned = {}
        for team_index, route in enumerate(routes):
            for sequence, stop_index in enumerate(route, 1):
                assigned[stop_index - 1] = (team_index + 1, sequence)

        line_rows = []
        line_geometries = []
        detail_rows = []
        stop_geometries = []
        team_summaries = []
        total_people = sum(item["people"] for item in destinations)
        measure_basis = (
            self.dest_people_field_combo.currentData()
            or "人数カラム未指定：訪問先1件を1単位として集計"
        )
        kmh = preset["kmh"]
        for team_index, route in enumerate(routes):
            if not route:
                team_summaries.append({
                    "team_id": team_index + 1, "team_size": team_size,
                    "stop_count": 0, "people": 0.0, "priority_weighted_people": 0.0,
                    "visit_rate_percent": 0.0, "people_coverage_percent": 0.0,
                    "measure_basis": measure_basis,
                    "distance_m": 0.0, "travel_min": 0.0, "service_min": 0.0,
                    "break_min": 0.0, "work_min": 0.0,
                    "within_shift": True, "visit_order": "",
                    "requested_team_count": requested_team_count,
                    "requested_shift_min": requested_shift_minutes,
                    "requested_service_min": requested_service_minutes,
                    "final_team_count": team_count,
                    "final_shift_min": shift_minutes,
                    "final_service_min": float(self.plan_service_minutes.value()),
                    "adjustment_summary": adjustment_summary,
                })
                continue
            ordered_indices = [0] + route + ([0] if return_to_base else [])
            route_coords = []
            for leg_number, (from_index, to_index) in enumerate(
                zip(ordered_indices[:-1], ordered_indices[1:]), 1
            ):
                path, _road_distance = self._network_path(
                    graph_nodes[from_index], graph_nodes[to_index],
                    nodes, adjacency, self._log,
                )
                from_point = locations[from_index]["point"] if from_index else base[0]
                to_point = locations[to_index]["point"] if to_index else base[0]
                leg_coords = [QgsPointXY(from_point)]
                leg_coords.extend(QgsPointXY(nodes[node_id]) for node_id in path)
                leg_coords.append(QgsPointXY(to_point))
                if route_coords and leg_coords:
                    leg_coords = leg_coords[1:]
                route_coords.extend(leg_coords)
                if leg_number % 20 == 0:
                    self._log("道路経路の形状を作成中：チーム{}、{}区間".format(team_index + 1, leg_number))

            distance_m = sum(
                distance_matrix_m[a][b]
                for a, b in zip(ordered_indices[:-1], ordered_indices[1:])
            )
            travel_min = distance_m / speed_m_per_minute
            service_total = sum(service_minutes[index - 1] for index in route)
            used_break = break_minutes if route else 0.0
            work_min = travel_min + service_total + used_break
            team_people = sum(destinations[index - 1]["people"] for index in route)
            team_weighted = sum(destinations[index - 1]["reward"] for index in route)
            line_rows.append({
                "team_id": "チーム{}".format(team_index + 1),
                "origin_location": "チーム{}".format(team_index + 1),
                "team_size": team_size, "stop_count": len(route), "people": team_people,
                "visit_rate_percent": len(route) / stop_count * 100.0 if stop_count else 0.0,
                "people_coverage_percent": team_people / total_people * 100.0 if total_people else 0.0,
                "measure_basis": measure_basis,
                "priority_weighted_people": team_weighted,
                "distance_m": distance_m, "estimated_time_min": work_min,
                "travel_min": travel_min, "service_min": service_total,
                "break_min": used_break, "work_min": work_min,
                "shift_limit_min": shift_minutes,
                "requested_team_count": requested_team_count,
                "requested_shift_min": requested_shift_minutes,
                "requested_service_min": requested_service_minutes,
                "final_team_count": team_count,
                "final_shift_min": shift_minutes,
                "final_service_min": float(self.plan_service_minutes.value()),
                "adjustment_summary": adjustment_summary,
                "within_shift": work_min <= shift_minutes + 1e-7,
                "visit_order": " → ".join(destinations[index - 1]["label"] for index in route),
                "speed_profile": preset["label"], "speed_kmh": kmh,
                "network_layer": network.name(), "network_crs": network.crs().authid(),
            })
            line_geometries.append(QgsGeometry.fromPolylineXY(route_coords))
            team_summaries.append({
                "team_id": team_index + 1, "team_size": team_size,
                "stop_count": len(route), "people": team_people,
                "visit_rate_percent": len(route) / stop_count * 100.0 if stop_count else 0.0,
                "people_coverage_percent": team_people / total_people * 100.0 if total_people else 0.0,
                "measure_basis": measure_basis,
                "priority_weighted_people": team_weighted,
                "distance_m": distance_m, "travel_min": travel_min,
                "service_min": service_total, "break_min": used_break,
                "work_min": work_min, "within_shift": work_min <= shift_minutes + 1e-7,
                "requested_team_count": requested_team_count,
                "requested_shift_min": requested_shift_minutes,
                "requested_service_min": requested_service_minutes,
                "final_team_count": team_count,
                "final_shift_min": shift_minutes,
                "final_service_min": float(self.plan_service_minutes.value()),
                "adjustment_summary": adjustment_summary,
                "visit_order": " → ".join(destinations[index - 1]["label"] for index in route),
            })

            active_total = travel_min + service_total
            break_threshold = active_total / 2.0
            elapsed = 0.0
            active_elapsed = 0.0
            break_added = False
            previous = 0
            for sequence, stop_index in enumerate(route, 1):
                leg_time = time_matrix[previous][stop_index]
                active_elapsed += leg_time
                elapsed += leg_time
                if used_break and not break_added and active_elapsed >= break_threshold:
                    elapsed += used_break
                    break_added = True
                arrival = elapsed
                service = service_minutes[stop_index - 1]
                service_end = arrival + service
                item = destinations[stop_index - 1]
                row = {
                    "status": "訪問予定", "team_id": "チーム{}".format(team_index + 1),
                    "visit_order": sequence, "origin_location": item["label"],
                    "origin_record_id": item["record_id"], "people": item["people"],
                    "priority": item["priority"], "reward": item["reward"],
                    "measure_basis": measure_basis,
                    "service_min": service, "travel_from_previous_min": leg_time,
                    "requested_team_count": requested_team_count,
                    "requested_shift_min": requested_shift_minutes,
                    "requested_service_min": requested_service_minutes,
                    "final_team_count": team_count,
                    "final_shift_min": shift_minutes,
                    "final_service_min": float(self.plan_service_minutes.value()),
                    "adjustment_summary": adjustment_summary,
                    "arrival_min_from_start": arrival,
                    "service_end_min_from_start": service_end,
                    "speed_profile": preset["label"], "speed_kmh": kmh,
                    "network_layer": network.name(), "reason": "",
                }
                detail_rows.append(row)
                stop_geometries.append(QgsGeometry.fromPointXY(item["point"]))
                elapsed = service_end
                active_elapsed += service
                previous = stop_index
            if used_break and not break_added:
                elapsed += used_break
            if return_to_base:
                elapsed += time_matrix[previous][0]

        unassigned_set = {index - 1 for index in unassigned}
        for index, item in enumerate(destinations):
            if index in assigned:
                continue
            reason = (
                "行動時間内に割り当てられなかった（試作法のため最適性・実行不可能性の証明なし）"
                if plan_mode == "all" else
                "行動時間内の訪問先候補から未選択（優先度と所要時間による近似選択）"
            )
            detail_rows.append({
                "status": "未訪問", "team_id": "", "visit_order": "",
                "origin_location": item["label"], "origin_record_id": item["record_id"],
                "people": item["people"], "priority": item["priority"],
                "reward": item["reward"], "service_min": item["service_minutes"],
                "requested_team_count": requested_team_count,
                "requested_shift_min": requested_shift_minutes,
                "requested_service_min": requested_service_minutes,
                "final_team_count": team_count,
                "final_shift_min": shift_minutes,
                "final_service_min": float(self.plan_service_minutes.value()),
                "adjustment_summary": adjustment_summary,
                "measure_basis": measure_basis,
                "travel_from_previous_min": "", "arrival_min_from_start": "",
                "service_end_min_from_start": "", "speed_profile": preset["label"],
                "speed_kmh": kmh, "network_layer": network.name(),
                "reason": reason,
            })
            stop_geometries.append(QgsGeometry.fromPointXY(item["point"]))

        if not detail_rows:
            raise ValueError("訪問先の出力対象がありません。")
        self._write_team_plan_files(
            network, line_rows, line_geometries, detail_rows, stop_geometries,
            team_summaries, gpkg_path, csv_path, summary_path, layer_name,
        )
        run_info = {
            "分析種類": "全訪問先を巡回" if plan_mode == "all" else "時間内で対応人数・優先度を最大化",
            "解析日時": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "出発拠点": base[3],
            "道路ネットワーク": network.name(),
            "座標系": network.crs().authid(),
            "移動速度": preset["label"],
            "訪問候補数": stop_count,
            "設定チーム数": team_count,
            "設定チーム数（調整前）": requested_team_count,
            "設定チーム数（調整後）": team_count,
            "1チームあたりの人数": team_size,
            "行動可能時間": round(shift_minutes, 1),
            "行動可能時間（調整前）": round(requested_shift_minutes, 1),
            "行動可能時間（調整後）": round(shift_minutes, 1),
            "休憩時間": break_minutes,
            "共通対応時間（調整前）": requested_service_minutes,
            "共通対応時間（調整後）": self.plan_service_minutes.value(),
            "集計単位": measure_basis,
            "調整内容": adjustment_summary,
            "出力レイヤ名": layer_name,
            "帰着条件": "拠点に戻る" if return_to_base else "拠点に戻らない",
            "スナップ許容距離": snap_limit,
            "訪問先レイヤ": self.dest_layer_combo.currentText(),
        }
        write_patrol_summary(
            summary_xlsx_path, run_info, team_summaries, detail_rows,
            language=self.language,
        )
        self._log(self._text("日本語サマリーExcelを書き出しました：{}").format(summary_xlsx_path))
        covered_people = sum(
            item["people"] for index, item in enumerate(destinations) if index in assigned
        )
        people_unit = "人" if self.dest_people_field_combo.currentData() else "対応単位"
        self._log(
            "巡回計画を保存しました：訪問{} / {}件、対応量{} / {}{}、未訪問{}件。"
            .format(len(assigned), stop_count, covered_people, total_people, people_unit, len(unassigned_set))
        )
        self._log(
            "Added team routes and destinations to GeoPackage, visit order and team summaries to CSV, and the summary workbook."
            if self.language == "en" else
            "GeoPackageにチーム経路・訪問先、CSVに訪問順とチーム別集計、Excelに日本語サマリーを追加しました。"
        )
        QMessageBox.information(
            self, self._text("巡回計画の作成完了"),
            self._text(
                "訪問予定：{} / {}件\n未訪問：{}件\n対応量：{} / {}{}\nCSV：{}\nサマリーCSV：{}\nサマリーExcel：{}\nGeoPackage：{}\n\n"
                "これは道路距離に基づく試作ヒューリスティックの結果です。全体最適は保証されません。"
            ).format(len(assigned), stop_count, len(unassigned_set), covered_people,
                     total_people, people_unit, csv_path, summary_path, summary_xlsx_path, gpkg_path)
        )

    def _choose_unvisited_action(self, unvisited_count, destination_count):
        box = QMessageBox(self)
        box.setWindowTitle(self._text("未訪問先があります"))
        try:
            warning_icon = QMessageBox.Icon.Warning
        except AttributeError:
            warning_icon = QMessageBox.Warning
        box.setIcon(warning_icon)
        box.setText(self._text(
            "全訪問先巡回の計算で、未訪問先が{}件残りました（全{}件）。\n"
            "このまま結果を出力するか、設定を自動調整しますか？"
        ).format(unvisited_count, destination_count))
        try:
            accept_role = QMessageBox.ButtonRole.AcceptRole
            action_role = QMessageBox.ButtonRole.ActionRole
            reject_role = QMessageBox.ButtonRole.RejectRole
        except AttributeError:
            accept_role = QMessageBox.AcceptRole
            action_role = QMessageBox.ActionRole
            reject_role = QMessageBox.RejectRole
        save_button = box.addButton(self._text("現在の設定で出力"), accept_role)
        adjust_button = box.addButton(self._text("設定を自動調整して全訪問先を回る"), action_role)
        box.addButton(self._text("キャンセル"), reject_role)
        try:
            box.exec()
        except AttributeError:
            box.exec_()
        if box.clickedButton() is save_button:
            return "save"
        if box.clickedButton() is adjust_button:
            return "auto"
        return "cancel"

    def _configure_auto_adjustment(self, team_count, shift_minutes, service_adjustable):
        dialog = QDialog(self)
        dialog.setWindowTitle(self._text("自動調整する条件"))
        dialog.setMinimumWidth(560)
        layout = QVBoxLayout(dialog)
        intro = QLabel(
            "1チームあたりの人数は固定し、選んだ項目を優先順に調整します。"
            "上限・下限に達したら次の項目へ進みます。"
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()

        team_enabled = QCheckBox("調整する")
        team_enabled.setChecked(True)
        team_priority = QSpinBox()
        team_priority.setRange(1, 3)
        team_priority.setValue(1)
        team_cap = QSpinBox()
        team_cap.setRange(team_count, 100)
        team_cap.setValue(min(100, max(team_count, team_count + 2)))
        team_row = QHBoxLayout()
        team_row.addWidget(team_enabled)
        team_row.addWidget(QLabel("優先順位"))
        team_row.addWidget(team_priority)
        team_row.addWidget(QLabel("チーム数の上限"))
        team_row.addWidget(team_cap)
        form.addRow("チーム数", team_row)

        shift_enabled = QCheckBox("調整する")
        shift_enabled.setChecked(True)
        shift_priority = QSpinBox()
        shift_priority.setRange(1, 3)
        shift_priority.setValue(2)
        shift_cap = QDoubleSpinBox()
        shift_cap.setRange(shift_minutes / 60.0, 24.0)
        shift_cap.setDecimals(2)
        shift_cap.setSingleStep(0.25)
        shift_cap.setValue(min(24.0, max(shift_minutes / 60.0, shift_minutes / 60.0 + 1.0)))
        shift_row = QHBoxLayout()
        shift_row.addWidget(shift_enabled)
        shift_row.addWidget(QLabel("優先順位"))
        shift_row.addWidget(shift_priority)
        shift_row.addWidget(QLabel("行動可能時間の上限（時間）"))
        shift_row.addWidget(shift_cap)
        form.addRow("行動可能時間", shift_row)

        service_enabled = QCheckBox("調整する")
        service_enabled.setChecked(service_adjustable)
        service_enabled.setEnabled(service_adjustable)
        service_priority = QSpinBox()
        service_priority.setRange(1, 3)
        service_priority.setValue(3)
        service_priority.setEnabled(service_adjustable)
        service_floor = QDoubleSpinBox()
        current_service = float(self.plan_service_minutes.value())
        service_floor.setRange(0.0, current_service)
        service_floor.setDecimals(1)
        service_floor.setSingleStep(1.0)
        service_floor.setValue(min(5.0, current_service))
        service_floor.setEnabled(service_adjustable)
        service_row = QHBoxLayout()
        service_row.addWidget(service_enabled)
        service_row.addWidget(QLabel("優先順位"))
        service_row.addWidget(service_priority)
        service_row.addWidget(QLabel("共通対応時間の下限（分）"))
        service_row.addWidget(service_floor)
        form.addRow("全訪問先共通の対応時間", service_row)
        if not service_adjustable:
            note = QLabel("対応時間カラムが選択されているため、この項目は調整できません。")
            note.setWordWrap(True)
            layout.addWidget(note)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        run_button = QPushButton("この条件で調整")
        cancel_button = QPushButton("キャンセル")
        buttons.addWidget(run_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        if self.language == "en":
            self._apply_language(dialog)
        run_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        try:
            accepted = dialog.exec()
        except AttributeError:
            accepted = dialog.exec_()
        try:
            accepted_value = QDialog.DialogCode.Accepted
        except AttributeError:
            accepted_value = QDialog.Accepted
        if accepted != accepted_value:
            return None
        enabled = []
        if team_enabled.isChecked():
            enabled.append((team_priority.value(), "teams"))
        if shift_enabled.isChecked():
            enabled.append((shift_priority.value(), "shift"))
        if service_enabled.isChecked():
            enabled.append((service_priority.value(), "service"))
        if not enabled:
            QMessageBox.warning(self, "調整項目がありません", "少なくとも1つの項目を選んでください。")
            return None
        priorities = [item[0] for item in enabled]
        if len(set(priorities)) != len(priorities):
            QMessageBox.warning(self, "優先順位を確認してください", "調整する項目の優先順位は重複できません。")
            return None
        enabled.sort()
        return {
            "order": [item[1] for item in enabled],
            "team_cap": team_cap.value(),
            "shift_cap_minutes": shift_cap.value() * 60.0,
            "service_floor": service_floor.value(),
        }

    def _auto_adjust_plan(
        self, time_matrix, destinations, rewards, team_count, shift_minutes,
        break_minutes, return_to_base, settings, service_adjustable,
    ):
        common_service = float(self.plan_service_minutes.value())
        initial_common_service = common_service
        initial_team_count = team_count
        initial_shift = shift_minutes
        base_components = [item["base_service_component"] for item in destinations]
        initial_services = [item["service_minutes"] for item in destinations]
        best = None
        trial_number = 0

        def evaluate(candidate_teams, candidate_shift, candidate_service):
            nonlocal trial_number
            trial_number += 1
            self._log(
                "自動調整の試行{}：{}チーム、行動{}分、共通対応{}分。"
                .format(trial_number, candidate_teams, candidate_shift, candidate_service)
            )
            services = (
                [component + candidate_service for component in base_components]
                if service_adjustable else list(initial_services)
            )
            planned = plan_routes(
                time_matrix, services, rewards, candidate_teams, candidate_shift,
                break_minutes, return_to_base, "all",
            )
            return {
                "routes": planned,
                "team_count": candidate_teams,
                "shift_minutes": candidate_shift,
                "service_minutes": services,
                "common_service_minutes": candidate_service,
            }

        def remember(result):
            nonlocal best
            count = len(result["routes"][1])
            best_count = len(best["routes"][1]) if best is not None else float("inf")
            if count < best_count:
                best = result

        current = evaluate(team_count, shift_minutes, common_service)
        remember(current)
        for parameter in settings["order"]:
            if not current["routes"][1]:
                break
            if parameter == "teams":
                low, high = team_count, int(settings["team_cap"])
                cap_result = evaluate(high, shift_minutes, common_service)
                remember(cap_result)
                if cap_result["routes"][1]:
                    team_count = high
                    current = cap_result
                    continue
                while low < high:
                    mid = (low + high) // 2
                    candidate = evaluate(mid, shift_minutes, common_service)
                    remember(candidate)
                    if candidate["routes"][1]:
                        low = mid + 1
                    else:
                        high = mid
                team_count = low
                current = evaluate(team_count, shift_minutes, common_service)
                remember(current)
            elif parameter == "shift":
                low = int(math.ceil(shift_minutes / 15.0))
                high = int(math.floor(settings["shift_cap_minutes"] / 15.0))
                if high < low:
                    continue
                cap_result = evaluate(team_count, high * 15.0, common_service)
                remember(cap_result)
                if cap_result["routes"][1]:
                    shift_minutes = high * 15.0
                    current = cap_result
                    continue
                while low < high:
                    mid = (low + high) // 2
                    candidate = evaluate(team_count, mid * 15.0, common_service)
                    remember(candidate)
                    if candidate["routes"][1]:
                        low = mid + 1
                    else:
                        high = mid
                shift_minutes = low * 15.0
                current = evaluate(team_count, shift_minutes, common_service)
                remember(current)
            elif parameter == "service" and service_adjustable:
                low = int(math.ceil(settings["service_floor"] * 10.0))
                high = int(math.floor(common_service * 10.0))
                cap_result = evaluate(team_count, shift_minutes, low / 10.0)
                remember(cap_result)
                if cap_result["routes"][1]:
                    # The lower bound still cannot cover all destinations.
                    common_service = low / 10.0
                    current = cap_result
                    continue
                while low < high:
                    mid = (low + high + 1) // 2
                    candidate = evaluate(team_count, shift_minutes, mid / 10.0)
                    remember(candidate)
                    if candidate["routes"][1]:
                        high = mid - 1
                    else:
                        low = mid
                common_service = low / 10.0
                current = evaluate(team_count, shift_minutes, common_service)
                remember(current)

        final = current if not current["routes"][1] else best
        if final is None:
            final = current
        if final["routes"][1]:
            summary = (
                "指定範囲の上限・下限まで調整しても未訪問先{}件が残りました。"
                .format(len(final["routes"][1]))
            )
        else:
            changes = []
            if final["team_count"] != initial_team_count:
                changes.append("チーム数 {}→{}".format(initial_team_count, final["team_count"]))
            if abs(final["shift_minutes"] - initial_shift) > 1e-8:
                changes.append("行動可能時間 {:.0f}→{:.0f}分".format(initial_shift, final["shift_minutes"]))
            if service_adjustable and abs(final["common_service_minutes"] - initial_common_service) > 1e-8:
                changes.append("共通対応時間を{:.1f}分に設定".format(final["common_service_minutes"]))
            summary = "全訪問先を割り当てました。" + (" 調整：" + "、".join(changes) if changes else "設定変更なし。")
        summary += " 試作ヒューリスティックのため、最適性や実行不可能性は証明しません。"
        final["summary"] = summary
        return final

    def _write_team_plan_files(
        self, network, line_rows, line_geometries, detail_rows, stop_geometries,
        team_summaries, gpkg_path, csv_path, summary_path, layer_name,
    ):
        if OUTPUT_LANGUAGE == "en":
            line_rows = [_localized_row(row) for row in line_rows]
            detail_rows = [_localized_row(row) for row in detail_rows]
            team_summaries = [_localized_row(row) for row in team_summaries]
        self._write_csv(csv_path, detail_rows)
        self._write_csv(summary_path, team_summaries)
        line_name = self._suffixed_layer_name(layer_name, "_チーム経路")
        stop_name = self._suffixed_layer_name(layer_name, "_訪問先")

        def write_layer(rows, geometries, geometry_type, output_name, action):
            uri = "{}?crs={}".format(geometry_type, network.crs().authid())
            memory = QgsVectorLayer(uri, output_name, "memory")
            if not memory.isValid():
                raise ValueError("巡回計画の出力レイヤを作成できませんでした。")
            column_names = list(rows[0].keys()) if rows else []
            fields = []
            for name in column_names:
                value = next((row.get(name) for row in rows if row.get(name) not in (None, "")), "")
                kind = FIELD_DOUBLE if isinstance(value, (int, float)) else FIELD_STRING
                fields.append(QgsField(name[:60], kind))
            provider = memory.dataProvider()
            provider.addAttributes(fields)
            memory.updateFields()
            features = []
            for row, geometry in zip(rows, geometries):
                feature = QgsFeature(memory.fields())
                feature.setGeometry(geometry)
                feature.setAttributes([
                    None if row.get(name) in (None, "") else row.get(name)
                    for name in column_names
                ])
                features.append(feature)
            add_result = provider.addFeatures(features)
            add_ok = add_result[0] if isinstance(add_result, tuple) else bool(add_result)
            if not add_ok or memory.featureCount() != len(features):
                raise ValueError(
                    "巡回先レイヤの地物追加に失敗しました（予定・未訪問を含む{}件中{}件）。"
                    .format(len(features), memory.featureCount())
                )
            memory.updateExtents()
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = output_name
            options.fileEncoding = "UTF-8"
            options.actionOnExistingFile = action
            result = QgsVectorFileWriter.writeAsVectorFormatV3(
                memory, str(gpkg_path), QgsProject.instance().transformContext(), options
            )
            if result[0] != QgsVectorFileWriter.NoError:
                raise ValueError("巡回計画レイヤを書き込めませんでした：{}".format(result[1]))
            saved = QgsVectorLayer(
                "{}|layername={}".format(gpkg_path, output_name), output_name, "ogr"
            )
            if not saved.isValid():
                raise ValueError("保存した巡回計画レイヤを読み込めませんでした：{}".format(output_name))
            QgsProject.instance().addMapLayer(saved)
            return saved

        if line_rows:
            saved_lines = write_layer(
                line_rows, line_geometries, "LineString", line_name,
                QgsVectorFileWriter.CreateOrOverwriteFile,
            )
            self._apply_origin_catchment_style(saved_lines)
        else:
            self._log("訪問可能なチーム経路がないため、経路ラインは作成しませんでした。")
        saved_stops = write_layer(
            detail_rows, stop_geometries, "Point", stop_name,
            (QgsVectorFileWriter.CreateOrOverwriteLayer if line_rows
             else QgsVectorFileWriter.CreateOrOverwriteFile),
        )

    def _build_graph(
        self, network_layer, progress_callback=None, merge_tolerance=0.1,
        search_rect=None,
    ):
        node_ids = {}
        node_xy = []
        adjacency = []
        edge_count = 0

        def node_id(point):
            key = (int(round(point.x() / merge_tolerance)), int(round(point.y() / merge_tolerance)))
            if key not in node_ids:
                idx = len(node_xy)
                node_ids[key] = idx
                node_xy.append(QgsPointXY(point))
                adjacency.append([])
            return node_ids[key]

        total_features = network_layer.featureCount()
        request = QgsFeatureRequest()
        clip_geometry = None
        if search_rect is not None:
            request.setFilterRect(search_rect)
            clip_geometry = QgsGeometry.fromRect(search_rect)
            if progress_callback:
                try:
                    index_status = network_layer.dataProvider().hasSpatialIndex()
                    index_present = index_status == network_layer.dataProvider().SpatialIndexPresent
                    index_note = "あり" if index_present else "なし／不明"
                except (AttributeError, RuntimeError):
                    index_note = "確認できず"
                progress_callback(
                    "周辺範囲だけを検索（レイヤ全体{}件、空間索引{}）".format(
                        total_features, index_note
                    )
                )
        selected_feature_count = 0
        for feature in network_layer.getFeatures(request):
            selected_feature_count += 1
            if progress_callback and selected_feature_count % 5000 == 0:
                progress_callback(
                    "対象範囲の道路を確認中：{}件（レイヤ全体{}件）".format(
                        selected_feature_count, total_features
                    )
                )
            geom = feature.geometry()
            if geom.isEmpty():
                continue
            if clip_geometry is not None:
                try:
                    geom = geom.intersection(clip_geometry)
                except Exception as exc:
                    raise ValueError(
                        "対象範囲内の道路形状を切り出せませんでした：{}".format(exc)
                    )
                if geom.isEmpty():
                    continue
            for part in _parts(geom):
                if len(part) < 2:
                    continue
                for a, b in zip(part[:-1], part[1:]):
                    u, v = node_id(a), node_id(b)
                    if u == v:
                        continue
                    length_m = math.hypot(b.x() - a.x(), b.y() - a.y())
                    # 隣接リストに距離を直接保持し、区間ごとの別配列を省いてメモリを節約。
                    adjacency[u].append((v, length_m))
                    adjacency[v].append((u, length_m))
                    edge_count += 1
        if not edge_count:
            raise ValueError(
                "指定した解析範囲に有効な道路ラインがありません。範囲、座標系、道路レイヤを確認してください。"
                if search_rect is not None else "道路ネットワークに有効なライン区間がありません。"
            )
        if progress_callback:
            progress_callback(
                "周辺道路グラフを構築：道路{}地物、{}地点、{}区間".format(
                    selected_feature_count, len(node_xy), edge_count
                )
            )

        # 最近傍ノード探索を全ノードの総当たりから空間索引に変更する。
        # 頂点の重複判定用辞書は索引構築時には不要なので、ピークメモリを抑えるため先に解放する。
        del node_ids
        spatial_index = QgsSpatialIndex()
        index_id_to_node = {}
        index_feature = QgsFeature()
        for idx, point in enumerate(node_xy):
            feature_id = idx + 1
            index_feature.setId(feature_id)
            index_feature.setGeometry(QgsGeometry.fromPointXY(point))
            spatial_index.addFeature(index_feature)
            index_id_to_node[feature_id] = idx
            if progress_callback and (idx + 1) % 100000 == 0:
                progress_callback(
                    "道路グラフのノード索引を作成中：{} / {}地点"
                    .format(idx + 1, len(node_xy))
                )
        return node_xy, adjacency, spatial_index, index_id_to_node

    @staticmethod
    def _nearest_node(point, nodes, spatial_index, index_id_to_node):
        nearest = spatial_index.nearestNeighbor(point, 1)
        if not nearest:
            raise ValueError("道路ネットワークから接続先を検索できませんでした。")
        node_id = index_id_to_node[int(nearest[0])]
        node = nodes[node_id]
        distance = math.hypot(point.x() - node.x(), point.y() - node.y())
        return node_id, distance

    @staticmethod
    def _dijkstra_to_targets(root, targets, adjacency, progress_callback=None):
        """一つの目的地から全起点への最短路木を一度だけ計算する。"""
        remaining = set(targets)
        costs = {root: 0.0}
        previous = {}
        queue = [(0.0, root)]
        visited_count = 0
        while queue:
            cost, node = heapq.heappop(queue)
            if cost != costs.get(node):
                continue
            remaining.discard(node)
            if not remaining:
                break
            visited_count += 1
            if progress_callback and visited_count % 20000 == 0:
                progress_callback("経路を探索中：{}地点を確認".format(visited_count))
            for neighbor, length_m in adjacency[node]:
                candidate = cost + length_m
                if candidate < costs.get(neighbor, float("inf")):
                    costs[neighbor] = candidate
                    previous[neighbor] = node
                    heapq.heappush(queue, (candidate, neighbor))
        unreachable = remaining.intersection(targets)
        if unreachable:
            raise ValueError("{}地点から目的地までの経路が見つかりません。道路ラインの接続を確認してください。".format(len(unreachable)))
        return costs, previous

    @staticmethod
    def _points_extent(points, margin):
        xs = [point.x() for point in points]
        ys = [point.y() for point in points]
        return QgsRectangle(
            min(xs) - margin, min(ys) - margin,
            max(xs) + margin, max(ys) + margin,
        )

    @staticmethod
    def _boundary_clearance(point, rect):
        """点から矩形の最も近い境界までの距離。矩形外経路の下限評価に使う。"""
        return max(0.0, min(
            point.x() - rect.xMinimum(), rect.xMaximum() - point.x(),
            point.y() - rect.yMinimum(), rect.yMaximum() - point.y(),
        ))

    @staticmethod
    def _contains_rect(outer, inner):
        return (
            outer.xMinimum() <= inner.xMinimum()
            and outer.yMinimum() <= inner.yMinimum()
            and outer.xMaximum() >= inner.xMaximum()
            and outer.yMaximum() >= inner.yMaximum()
        )

    def _preflight_snap_distances(self, network, points):
        """対象地点ごとに、道路ラインの全頂点までの厳密な最近接距離を調べる。

        道路形状は保持せず、地物の空間索引だけを一時的に作る。最初の最近傍
        地物の頂点距離を上限に、その範囲に交差する地物だけを精査する。
        """
        self._log(
            "道路接続を事前確認：対象{}地点（起点・目的地）".format(len(points))
        )
        index = QgsSpatialIndex()
        request = QgsFeatureRequest()
        request.setNoAttributes()
        feature_count = 0
        for feature_count, feature in enumerate(network.getFeatures(request), 1):
            if feature.hasGeometry() and not feature.geometry().isEmpty():
                index.addFeature(feature)
            if feature_count % 50000 == 0:
                self._log("道路の検索用索引を作成中：{}地物".format(feature_count))
        if feature_count == 0 or index is None:
            raise ValueError("道路レイヤに検索可能な地物がありません。")
        self._log("道路の検索用索引を作成：{}地物".format(feature_count))

        distance_cache = {}

        def feature_vertex_distance(feature, point):
            if not feature.isValid() or not feature.hasGeometry():
                return float("inf")
            geometry = feature.geometry()
            if geometry.isEmpty():
                return float("inf")
            return min(
                (math.hypot(point.x() - vertex.x(), point.y() - vertex.y())
                 for vertex in geometry.vertices()),
                default=float("inf"),
            )

        results = []
        for point, label, role in points:
            cache_key = (point.x(), point.y())
            if cache_key in distance_cache:
                distance = distance_cache[cache_key]
            else:
                nearest_ids = index.nearestNeighbor(point, 1)
                if not nearest_ids:
                    raise ValueError("道路頂点を検索できません。道路レイヤの形状を確認してください。")
                nearest_feature = network.getFeature(int(nearest_ids[0]))
                best_distance = feature_vertex_distance(nearest_feature, point)
                if not math.isfinite(best_distance):
                    raise ValueError("道路頂点までの距離を計算できません。道路レイヤの形状を確認してください。")

                # 頂点までbest_distanceより近い線は、その外接矩形がこの矩形と
                # 必ず交差する。候補だけを精査すれば全道路頂点に対する最近傍となる。
                radius = max(best_distance, 0.001) + 1e-6
                rect = QgsRectangle(
                    point.x() - radius, point.y() - radius,
                    point.x() + radius, point.y() + radius,
                )
                candidate_ids = set(index.intersects(rect))
                candidate_ids.add(int(nearest_ids[0]))
                candidate_request = QgsFeatureRequest()
                candidate_request.setNoAttributes()
                candidate_request.setFilterFids(list(candidate_ids))
                for candidate in network.getFeatures(candidate_request):
                    best_distance = min(
                        best_distance, feature_vertex_distance(candidate, point)
                    )
                distance = best_distance
                distance_cache[cache_key] = distance
            results.append((point, label, role, distance))

        return results

    def _confirm_snap_distance_if_needed(self, snap_distances, allowed_distance):
        """全対象点が接続できる最小許容距離を提示し、適用の可否を確認する。"""
        exceedances = sorted(
            (item for item in snap_distances if item[3] > allowed_distance),
            key=lambda item: item[3], reverse=True,
        )
        max_distance = max((item[3] for item in snap_distances), default=0.0)
        if not exceedances:
            self._log(
                "事前確認完了：全{}地点が現在の許容距離{:.0f} m以内です。"
                .format(len(snap_distances), allowed_distance)
            )
            return allowed_distance

        required_distance = max(1, int(math.ceil(max_distance)))
        self._log(
            "許容距離超過：{} / {}地点。全地点を接続する最小許容距離は{} mです。"
            .format(len(exceedances), len(snap_distances), required_distance)
        )
        details = [
            "{}「{}」：{:.1f} m".format(role, label, distance)
            for _point, label, role, distance in exceedances[:12]
        ]
        if len(exceedances) > 12:
            details.append("ほか{}地点".format(len(exceedances) - 12))
        prompt = (
            "現在の許容距離{:.0f} mを超える地点があります。\n\n{}\n\n"
            "全地点を接続する最小値は{} mです。この値に自動変更して解析を続けますか？\n"
            "許容距離を広げると、意図しない道路へ接続する可能性があります。"
        ).format(allowed_distance, "\n".join(details), required_distance)
        answer = QMessageBox.question(
            self, "道路への接続距離を確認", prompt,
            MESSAGE_YES | MESSAGE_NO, MESSAGE_NO,
        )
        if answer != MESSAGE_YES:
            self._log("接続距離が超過したため、解析を中止しました。許容距離を確認して再実行してください。")
            return None

        self.snap_spin.setMaximum(max(self.snap_spin.maximum(), required_distance))
        self.snap_spin.setValue(required_distance)
        self._log("許容距離を最小必要値{} mに変更して続行します。".format(required_distance))
        return float(required_distance)

    def _build_route_graph(self, network, start_points, end_pt, snap_limit):
        """起終点の近傍から道路グラフを作り、外側に短い経路がない範囲まで拡張する。"""
        route_points = [item[0] for item in start_points] + [end_pt]
        straight_distance = max(
            math.hypot(item[0].x() - end_pt.x(), item[0].y() - end_pt.y())
            for item in start_points
        )
        margin = max(250.0, snap_limit * 2.0, straight_distance * 0.25)
        network_extent = network.extent()
        last_error = None

        for attempt in range(16):
            search_rect = self._points_extent(route_points, margin)
            covers_network = self._contains_rect(search_rect, network_extent)
            self._log(
                "局所道路範囲を検索：拡張{}回目、余白{:.0f} m{}".format(
                    attempt + 1, margin,
                    "（ネットワーク全域）" if covers_network else "",
                )
            )
            try:
                nodes, adjacency, spatial_index, index_id_to_node = self._build_graph(
                    network, self._log, search_rect=search_rect
                )
                end_node, end_snap = self._nearest_node(
                    end_pt, nodes, spatial_index, index_id_to_node
                )
                snapped_starts = []
                for start_pt, start_id, layer_name, start_label in start_points:
                    start_node, start_snap = self._nearest_node(
                        start_pt, nodes, spatial_index, index_id_to_node
                    )
                    if start_snap > snap_limit:
                        raise ValueError(
                            "起点「{}」を道路に接続できません。起点 {:.1f} m（許容距離 {:.1f} m）。"
                            .format(start_label, start_snap, snap_limit)
                        )
                    snapped_starts.append((
                        start_pt, start_id, layer_name, start_label,
                        start_node, start_snap,
                    ))
                if end_snap > snap_limit:
                    raise ValueError(
                        "目的地を道路に接続できません。目的地 {:.1f} m（許容距離 {:.1f} m）。"
                        .format(end_snap, snap_limit)
                    )
                costs, previous = self._dijkstra_to_targets(
                    end_node, [item[4] for item in snapped_starts],
                    adjacency, self._log,
                )
                # 矩形外へ出る経路は、起点・目的地から矩形境界までの距離だけで
                # 少なくともこの距離を要する。候補路以下なら、矩形外に短縮路はない。
                certified = all(
                    self._boundary_clearance(item[0], search_rect)
                    + self._boundary_clearance(end_pt, search_rect)
                    >= costs[item[4]] + item[5] + end_snap
                    for item in snapped_starts
                )
                if certified or covers_network:
                    self._log(
                        "経路候補を確定：対象範囲{}地点、{}区間。{}".format(
                            len(nodes), sum(len(v) for v in adjacency) // 2,
                            "レイヤ全域を検索" if covers_network else "範囲外により短い経路がないことを確認",
                        )
                    )
                    return (
                        nodes, adjacency, spatial_index, index_id_to_node,
                        end_node, end_snap, snapped_starts, costs, previous,
                    )
                last_error = ValueError("局所範囲内に経路はありますが、範囲外に短い経路がないと確認できません。")
            except ValueError as exc:
                last_error = exc
                if covers_network and "有効な道路ラインがありません" not in str(exc):
                    raise
            if covers_network:
                if last_error is not None:
                    raise last_error
                break
            margin *= 2.0

        raise ValueError(
            "起点・目的地の周辺範囲を拡張しても経路を確定できませんでした。"
            "道路データの接続状態を確認するか、解析対象地域に道路データを切り出して再実行してください。"
            + (" 詳細：{}".format(last_error) if last_error else "")
        )

    @staticmethod
    def _route_from_tree(origin, root, nodes, previous):
        coords = [QgsPointXY(nodes[origin])]
        cursor = origin
        while cursor != root:
            next_node = previous[cursor]
            coords.append(QgsPointXY(nodes[next_node]))
            cursor = next_node
        return coords

    @staticmethod
    def _dijkstra_reach(seeds, adjacency, limit, meters_per_cost_unit, progress_callback=None):
        """距離または時間の上限までの最短コストを、必要な範囲だけ探索する。"""
        costs = {}
        owners = {}
        queue = []
        for node, owner, initial_cost in seeds:
            if initial_cost < costs.get(node, float("inf")):
                costs[node] = initial_cost
                owners[node] = owner
                heapq.heappush(queue, (initial_cost, node, owner))
        visited_count = 0
        while queue:
            cost, node, owner = heapq.heappop(queue)
            if cost != costs.get(node) or owner != owners.get(node):
                continue
            if cost > limit:
                break
            visited_count += 1
            if progress_callback and visited_count % 20000 == 0:
                progress_callback("到達圏を探索中：{}地点を確認".format(visited_count))
            for neighbor, length_m in adjacency[node]:
                candidate = cost + length_m / meters_per_cost_unit
                if candidate <= limit and candidate < costs.get(neighbor, float("inf")):
                    costs[neighbor] = candidate
                    owners[neighbor] = owner
                    heapq.heappush(queue, (candidate, neighbor, owner))
        return costs, owners

    def _unique_output_paths(self, gpkg_file, layer_name):
        """既存結果を保護し、同名ファイルがあれば日時と連番を付ける。"""
        gpkg_file = Path(gpkg_file)
        csv_file = gpkg_file.with_suffix(".csv")
        summary_file = gpkg_file.with_name(gpkg_file.stem + "_summary.csv")
        if gpkg_file.exists() or csv_file.exists() or summary_file.exists():
            stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
            suffix = stamp
            counter = 1
            while True:
                candidate = gpkg_file.with_name("{}_{}.gpkg".format(gpkg_file.stem, suffix))
                candidate_csv = candidate.with_suffix(".csv")
                candidate_summary = candidate.with_name(candidate.stem + "_summary.csv")
                if not candidate.exists() and not candidate_csv.exists() and not candidate_summary.exists():
                    gpkg_file = candidate
                    break
                counter += 1
                suffix = "{}_{}".format(stamp, counter)
            layer_name = "{}_{}".format(layer_name, suffix)
        return gpkg_file, gpkg_file.with_suffix(".csv"), layer_name

    def _write_catchment_outputs(
        self, network, nodes, adjacency, reach_sets, origins,
        limit, limit_kind, aggregation, meters_per_cost_unit, preset,
        gpkg_path, csv_path, summary_path, layer_name, release_graph_state=None,
    ):
        """到達区間を逐次出力し、同時に起点別・全体の要約統計を作る。"""
        columns = [
            ("run_datetime", FIELD_STRING), ("catchment_mode", FIELD_STRING),
            ("origin_layer", FIELD_STRING), ("origin_location", FIELD_STRING),
            ("origin_record_id", FIELD_STRING), ("network_layer", FIELD_STRING),
            ("network_crs", FIELD_STRING), ("threshold_type", FIELD_STRING),
            ("threshold_value", FIELD_DOUBLE), ("threshold_unit", FIELD_STRING),
            ("origin_snap_m", FIELD_DOUBLE),
            ("segment_distance_from_origin_m", FIELD_DOUBLE),
            ("segment_reach_length_m", FIELD_DOUBLE),
            ("segment_midpoint_distance_from_origin_m", FIELD_DOUBLE),
            ("speed_kmh", FIELD_DOUBLE), ("speed_mps", FIELD_DOUBLE),
            ("speed_region", FIELD_STRING), ("speed_road_type", FIELD_STRING),
            ("speed_time_period", FIELD_STRING), ("speed_area_category", FIELD_STRING),
            ("speed_profile", FIELD_STRING), ("speed_source_issuer", FIELD_STRING),
            ("speed_source_title", FIELD_STRING), ("speed_source_year", FIELD_STRING),
            ("speed_source_page", FIELD_STRING), ("speed_source_url", FIELD_STRING),
            ("speed_definition", FIELD_STRING),
        ]
        fields = QgsFields()
        for name, field_type in columns:
            fields.append(QgsField(name, field_type))
        csv_file = Path(csv_path)
        gpkg_file = Path(gpkg_path)
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        gpkg_file.parent.mkdir(parents=True, exist_ok=True)
        detail_layer_name = self._suffixed_layer_name(layer_name, "_区間明細")
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = detail_layer_name
        options.fileEncoding = "UTF-8"
        # _unique_output_paths()で未作成の新規ファイル名を確保しているため、
        # GeoPackageファイル自体を新規作成する。CreateOrOverwriteLayerは
        # 存在しないGPKGを更新モードで開こうとして、OGRエラーになるQGIS環境がある。
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        writer = QgsVectorFileWriter.create(
            str(gpkg_path), fields, LINE_WKB_TYPE, network.crs(),
            QgsProject.instance().transformContext(), options,
        )
        if writer is None or writer.hasError() != QgsVectorFileWriter.NoError:
            message = writer.errorMessage() if writer is not None else "GeoPackage writerを作成できませんでした。"
            raise ValueError("結果GeoPackageを作成できません：{}".format(message))

        column_names = [name for name, _kind in columns]
        feature_count = 0
        scale_m = meters_per_cost_unit
        run_datetime = datetime.now().astimezone().isoformat(timespec="seconds")
        stats_by_origin = {
            i: {"pieces": 0, "length_m": 0.0, "weighted_distance_m": 0.0,
                "min_distance_m": None, "max_distance_m": None}
            for i in range(len(origins))
        }

        def distance_along_edge(distance_u, distance_v, length_m, offset_m):
            """起点から道路区間上の位置までの最短距離（スナップ距離を含む）。"""
            from_u = distance_u * scale_m + offset_m
            from_v = distance_v * scale_m + length_m - offset_m
            return min(from_u, from_v)

        def summarize_piece(stats, distance_u, distance_v, length_m, begin_m, end_m):
            piece_length = end_m - begin_m
            if piece_length <= 0:
                return
            values = [distance_along_edge(distance_u, distance_v, length_m, begin_m),
                      distance_along_edge(distance_u, distance_v, length_m, end_m)]
            # 両端からの経路距離が等しくなる位置では、距離関数が折れ曲がる。
            if math.isfinite(distance_u) and math.isfinite(distance_v):
                crossover = (distance_v * scale_m + length_m - distance_u * scale_m) / 2.0
                if begin_m <= crossover <= end_m:
                    values.append(distance_along_edge(distance_u, distance_v, length_m, crossover))
                    breakpoints = [begin_m, crossover, end_m]
                else:
                    breakpoints = [begin_m, end_m]
            else:
                breakpoints = [begin_m, end_m]
            # 距離関数は区間ごとに線形なので、台形積分で延長加重平均を算出。
            area = 0.0
            for left, right in zip(breakpoints[:-1], breakpoints[1:]):
                left_value = distance_along_edge(distance_u, distance_v, length_m, left)
                right_value = distance_along_edge(distance_u, distance_v, length_m, right)
                area += (right - left) * (left_value + right_value) / 2.0
            stats["pieces"] += 1
            stats["length_m"] += piece_length
            stats["weighted_distance_m"] += area
            local_min, local_max = min(values), max(values)
            stats["min_distance_m"] = (
                local_min if stats["min_distance_m"] is None
                else min(stats["min_distance_m"], local_min)
            )
            stats["max_distance_m"] = (
                local_max if stats["max_distance_m"] is None
                else max(stats["max_distance_m"], local_max)
            )

        # 同じ無向区間は u < v の側から一度だけ出力。
        try:
            with csv_file.open("w", newline="", encoding="utf-8-sig") as handle:
                csv_writer = csv.DictWriter(handle, fieldnames=column_names)
                csv_writer.writeheader()
                for costs, owners in reach_sets:
                    for u, neighbors in enumerate(adjacency):
                        distance_u = costs.get(u, float("inf"))
                        for v, length_m in neighbors:
                            if v <= u:
                                continue
                            distance_v = costs.get(v, float("inf"))
                            if distance_u > limit and distance_v > limit:
                                continue
                            reach_u = min(length_m, max(0.0, (limit - distance_u) * scale_m))
                            reach_v = min(length_m, max(0.0, (limit - distance_v) * scale_m))
                            pieces = []
                            if reach_u + reach_v >= length_m:
                                chosen = u if distance_u <= distance_v else v
                                pieces.append((0.0, length_m, chosen))
                            else:
                                if reach_u > 0.001:
                                    pieces.append((0.0, reach_u, u))
                                if reach_v > 0.001:
                                    pieces.append((length_m - reach_v, length_m, v))
                            point_u, point_v = nodes[u], nodes[v]
                            dx, dy = point_v.x() - point_u.x(), point_v.y() - point_u.y()
                            for begin_m, end_m, owner_node in pieces:
                                owner = owners.get(owner_node, 0)
                                origin = origins[owner]
                                begin_ratio = begin_m / length_m
                                end_ratio = end_m / length_m
                                start_xy = QgsPointXY(point_u.x() + dx * begin_ratio, point_u.y() + dy * begin_ratio)
                                end_xy = QgsPointXY(point_u.x() + dx * end_ratio, point_u.y() + dy * end_ratio)
                                geometry = QgsGeometry.fromPolylineXY([start_xy, end_xy])
                                distance_from_origin = costs[owner_node] * scale_m
                                midpoint_offset = (begin_m + end_m) / 2.0
                                midpoint_distance = distance_along_edge(
                                    costs.get(u, float("inf")),
                                    costs.get(v, float("inf")),
                                    length_m, midpoint_offset,
                                )
                                summarize_piece(
                                    stats_by_origin[owner], costs.get(u, float("inf")),
                                    costs.get(v, float("inf")), length_m, begin_m, end_m,
                                )
                                threshold_type = "距離" if limit_kind == "distance" else "所要時間"
                                threshold_unit = "m" if limit_kind == "distance" else "分"
                                row = {
                                    "run_datetime": run_datetime,
                                    "catchment_mode": "起点ごとに個別" if aggregation == "individual" else "全起点で統合",
                                    "origin_layer": origin[2],
                                    "origin_location": origin[3],
                                    "origin_record_id": str(origin[1]),
                                    "network_layer": network.name(),
                                    "network_crs": network.crs().authid(),
                                    "threshold_type": threshold_type,
                                    "threshold_value": limit,
                                    "threshold_unit": threshold_unit,
                                    "origin_snap_m": round(origin[5], 2),
                                    "segment_distance_from_origin_m": round(distance_from_origin, 2),
                                    "segment_reach_length_m": round(end_m - begin_m, 2),
                                    "segment_midpoint_distance_from_origin_m": round(midpoint_distance, 2),
                                    "speed_kmh": preset["kmh"],
                                    "speed_mps": round(preset["kmh"] / 3.6, 4),
                                    "speed_region": preset.get("speed_region", ""),
                                    "speed_road_type": preset.get("speed_road_type", ""),
                                    "speed_time_period": preset.get("speed_time_period", ""),
                                    "speed_area_category": preset.get("speed_area_category", ""),
                                    "speed_profile": preset["label"],
                                    "speed_source_issuer": preset["issuer"],
                                    "speed_source_title": preset["title"],
                                    "speed_source_year": preset["year"],
                                    "speed_source_page": preset["page"],
                                    "speed_source_url": preset["url"],
                                    "speed_definition": preset["definition"],
                                }
                                feature = QgsFeature(fields)
                                feature.setGeometry(geometry)
                                feature.setAttributes([_localized_value(row[name]) for name in column_names])
                                if not writer.addFeature(feature):
                                    raise ValueError("GeoPackageへの到達区間書き込みに失敗しました：{}".format(writer.errorMessage()))
                                csv_writer.writerow({key: _localized_value(value) for key, value in row.items()})
                                feature_count += 1
                                if feature_count % 50000 == 0:
                                    self._log("到達道路区間を書き出し中：{}件".format(feature_count))
        finally:
            del writer
        self._log("区間明細を書き終えました。計算用の道路グラフを解放します。")
        if aggregation == "combined":
            for result in reach_sets:
                if isinstance(result, tuple) and len(result) == 2:
                    result[0].clear()
                    result[1].clear()
        for neighbors in adjacency:
            neighbors.clear()
        adjacency.clear()
        nodes.clear()
        if release_graph_state is not None:
            release_graph_state()
        gc.collect()
        self._log("道路グラフと探索結果を解放しました。後処理を開始します。")
        display_layer_name = layer_name
        if aggregation == "individual":
            self._write_origin_catchment_layer(
                gpkg_file, detail_layer_name, layer_name, network, origins,
                limit, limit_kind, preset, run_datetime,
            )
            self._write_individual_convex_hulls(
                gpkg_file, layer_name, network.crs(),
            )
            self._log("起点別凸包と、起点別凸包を融合したポリゴンを作成しました。")
        else:
            self._write_combined_catchment_layer(
                gpkg_file, detail_layer_name, layer_name, network, origins,
                limit, limit_kind, preset, run_datetime,
            )
            self._log("起点別に道路を囲む凸包を1レイヤに作成しました。")
        saved_layer = QgsVectorLayer(
            "{}|layername={}".format(gpkg_file, display_layer_name),
            display_layer_name, "ogr"
        )
        if not saved_layer.isValid():
            raise ValueError("保存した到達圏レイヤをQGISに読み込めませんでした。")
        if aggregation == "individual":
            self._apply_origin_catchment_style(saved_layer)
        else:
            self._apply_output_line_style(saved_layer)
        hide_dense_line = feature_count >= 100000
        project = QgsProject.instance()
        project.addMapLayer(saved_layer, False)
        line_node = project.layerTreeRoot().insertLayer(0, saved_layer)
        line_node.setItemVisibilityChecked(not hide_dense_line)
        if hide_dense_line:
            self._log(
                "区間明細{}件の集約ラインは、初期描画の負荷を避けるため非表示で追加しました。"
                .format(feature_count)
            )
        self._write_catchment_summary(
            summary_path, origins, stats_by_origin, limit, limit_kind,
            aggregation, preset, feature_count,
        )
        return feature_count

    def _write_origin_catchment_layer(
        self, gpkg_file, detail_layer_name, layer_name, network, origins,
        limit, limit_kind, preset, run_datetime,
    ):
        """区間明細を残し、起点ごとに1つのMultiLineString地物を別レイヤに作る。"""
        detail_layer = QgsVectorLayer(
            "{}|layername={}".format(gpkg_file, detail_layer_name),
            detail_layer_name, "ogr",
        )
        if not detail_layer.isValid():
            raise ValueError("到達圏の区間明細レイヤを再読込できませんでした。")

        id_field = detail_layer.fields().indexOf("origin_record_id")
        layer_field = detail_layer.fields().indexOf("origin_layer")
        length_field = detail_layer.fields().indexOf("segment_reach_length_m")
        if min(id_field, layer_field, length_field) < 0:
            raise ValueError("区間明細に集約に必要な属性がありません。")
        try:
            detail_layer.dataProvider().createAttributeIndex(id_field)
        except Exception:
            # Providerによって属性索引作成に対応しない場合も、正確性を優先して続行する。
            pass

        aggregate_columns = [
            ("run_datetime", FIELD_STRING), ("catchment_mode", FIELD_STRING),
            ("origin_layer", FIELD_STRING), ("origin_location", FIELD_STRING),
            ("origin_record_id", FIELD_STRING), ("network_layer", FIELD_STRING),
            ("network_crs", FIELD_STRING), ("threshold_type", FIELD_STRING),
            ("threshold_value", FIELD_DOUBLE), ("threshold_unit", FIELD_STRING),
            ("origin_snap_m", FIELD_DOUBLE),
            ("reachable_segment_count", FIELD_DOUBLE),
            ("reachable_road_length_m", FIELD_DOUBLE),
            ("speed_kmh", FIELD_DOUBLE), ("speed_mps", FIELD_DOUBLE),
            ("speed_region", FIELD_STRING), ("speed_road_type", FIELD_STRING),
            ("speed_time_period", FIELD_STRING), ("speed_area_category", FIELD_STRING),
            ("speed_profile", FIELD_STRING), ("speed_source_issuer", FIELD_STRING),
            ("speed_source_title", FIELD_STRING), ("speed_source_year", FIELD_STRING),
            ("speed_source_page", FIELD_STRING), ("speed_source_url", FIELD_STRING),
            ("speed_definition", FIELD_STRING),
        ]
        fields = QgsFields()
        for name, field_type in aggregate_columns:
            fields.append(QgsField(name, field_type))

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = layer_name
        options.fileEncoding = "UTF-8"
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        writer = QgsVectorFileWriter.create(
            str(gpkg_file), fields, MULTILINE_WKB_TYPE, network.crs(),
            QgsProject.instance().transformContext(), options,
        )
        if writer is None or writer.hasError() != QgsVectorFileWriter.NoError:
            message = writer.errorMessage() if writer is not None else "GeoPackage writerを作成できませんでした。"
            raise ValueError("起点別集約レイヤをGeoPackageに作成できません：{}".format(message))

        try:
            for index, origin in enumerate(origins):
                escaped_id = str(origin[1]).replace("'", "''")
                escaped_layer = str(origin[2]).replace("'", "''")
                expression = (
                    '"origin_record_id" = \'{}\' AND "origin_layer" = \'{}\''
                    .format(escaped_id, escaped_layer)
                )
                request = QgsFeatureRequest().setFilterExpression(expression)
                parts = []
                road_length = 0.0
                for feature in detail_layer.getFeatures(request):
                    geometry = feature.geometry()
                    if geometry.isNull() or geometry.isEmpty():
                        continue
                    line = geometry.asPolyline()
                    if len(line) >= 2:
                        parts.append(line)
                        road_length += float(feature.attribute(length_field) or 0.0)

                feature = QgsFeature(fields)
                if parts:
                    feature.setGeometry(QgsGeometry.fromMultiPolylineXY(parts))
                threshold_type = "距離" if limit_kind == "distance" else "所要時間"
                threshold_unit = "m" if limit_kind == "distance" else "分"
                row = {
                    "run_datetime": run_datetime,
                    "catchment_mode": "起点ごとに個別",
                    "origin_layer": origin[2],
                    "origin_location": origin[3],
                    "origin_record_id": str(origin[1]),
                    "network_layer": network.name(),
                    "network_crs": network.crs().authid(),
                    "threshold_type": threshold_type,
                    "threshold_value": limit,
                    "threshold_unit": threshold_unit,
                    "origin_snap_m": round(origin[5], 2),
                    "reachable_segment_count": len(parts),
                    "reachable_road_length_m": round(road_length, 2),
                    "speed_kmh": preset["kmh"],
                    "speed_mps": round(preset["kmh"] / 3.6, 4),
                    "speed_region": preset.get("speed_region", ""),
                    "speed_road_type": preset.get("speed_road_type", ""),
                    "speed_time_period": preset.get("speed_time_period", ""),
                    "speed_area_category": preset.get("speed_area_category", ""),
                    "speed_profile": preset["label"],
                    "speed_source_issuer": preset["issuer"],
                    "speed_source_title": preset["title"],
                    "speed_source_year": preset["year"],
                    "speed_source_page": preset["page"],
                    "speed_source_url": preset["url"],
                    "speed_definition": preset["definition"],
                }
                feature.setAttributes([_localized_value(row[name]) for name, _kind in aggregate_columns])
                if not writer.addFeature(feature):
                    raise ValueError(
                        "起点別集約ラインの書き込みに失敗しました：{}"
                        .format(writer.errorMessage())
                    )
                if (index + 1) % 100 == 0 or index + 1 == len(origins):
                    self._log("起点別集約ラインを書き出し中：{} / {}件".format(index + 1, len(origins)))
        finally:
            del writer

    def _write_combined_catchment_layer(
        self, gpkg_file, detail_layer_name, layer_name, network, origins,
        limit, limit_kind, preset, run_datetime,
    ):
        """区間明細をC++のMultiLineStringに集約し、帰属先別の凸包を作る。"""
        detail_layer = QgsVectorLayer(
            "{}|layername={}".format(gpkg_file, detail_layer_name),
            detail_layer_name, "ogr",
        )
        if not detail_layer.isValid():
            raise ValueError("統合到達圏の区間明細を読み込めませんでした。")
        length_index = detail_layer.fields().indexOf("segment_reach_length_m")
        record_id_index = detail_layer.fields().indexOf("origin_record_id")
        origin_layer_index = detail_layer.fields().indexOf("origin_layer")
        if min(length_index, record_id_index, origin_layer_index) < 0:
            raise ValueError("統合到達圏の区間明細に集約に必要な属性がありません。")

        origin_indices = {
            (str(origin[1]), str(origin[2])): index
            for index, origin in enumerate(origins)
        }
        origin_points = [[] for _origin in origins]
        origin_segment_counts = [0] * len(origins)
        origin_lengths = [0.0] * len(origins)
        multi_line = QgsMultiLineString()
        road_length = 0.0
        segment_count = 0
        for source in detail_layer.getFeatures():
            geometry = source.geometry()
            if geometry.isNull() or geometry.isEmpty():
                continue
            if geometry.isMultipart():
                raise ValueError("統合区間明細に想定外のマルチライン地物があります。")
            if not multi_line.addGeometry(geometry.constGet().clone()):
                raise ValueError("統合ラインへ道路区間を追加できませんでした。")
            origin_key = (
                str(source.attribute(record_id_index)),
                str(source.attribute(origin_layer_index)),
            )
            origin_index = origin_indices.get(origin_key)
            segment_length = float(source.attribute(length_index) or 0.0)
            if origin_index is not None:
                origin_segment_counts[origin_index] += 1
                origin_lengths[origin_index] += segment_length
                points = origin_points[origin_index]
                for point in geometry.vertices():
                    points.append(QgsPointXY(point.x(), point.y()))
                    if len(points) >= 20000:
                        partial_hull = QgsGeometry.fromMultiPointXY(points).convexHull()
                        origin_points[origin_index] = [
                            QgsPointXY(vertex.x(), vertex.y())
                            for vertex in partial_hull.vertices()
                        ]
                        points = origin_points[origin_index]
            road_length += segment_length
            segment_count += 1
            if segment_count % 50000 == 0:
                self._log(
                    "統合表示ライン・起点別凸包を準備中：{} / {}区間"
                    .format(segment_count, detail_layer.featureCount())
                )

        columns = [
            ("run_datetime", FIELD_STRING), ("catchment_mode", FIELD_STRING),
            ("origin_layer", FIELD_STRING), ("origin_location", FIELD_STRING),
            ("origin_record_id", FIELD_STRING), ("origin_count", FIELD_DOUBLE),
            ("network_layer", FIELD_STRING), ("network_crs", FIELD_STRING),
            ("threshold_type", FIELD_STRING), ("threshold_value", FIELD_DOUBLE),
            ("threshold_unit", FIELD_STRING), ("reachable_segment_count", FIELD_DOUBLE),
            ("reachable_road_length_m", FIELD_DOUBLE),
            ("speed_kmh", FIELD_DOUBLE), ("speed_mps", FIELD_DOUBLE),
            ("speed_region", FIELD_STRING), ("speed_road_type", FIELD_STRING),
            ("speed_time_period", FIELD_STRING), ("speed_area_category", FIELD_STRING),
            ("speed_profile", FIELD_STRING), ("speed_source_issuer", FIELD_STRING),
            ("speed_source_title", FIELD_STRING), ("speed_source_year", FIELD_STRING),
            ("speed_source_page", FIELD_STRING), ("speed_source_url", FIELD_STRING),
            ("speed_definition", FIELD_STRING),
        ]
        fields = QgsFields()
        for name, kind in columns:
            fields.append(QgsField(name, kind))
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = layer_name
        options.fileEncoding = "UTF-8"
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        writer = QgsVectorFileWriter.create(
            str(gpkg_file), fields, MULTILINE_WKB_TYPE, network.crs(),
            QgsProject.instance().transformContext(), options,
        )
        if writer is None or writer.hasError() != QgsVectorFileWriter.NoError:
            message = writer.errorMessage() if writer is not None else "GeoPackage writerを作成できませんでした。"
            raise ValueError("統合到達圏レイヤを作成できません：{}".format(message))
        try:
            self._log("全道路区間を1地物のマルチラインに書き込んでいます。")
            feature = QgsFeature(fields)
            if segment_count:
                feature.setGeometry(QgsGeometry(multi_line))
            row = {
                "run_datetime": run_datetime,
                "catchment_mode": "全起点で統合",
                "origin_layer": origins[0][2] if origins else "",
                "origin_location": "全起点を統合",
                "origin_record_id": "",
                "origin_count": len(origins),
                "network_layer": network.name(),
                "network_crs": network.crs().authid(),
                "threshold_type": "距離" if limit_kind == "distance" else "所要時間",
                "threshold_value": limit,
                "threshold_unit": "m" if limit_kind == "distance" else "分",
                "reachable_segment_count": segment_count,
                "reachable_road_length_m": round(road_length, 2),
                "speed_kmh": preset["kmh"],
                "speed_mps": round(preset["kmh"] / 3.6, 4),
                "speed_region": preset.get("speed_region", ""),
                "speed_road_type": preset.get("speed_road_type", ""),
                "speed_time_period": preset.get("speed_time_period", ""),
                "speed_area_category": preset.get("speed_area_category", ""),
                "speed_profile": preset["label"],
                "speed_source_issuer": preset["issuer"],
                "speed_source_title": preset["title"],
                "speed_source_year": preset["year"],
                "speed_source_page": preset["page"],
                "speed_source_url": preset["url"],
                "speed_definition": preset["definition"],
            }
            feature.setAttributes([_localized_value(row[name]) for name, _kind in columns])
            if not writer.addFeature(feature):
                raise ValueError("統合到達圏の集約ラインを書き込めません：{}".format(writer.errorMessage()))
        finally:
            del writer
        self._log(
            "統合到達圏を1地物に集約：起点{}件、道路区間{}件、重複を除く道路延長{:.1f} m。"
            .format(len(origins), segment_count, road_length)
        )

        hull_name = AccessibilityDialog._suffixed_layer_name(
            layer_name, "_到達道路別凸包"
        )
        hull_fields = QgsFields()
        for name, kind in (
            ("origin_layer", FIELD_STRING), ("origin_location", FIELD_STRING),
            ("origin_record_id", FIELD_STRING),
            ("assigned_segment_count", FIELD_DOUBLE),
            ("assigned_road_length_m", FIELD_DOUBLE),
            ("hull_definition", FIELD_STRING),
        ):
            hull_fields.append(QgsField(name, kind))
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = hull_name
        options.fileEncoding = "UTF-8"
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        hull_writer = QgsVectorFileWriter.create(
            str(gpkg_file), hull_fields, MULTIPOLYGON_WKB_TYPE, network.crs(),
            QgsProject.instance().transformContext(), options,
        )
        if hull_writer is None or hull_writer.hasError() != QgsVectorFileWriter.NoError:
            message = hull_writer.errorMessage() if hull_writer is not None else "GeoPackage writerを作成できませんでした。"
            raise ValueError("帰属先別凸包レイヤを作成できません：{}".format(message))
        try:
            for index, origin in enumerate(origins):
                points = origin_points[index]
                hull = (
                    QgsGeometry.fromMultiPointXY(points).convexHull()
                    if len(points) >= 3 else QgsGeometry()
                )
                is_polygon = (
                    not hull.isNull() and not hull.isEmpty()
                    and QgsWkbTypes.geometryType(hull.wkbType()) == POLYGON_GEOMETRY_TYPE
                )
                if is_polygon:
                    hull.convertToMultiType()
                feature = QgsFeature(hull_fields)
                if is_polygon:
                    feature.setGeometry(hull)
                feature.setAttributes([
                    origin[2], origin[3], str(origin[1]),
                    origin_segment_counts[index], round(origin_lengths[index], 2),
                    _localized_value("統合到達区間の最短コスト帰属先別凸包。起点単独の到達圏ではない。"),
                ])
                if not hull_writer.addFeature(feature):
                    raise ValueError(
                        "帰属先別凸包を書き込めません：{}"
                        .format(hull_writer.errorMessage())
                    )
                if (index + 1) % 100 == 0 or index + 1 == len(origins):
                    self._log("帰属先別凸包を書き出し中：{} / {}起点".format(index + 1, len(origins)))
        finally:
            del hull_writer

        hull_layer = AccessibilityDialog._polygon_layer(gpkg_file, hull_name, network.crs())
        if not hull_layer.isValid():
            raise ValueError("帰属先別凸包レイヤをQGISに読み込めませんでした。")
        AccessibilityDialog._apply_origin_hull_style(hull_layer)
        QgsProject.instance().addMapLayer(hull_layer)
        self._log("帰属先別の凸包ポリゴン{}件を1レイヤに追加しました。".format(len(origins)))

    @staticmethod
    def _suffixed_layer_name(base_name, suffix):
        suffix = translate_text(suffix, OUTPUT_LANGUAGE)
        max_base_length = max(1, 63 - len(suffix))
        return "{}{}".format(base_name[:max_base_length], suffix)

    @staticmethod
    def _random_origin_color(value):
        seed = hashlib.sha256(str(value).encode("utf-8")).digest()
        hue = int.from_bytes(seed[:4], "big") % 360
        # QGIS の選択色と紛らわしい黄色帯を避ける。
        if 38 <= hue <= 72:
            hue = (hue + 65) % 360
        return QColor.fromHsv(hue, 230, 255)

    @staticmethod
    def _polygon_layer(gpkg_file, layer_name, crs):
        return QgsVectorLayer(
            "{}|layername={}".format(gpkg_file, layer_name), layer_name, "ogr"
        )

    @staticmethod
    def _write_individual_convex_hulls(gpkg_file, line_layer_name, crs):
        """起点別凸包と、各凸包の重なりを融合したレイヤを保存・追加する。"""
        line_layer = QgsVectorLayer(
            "{}|layername={}".format(gpkg_file, line_layer_name),
            line_layer_name, "ogr",
        )
        if not line_layer.isValid():
            raise ValueError("起点別集約ラインを凸包計算用に読み込めませんでした。")

        origin_suffix = "_起点別凸包"
        origin_hull_name = AccessibilityDialog._suffixed_layer_name(
            line_layer_name, origin_suffix
        )
        hull_fields = QgsFields()
        for name, kind in (
            ("origin_layer", FIELD_STRING), ("origin_location", FIELD_STRING),
            ("origin_record_id", FIELD_STRING),
            ("reachable_segment_count", FIELD_DOUBLE),
            ("reachable_road_length_m", FIELD_DOUBLE),
            ("hull_method", FIELD_STRING),
        ):
            hull_fields.append(QgsField(name, kind))

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = origin_hull_name
        options.fileEncoding = "UTF-8"
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        writer = QgsVectorFileWriter.create(
            str(gpkg_file), hull_fields, MULTIPOLYGON_WKB_TYPE, crs,
            QgsProject.instance().transformContext(), options,
        )
        if writer is None or writer.hasError() != QgsVectorFileWriter.NoError:
            message = writer.errorMessage() if writer is not None else "GeoPackage writerを作成できませんでした。"
            raise ValueError("起点別凸包レイヤを作成できません：{}".format(message))

        valid_hulls = []
        try:
            for source in line_layer.getFeatures():
                geometry = source.geometry()
                hull = geometry.convexHull() if not geometry.isNull() and not geometry.isEmpty() else QgsGeometry()
                is_polygon = (
                    not hull.isNull() and not hull.isEmpty()
                    and QgsWkbTypes.geometryType(hull.wkbType()) == POLYGON_GEOMETRY_TYPE
                )
                if is_polygon:
                    hull.convertToMultiType()
                    valid_hulls.append(QgsGeometry(hull))
                output = QgsFeature(hull_fields)
                if is_polygon:
                    output.setGeometry(hull)
                output.setAttributes([
                    source.attribute("origin_layer"),
                    source.attribute("origin_location"),
                    source.attribute("origin_record_id"),
                    source.attribute("reachable_segment_count"),
                    source.attribute("reachable_road_length_m"),
                    _localized_value("到達道路区間の凸包（内部がすべて到達可能とは限らない）"),
                ])
                if not writer.addFeature(output):
                    raise ValueError("起点別凸包を書き込めません：{}".format(writer.errorMessage()))
        finally:
            del writer

        merged_name = AccessibilityDialog._suffixed_layer_name(
            line_layer_name, "_全起点凸包融合"
        )
        merged_fields = QgsFields()
        for name, kind in (
            ("origin_count", FIELD_DOUBLE), ("hull_count", FIELD_DOUBLE),
            ("geometry_method", FIELD_STRING), ("interpretation", FIELD_STRING),
        ):
            merged_fields.append(QgsField(name, kind))
        merged_geometry = (
            QgsGeometry.unaryUnion(valid_hulls)
            if valid_hulls else QgsGeometry()
        )
        if (
            not merged_geometry.isNull() and not merged_geometry.isEmpty()
            and QgsWkbTypes.geometryType(merged_geometry.wkbType()) == POLYGON_GEOMETRY_TYPE
        ):
            merged_geometry.convertToMultiType()
        else:
            merged_geometry = QgsGeometry()

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = merged_name
        options.fileEncoding = "UTF-8"
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        writer = QgsVectorFileWriter.create(
            str(gpkg_file), merged_fields, MULTIPOLYGON_WKB_TYPE, crs,
            QgsProject.instance().transformContext(), options,
        )
        if writer is None or writer.hasError() != QgsVectorFileWriter.NoError:
            message = writer.errorMessage() if writer is not None else "GeoPackage writerを作成できませんでした。"
            raise ValueError("融合凸包レイヤを作成できません：{}".format(message))
        try:
            output = QgsFeature(merged_fields)
            if not merged_geometry.isNull() and not merged_geometry.isEmpty():
                output.setGeometry(merged_geometry)
            output.setAttributes([
                line_layer.featureCount(), len(valid_hulls),
                _localized_value("起点別凸包の融合（凸包全体を再度凸包化したものではない）"),
                _localized_value("各起点の凸包を融合。ポリゴン内部がすべて到達可能とは限らない。"),
            ])
            if not writer.addFeature(output):
                raise ValueError("融合凸包を書き込めません：{}".format(writer.errorMessage()))
        finally:
            del writer

        origin_hull_layer = AccessibilityDialog._polygon_layer(
            gpkg_file, origin_hull_name, crs
        )
        merged_layer = AccessibilityDialog._polygon_layer(gpkg_file, merged_name, crs)
        if not origin_hull_layer.isValid() or not merged_layer.isValid():
            raise ValueError("作成した凸包レイヤをQGISに読み込めませんでした。")
        AccessibilityDialog._apply_origin_hull_style(origin_hull_layer)
        AccessibilityDialog._apply_fused_hull_style(merged_layer)
        project = QgsProject.instance()
        project.addMapLayer(origin_hull_layer)
        project.addMapLayer(merged_layer)

    @staticmethod
    def _apply_origin_hull_style(layer):
        field_name = "origin_location"
        values = sorted(layer.uniqueValues(layer.fields().indexOf(field_name)), key=lambda value: str(value))
        categories = []
        for value in values:
            color = AccessibilityDialog._random_origin_color(value)
            symbol = QgsFillSymbol.createSimple({
                "color": "{},{},{},45".format(color.red(), color.green(), color.blue()),
                "outline_color": "35,35,35,220", "outline_width": "0.45",
                "outline_width_unit": "MM",
            })
            categories.append(QgsRendererCategory(value, symbol, str(value)))
        layer.setRenderer(QgsCategorizedSymbolRenderer(field_name, categories))
        layer.triggerRepaint()

    @staticmethod
    def _apply_fused_hull_style(layer):
        symbol = QgsFillSymbol.createSimple({
            "color": "55,125,185,48", "outline_color": "25,25,25,230",
            "outline_width": "0.6", "outline_width_unit": "MM",
        })
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()

    @staticmethod
    def _apply_origin_catchment_style(layer):
        """起点名ごとにランダム風の再現可能な色を付け、黒い縁取りを残す。"""
        field_name = "origin_location"
        field_index = layer.fields().indexOf(field_name)
        if field_index < 0:
            AccessibilityDialog._apply_output_line_style(layer)
            return

        values = sorted(layer.uniqueValues(field_index), key=lambda value: str(value))
        categories = []
        for value in values:
            color = AccessibilityDialog._random_origin_color(value)
            symbol = QgsLineSymbol()
            symbol.changeSymbolLayer(0, QgsSimpleLineSymbolLayer.create({
                "line_color": "25,25,25,255", "line_width": "0.8",
                "line_width_unit": "MM", "line_style": "solid",
                "joinstyle": "round", "capstyle": "round",
            }))
            symbol.appendSymbolLayer(QgsSimpleLineSymbolLayer.create({
                "line_color": color.name(), "line_width": "0.4",
                "line_width_unit": "MM", "line_style": "solid",
                "joinstyle": "round", "capstyle": "round",
            }))
            label = str(value) if str(value) else "（名称なし）"
            categories.append(QgsRendererCategory(value, symbol, label))
        layer.setRenderer(QgsCategorizedSymbolRenderer(field_name, categories))
        layer.triggerRepaint()

    @staticmethod
    def _write_catchment_summary(
        path, origins, stats_by_origin, limit, limit_kind,
        aggregation, preset, feature_count,
    ):
        """区間CSVとは別に、全体と起点別の到達量をUTF-8 CSVに保存する。"""
        summary_path = Path(path)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        speed_m_per_min = preset.get("kmh", 0.0) * 1000.0 / 60.0
        threshold_unit = "m" if limit_kind == "distance" else "分"
        threshold_type = "距離" if limit_kind == "distance" else "所要時間"
        summary_scope = (
            "起点別到達圏（重複あり）" if aggregation == "individual"
            else "到達可能道路の和集合（重複なし）"
        )
        header = [
            "summary_type", "summary_scope", "aggregation_method", "origin_layer",
            "origin_record_id", "origin_name", "origin_snap_m", "origin_count",
            "output_piece_count", "reachable_road_length_m", "reachable_road_length_km",
            "min_network_distance_from_origin_m", "mean_network_distance_from_origin_m",
            "max_network_distance_from_origin_m", "min_estimated_time_min",
            "mean_estimated_time_min", "max_estimated_time_min", "threshold_type",
            "threshold_value", "threshold_unit", "speed_kmh", "speed_profile",
            "speed_source_issuer", "speed_source_title", "speed_source_year",
            "speed_source_page", "speed_source_url", "facility_distance_n",
            "facility_time_n", "facility_reach_length_min_m",
            "facility_reach_length_mean_m", "facility_reach_length_median_m",
            "facility_reach_length_max_m", "facility_max_distance_min_m",
            "facility_max_distance_mean_m", "facility_max_distance_median_m",
            "facility_max_distance_max_m", "facility_max_time_min_min",
            "facility_max_time_mean_min", "facility_max_time_median_min",
            "facility_max_time_max_min", "interpretation_note",
        ]
        display_names = {
            "summary_type": "行の区分", "summary_scope": "集計対象",
            "aggregation_method": "集計方法", "origin_layer": "起点レイヤ",
            "origin_record_id": "起点ID", "origin_name": "起点名",
            "origin_snap_m": "起点から道路までの距離_m", "origin_count": "起点数",
            "output_piece_count": "出力区間数", "reachable_road_length_m": "到達道路延長_m",
            "reachable_road_length_km": "到達道路延長_km",
            "min_network_distance_from_origin_m": "道路上距離_最小_m",
            "mean_network_distance_from_origin_m": "道路上距離_平均_m",
            "max_network_distance_from_origin_m": "道路上距離_最大_m",
            "min_estimated_time_min": "参考時間_最小_分",
            "mean_estimated_time_min": "参考時間_平均_分",
            "max_estimated_time_min": "参考時間_最大_分",
            "threshold_type": "上限基準", "threshold_value": "上限値",
            "threshold_unit": "上限単位", "speed_kmh": "移動速度_km_h",
            "speed_profile": "移動速度設定", "speed_source_issuer": "速度出典機関",
            "speed_source_title": "速度出典資料", "speed_source_year": "速度出典年",
            "speed_source_page": "速度出典頁", "speed_source_url": "速度出典URL",
            "facility_distance_n": "施設別距離統計の対象数",
            "facility_time_n": "施設別時間統計の対象数",
            "facility_reach_length_min_m": "施設別到達道路延長_最小_m",
            "facility_reach_length_mean_m": "施設別到達道路延長_平均_m",
            "facility_reach_length_median_m": "施設別到達道路延長_中央値_m",
            "facility_reach_length_max_m": "施設別到達道路延長_最大_m",
            "facility_max_distance_min_m": "施設別最大到達距離_最小_m",
            "facility_max_distance_mean_m": "施設別最大到達距離_平均_m",
            "facility_max_distance_median_m": "施設別最大到達距離_中央値_m",
            "facility_max_distance_max_m": "施設別最大到達距離_最大_m",
            "facility_max_time_min_min": "施設別最大参考時間_最小_分",
            "facility_max_time_mean_min": "施設別最大参考時間_平均_分",
            "facility_max_time_median_min": "施設別最大参考時間_中央値_分",
            "facility_max_time_max_min": "施設別最大参考時間_最大_分",
            "interpretation_note": "読み方",
        }

        def record(summary_type, scope, origin, stats, count, note):
            length = stats["length_m"]
            if length > 0:
                mean_distance = stats["weighted_distance_m"] / length
                min_distance = stats["min_distance_m"]
                max_distance = stats["max_distance_m"]
            else:
                mean_distance = min_distance = max_distance = ""
            if speed_m_per_min > 0 and length > 0:
                min_time = min_distance / speed_m_per_min
                mean_time = mean_distance / speed_m_per_min
                max_time = max_distance / speed_m_per_min
            else:
                min_time = mean_time = max_time = ""
            origin = origin or (None, "", "全体", "全体", 0, 0.0)
            return {
                "summary_type": summary_type,
                "summary_scope": scope,
                "aggregation_method": "個別" if aggregation == "individual" else "統合",
                "origin_layer": origin[2] if summary_type != "全体" else "",
                "origin_record_id": str(origin[1]) if summary_type != "全体" else "",
                "origin_name": origin[3] if summary_type != "全体" else "",
                "origin_snap_m": round(origin[5], 2) if summary_type != "全体" else "",
                "origin_count": len(origins) if summary_type == "全体" else 1,
                "output_piece_count": count,
                "reachable_road_length_m": round(length, 2),
                "reachable_road_length_km": round(length / 1000.0, 4),
                "min_network_distance_from_origin_m": round(min_distance, 2) if min_distance != "" else "",
                "mean_network_distance_from_origin_m": round(mean_distance, 2) if mean_distance != "" else "",
                "max_network_distance_from_origin_m": round(max_distance, 2) if max_distance != "" else "",
                "min_estimated_time_min": round(min_time, 2) if min_time != "" else "",
                "mean_estimated_time_min": round(mean_time, 2) if mean_time != "" else "",
                "max_estimated_time_min": round(max_time, 2) if max_time != "" else "",
                "threshold_type": threshold_type,
                "threshold_value": limit,
                "threshold_unit": threshold_unit,
                "speed_kmh": preset.get("kmh", 0.0),
                "speed_profile": preset.get("label", ""),
                "speed_source_issuer": preset.get("issuer", ""),
                "speed_source_title": preset.get("title", ""),
                "speed_source_year": preset.get("year", ""),
                "speed_source_page": preset.get("page", ""),
                "speed_source_url": preset.get("url", ""),
                "facility_distance_n": "",
                "facility_time_n": "",
                "facility_reach_length_min_m": "",
                "facility_reach_length_mean_m": "",
                "facility_reach_length_median_m": "",
                "facility_reach_length_max_m": "",
                "facility_max_distance_min_m": "",
                "facility_max_distance_mean_m": "",
                "facility_max_distance_median_m": "",
                "facility_max_distance_max_m": "",
                "facility_max_time_min_min": "",
                "facility_max_time_mean_min": "",
                "facility_max_time_median_min": "",
                "facility_max_time_max_min": "",
                "interpretation_note": note,
            }

        overall = {"pieces": 0, "length_m": 0.0, "weighted_distance_m": 0.0,
                   "min_distance_m": None, "max_distance_m": None}
        for stats in stats_by_origin.values():
            overall["pieces"] += stats["pieces"]
            overall["length_m"] += stats["length_m"]
            overall["weighted_distance_m"] += stats["weighted_distance_m"]
            if stats["min_distance_m"] is not None:
                overall["min_distance_m"] = (
                    stats["min_distance_m"] if overall["min_distance_m"] is None
                    else min(overall["min_distance_m"], stats["min_distance_m"])
                )
                overall["max_distance_m"] = (
                    stats["max_distance_m"] if overall["max_distance_m"] is None
                    else max(overall["max_distance_m"], stats["max_distance_m"])
                )
        note = (
            "個別起点の値を合計。重複する道路区間は起点数分含まれる。"
            if aggregation == "individual"
            else "到達可能道路の和集合。各起点行は、出力区間の帰属先別集計であり、施設単独の到達範囲ではない。"
        )
        rows = [record("全体", summary_scope, None, overall, feature_count, note)]
        if aggregation == "individual":
            facility_lengths = [stats["length_m"] for stats in stats_by_origin.values()]
            facility_distances = [
                stats["max_distance_m"] for stats in stats_by_origin.values()
                if stats["max_distance_m"] is not None
            ]
            facility_times = (
                [distance / speed_m_per_min for distance in facility_distances]
                if speed_m_per_min > 0 else []
            )

            def descriptive(values, prefix, unit):
                if not values:
                    return {}
                return {
                    prefix + "_min_" + unit: round(min(values), 2),
                    prefix + "_mean_" + unit: round(statistics.mean(values), 2),
                    prefix + "_median_" + unit: round(statistics.median(values), 2),
                    prefix + "_max_" + unit: round(max(values), 2),
                }

            rows[0].update({
                "facility_distance_n": len(facility_distances),
                "facility_time_n": len(facility_times),
                **descriptive(facility_lengths, "facility_reach_length", "m"),
                **descriptive(facility_distances, "facility_max_distance", "m"),
                **descriptive(facility_times, "facility_max_time", "min"),
            })
        for index, origin in enumerate(origins):
            origin_scope = (
                "施設単独の到達圏" if aggregation == "individual"
                else "統合出力の帰属先別内訳（施設単独の到達圏ではない）"
            )
            rows.append(record(
                "起点別" if aggregation == "individual" else "帰属先別",
                origin_scope, origin, stats_by_origin[index], stats_by_origin[index]["pieces"], note,
            ))
        with summary_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=[display_names[name] for name in header])
            writer.writeheader()
            writer.writerows(
                {display_names[name]: row[name] for name in header}
                for row in rows
            )

    def run_analysis(self):
        self.log_edit.clear()
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self._log("解析を開始します。")
        nodes = adjacency = spatial_index = index_id_to_node = None
        costs = owners = seeds = None

        def release_graph_state():
            nonlocal nodes, adjacency, spatial_index, index_id_to_node
            nonlocal costs, owners, seeds
            nodes = adjacency = spatial_index = index_id_to_node = None
            costs = owners = seeds = None

        try:
            network = self._layer(self.layer_combo)
            if network is None:
                raise ValueError("道路ラインレイヤを選択してください。")
            if network.crs().isGeographic() or network.crs().mapUnits() != DISTANCE_METERS:
                raise ValueError("道路ラインレイヤはメートル単位の投影座標系にしてください。")
            output_path = self.output_edit.text().strip()
            layer_name = self.result_layer_name_edit.text().strip()
            if not output_path:
                raise ValueError("共通の出力先（.gpkg）を指定してください。")
            gpkg_file = Path(output_path)
            if gpkg_file.suffix.lower() != ".gpkg":
                raise ValueError("結果レイヤの保存先は .gpkg ファイルにしてください。")
            if not layer_name:
                raise ValueError("QGISに追加するレイヤ名を入力してください。")
            gpkg_file, csv_file, layer_name = self._unique_output_paths(gpkg_file, layer_name)
            csv_path = str(csv_file)
            gpkg_path = str(gpkg_file)
            summary_path = str(gpkg_file.with_name(gpkg_file.stem + "_summary.csv"))
            summary_xlsx_path = str(gpkg_file.with_name(gpkg_file.stem + "_summary_report.xlsx"))

            self._log("入力条件を確認しました。")
            self._log("CSV：{}".format(csv_path))
            self._log("GeoPackage：{}".format(gpkg_path))

            analysis_mode = self.analysis_mode_combo.currentData()
            catchment_analysis = analysis_mode == "catchment"
            planning_analysis = analysis_mode in ("team_all", "team_coverage")
            start_points = self._start_points(network)
            destinations = []
            if planning_analysis:
                if len(start_points) != 1:
                    raise ValueError(
                        "巡回計画の拠点は1か所です。「選択した地物のみを使用する」を使う場合は、"
                        "起点レイヤ上で拠点を1地点だけ選択してください。複数選択を解除するか、"
                        "チェックを外して起点リストから1地点を選んでください。"
                    )
                destinations = self._planning_destinations(network, analysis_mode)
            elif not catchment_analysis:
                dest_layer = self._layer(self.dest_layer_combo)
                if dest_layer is None or self.dest_point_combo.currentData() is None:
                    raise ValueError("目的地レイヤと目的地となる地点を選択してください。")
                end_pt, end_id, end_name = self._get_point(
                    dest_layer, self.dest_point_combo.currentData(), network
                )
                end_feature = dest_layer.getFeature(end_id)
                start_name_field = self.origin_name_field_combo.currentData() or ""
                destination_name_field = self.dest_name_field_combo.currentData() or ""
                end_label = _point_label(
                    end_feature, self.dest_name_field_combo.currentData() or None
                )
            snap_limit = float(self.snap_spin.value())
            snap_check_points = [
                (item[0], item[3], "起点") for item in start_points
            ]
            if planning_analysis:
                snap_check_points.extend(
                    (item["point"], item["label"], "巡回先") for item in destinations
                )
            elif not catchment_analysis:
                snap_check_points.append((end_pt, end_label, "目的地"))
            snap_distances = self._preflight_snap_distances(
                network, snap_check_points
            )
            snap_limit = self._confirm_snap_distance_if_needed(
                snap_distances, snap_limit
            )
            if snap_limit is None:
                return
            distance_catchment = (
                catchment_analysis and self.catchment_limit_combo.currentData() == "distance"
            )
            if distance_catchment:
                preset = {
                    "label": "距離基準（移動速度は不使用）", "kmh": 0.0,
                    "category": "", "definition": "距離上限のため移動速度は使用していません。",
                    "issuer": "", "title": "", "year": "", "page": "", "url": "",
                    "speed_region": "", "speed_road_type": "",
                    "speed_time_period": "", "speed_area_category": "",
                }
            else:
                preset = self._selected_speed()
            if not catchment_analysis or self.catchment_limit_combo.currentData() == "time":
                self._log("速度設定：{}（{:.2f} km/h）".format(preset["label"], preset["kmh"]))
            else:
                self._log("距離基準のため、移動速度は計算に使用しません。")

            if planning_analysis:
                self._log("サマリーCSV：{}".format(summary_path))
                self._log("サマリーExcel：{}".format(summary_xlsx_path))
                self._execute_team_plan(
                    network, start_points[0], destinations, snap_limit, preset,
                    gpkg_path, csv_path, summary_path, summary_xlsx_path, layer_name, analysis_mode,
                )
                return

            if catchment_analysis:
                self._log("サマリーCSV：{}".format(summary_path))
                limit_kind = self.catchment_limit_combo.currentData()
                limit = float(self.catchment_limit_value.value())
                meters_per_cost_unit = (
                    1.0 if limit_kind == "distance"
                    else preset["kmh"] * 1000.0 / 60.0
                )
                max_network_distance = (
                    limit if limit_kind == "distance"
                    else limit * meters_per_cost_unit
                )
                # 各起点から上限距離内に到達し得る範囲だけを読み込む。
                # スナップ距離分も加え、入力点から道路までのずれを含めても範囲漏れを防ぐ。
                search_rect = self._points_extent(
                    [item[0] for item in start_points], max_network_distance + snap_limit
                )
                self._log(
                    "到達圏の上限距離に基づき、起点周辺の道路だけを読み込みます。"
                )
                nodes, adjacency, spatial_index, index_id_to_node = self._build_graph(
                    network, self._log, search_rect=search_rect
                )
                snapped_starts = []
                for start_pt, start_id, start_layer_name, start_label in start_points:
                    start_node, start_snap = self._nearest_node(
                        start_pt, nodes, spatial_index, index_id_to_node
                    )
                    if start_snap > snap_limit:
                        raise ValueError(
                            "起点「{}」を道路に接続できません。起点 {:.1f} m（許容距離 {:.1f} m）。"
                            .format(start_label, start_snap, snap_limit)
                        )
                    snapped_starts.append((
                        start_pt, start_id, start_layer_name, start_label,
                        start_node, start_snap,
                    ))
                self._log("到達圏用の道路グラフ準備完了：{}地点。".format(len(nodes)))
            else:
                self._log("起終点の周辺道路だけを読み込み、経路を探索します。")
                (
                    nodes, adjacency, spatial_index, index_id_to_node,
                    end_node, end_snap, snapped_starts, costs, previous,
                ) = self._build_route_graph(network, start_points, end_pt, snap_limit)

            if catchment_analysis:
                output_preset = dict(preset)
                if limit_kind == "distance":
                    output_preset.update({
                        "kmh": 0.0,
                        "label": "距離基準（移動速度は不使用）",
                        "issuer": "", "title": "", "year": "", "page": "", "url": "",
                        "definition": "距離上限による到達圏解析のため、移動速度は使用していません。",
                        "speed_region": "", "speed_road_type": "",
                        "speed_time_period": "", "speed_area_category": "",
                    })
                origins = snapped_starts
                aggregation = self.catchment_mode_combo.currentData()
                if not self.selected_origins_check.isChecked():
                    self._log("起点レイヤの全地点（{}件）を使用します。".format(len(origins)))
                else:
                    self._log("選択中の起点{}件を使用します。".format(len(origins)))
                if aggregation == "individual":
                    self._log("起点ごとに到達圏を計算します（{}起点）。".format(len(origins)))
                    def individual_reaches():
                        for idx, origin in enumerate(origins):
                            self._log("起点別の探索：{} / {}　{}".format(idx + 1, len(origins), origin[3]))
                            initial = origin[5] / meters_per_cost_unit
                            yield self._dijkstra_reach(
                                [(origin[4], idx, initial)], adjacency, limit,
                                meters_per_cost_unit, self._log,
                            )
                    feature_count = self._write_catchment_outputs(
                        network, nodes, adjacency, individual_reaches(), origins,
                        limit, limit_kind, aggregation, meters_per_cost_unit, output_preset,
                        gpkg_path, csv_path, summary_path, layer_name,
                        release_graph_state,
                    )
                else:
                    self._log("全起点を統合し、いずれかの起点から届く区間を計算します。")
                    seeds = [
                        (origin[4], idx, origin[5] / meters_per_cost_unit)
                        for idx, origin in enumerate(origins)
                    ]
                    costs, owners = self._dijkstra_reach(
                        seeds, adjacency, limit, meters_per_cost_unit, self._log
                    )
                    feature_count = self._write_catchment_outputs(
                        network, nodes, adjacency, [(costs, owners)], origins,
                        limit, limit_kind, aggregation, meters_per_cost_unit, output_preset,
                        gpkg_path, csv_path, summary_path, layer_name,
                        release_graph_state,
                    )
                self._log("完了：到達可能な道路区間{}件を保存しました。".format(feature_count))
                self._log(
                    "QGIS表示用の集約ラインを{}地物で追加しました。"
                    .format(len(origins) if aggregation == "individual" else 1)
                )
                QMessageBox.information(
                    self, self._text("到達圏解析完了"),
                    self._text("到達可能な道路区間明細：{}件\nQGIS表示用ライン：{}地物\n区間CSV：{}\nサマリーCSV：{}\nGeoPackage：{}\n追加レイヤ名：{}{}{}")
                    .format(
                        feature_count, len(origins) if aggregation == "individual" else 1,
                        csv_path, summary_path, gpkg_path, layer_name,
                        "（起点名別の色分け）"
                        if aggregation == "individual" else "",
                        (
                            "\n凸包：起点別凸包、全起点凸包融合"
                            if aggregation == "individual" else "\n凸包：統合到達区間の帰属先別凸包"
                        ),
                    )
                )
                return

            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            profile = preset["label"]
            rows = []
            geometries = []
            for number, (start_pt, start_id, start_layer_name, start_label, start_node, start_snap) in enumerate(snapped_starts, 1):
                self._log("ルートを組み立て中：{} / {}　{}".format(number, len(snapped_starts), start_label))
                coords = self._route_from_tree(start_node, end_node, nodes, previous)
                network_length_m = costs[start_node]
                connector_length_m = start_snap + end_snap
                length_m = network_length_m + connector_length_m
                route_coords = [start_pt] + coords + [end_pt]
                route_geom = QgsGeometry.fromPolylineXY(route_coords)
                time_min = length_m / (preset["kmh"] * 1000.0 / 60.0)
                row = {
                    "run_datetime": timestamp,
                    "analysis_objective": "最短距離",
                    "start_layer": start_layer_name,
                    "start_location": start_label,
                    "start_name_field": start_name_field,
                    "start_record_id": str(start_id),
                    "destination_layer": end_name,
                    "destination_location": end_label,
                    "destination_name_field": destination_name_field,
                    "destination_record_id": str(end_id),
                    "network_layer": network.name(),
                    "network_crs": network.crs().authid(),
                    "distance_m": round(length_m, 2),
                    "network_distance_m": round(network_length_m, 2),
                    "straight_snap_connectors_m": round(connector_length_m, 2),
                    "distance_km": round(length_m / 1000.0, 4),
                    "estimated_time_min": round(time_min, 2),
                    "speed_profile": profile,
                    "speed_category": preset["category"],
                    "speed_kmh": preset["kmh"],
                    "speed_mps": round(preset["kmh"] / 3.6, 4),
                    "speed_region": preset.get("speed_region", ""),
                    "speed_road_type": preset.get("speed_road_type", ""),
                    "speed_time_period": preset.get("speed_time_period", ""),
                    "speed_area_category": preset.get("speed_area_category", ""),
                    "speed_source_issuer": preset["issuer"],
                    "speed_source_title": preset["title"],
                    "speed_source_year": preset["year"],
                    "speed_source_page": preset["page"],
                    "speed_source_url": preset["url"],
                    "speed_definition": preset["definition"],
                    "travel_time_method": "参考時間＝全ルート距離÷選択速度。ルートは最短距離で、時間最短化はしていない。自転車の公道旅行速度は信号待ちを含むため別途加算しない。",
                    "start_snap_m": round(start_snap, 2),
                    "destination_snap_m": round(end_snap, 2),
                    "max_snap_m": snap_limit,
                    "network_assumptions": "ライン頂点間を双方向接続。一方通行・通行規制・交差点遅延は未考慮。起終点スナップ線は直線距離。",
                    "route_wkt": route_geom.asWkt(6),
                }
                rows.append(row)
                geometries.append(route_geom)

            self._log("CSVを書き出しています。")
            self._write_csv(csv_path, rows)
            self._log("GeoPackageレイヤを書き出しています。")
            self._save_result_layer(network, rows, geometries, gpkg_path, layer_name)
            self._log("完了：{}件のルートを保存し、結果レイヤをプロジェクトに追加しました。".format(len(rows)))
            QMessageBox.information(
                self, self._text("解析完了"),
                self._text("{}件のルートを保存しました。\nCSV：{}\nGeoPackage：{}\n追加レイヤ名：{}")
                .format(len(rows), csv_path, gpkg_path, layer_name)
            )
        except Exception as exc:
            self._log("エラー：{}".format(exc))
            QMessageBox.critical(self, self._text("解析できませんでした"), self._text(str(exc)))
        finally:
            self.run_button.setEnabled(True)
            self.cancel_button.setEnabled(True)

    @staticmethod
    def _write_csv(path, rows):
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        if OUTPUT_LANGUAGE == "en":
            rows = [_localized_row(row) for row in rows]
        with output.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _apply_output_line_style(layer, route=False):
        """背景地図上で判別できる線にし、ルート属性があればラベルも設定する。"""
        core_color = "255,53,200,255" if route else "0,210,255,255"
        outline_width = "1.4" if route else "0.8"
        core_width = "0.7" if route else "0.4"
        symbol = QgsLineSymbol()
        symbol.changeSymbolLayer(0, QgsSimpleLineSymbolLayer.create({
            "line_color": "25,25,25,255", "line_width": outline_width,
            "line_width_unit": "MM", "line_style": "solid",
            "joinstyle": "round", "capstyle": "round",
        }))
        symbol.appendSymbolLayer(QgsSimpleLineSymbolLayer.create({
            "line_color": core_color, "line_width": core_width,
            "line_width_unit": "MM", "line_style": "solid",
            "joinstyle": "round", "capstyle": "round",
        }))
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))

        field_names = {field.name() for field in layer.fields()}
        if {"distance_m", "estimated_time_min"}.issubset(field_names):
            settings = QgsPalLayerSettings()
            minute_unit = " min" if OUTPUT_LANGUAGE == "en" else " 分"
            hour_unit = " h" if OUTPUT_LANGUAGE == "en" else " 時間"
            settings.fieldName = (
                "CASE WHEN \"distance_m\" < 1000 "
                "THEN format_number(\"distance_m\", 0) || ' m' "
                "ELSE format_number(\"distance_m\" / 1000.0, 2) || ' km' END "
                "|| '\\n' || CASE WHEN \"estimated_time_min\" < 60 "
                "THEN format_number(\"estimated_time_min\", 1) || '{}' "
                "ELSE format_number(\"estimated_time_min\" / 60.0, 1) || '{}' END"
            ).format(minute_unit, hour_unit)
            settings.isExpression = True
            try:
                settings.placement = Qgis.LabelPlacement.Line
            except AttributeError:
                settings.placement = QgsPalLayerSettings.Line
            text_format = QgsTextFormat()
            text_format.setSize(9)
            text_format.setColor(QColor("#ffffff"))
            buffer = QgsTextBufferSettings()
            buffer.setEnabled(True)
            buffer.setSize(1.0)
            buffer.setColor(QColor("#202020"))
            text_format.setBuffer(buffer)
            settings.setFormat(text_format)
            layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
            layer.setLabelsEnabled(True)
        layer.triggerRepaint()

    def _save_result_layer(self, network, rows, geometries, path, layer_name):
        if OUTPUT_LANGUAGE == "en":
            rows = [_localized_row(row) for row in rows]
        uri = "LineString?crs={}".format(network.crs().authid())
        memory_layer = QgsVectorLayer(uri, layer_name, "memory")
        if not memory_layer.isValid():
            raise ValueError("結果レイヤを作成できませんでした。道路レイヤの座標系を確認してください。")
        field_names = [name for name in rows[0] if name != "route_wkt"]
        fields = []
        for name in field_names:
            value = rows[0][name]
            field_type = FIELD_DOUBLE if isinstance(value, (int, float)) else FIELD_STRING
            fields.append(QgsField(name[:60], field_type))
        provider = memory_layer.dataProvider()
        provider.addAttributes(fields)
        memory_layer.updateFields()
        for row, geom in zip(rows, geometries):
            feature = QgsFeature(memory_layer.fields())
            feature.setGeometry(geom)
            feature.setAttributes([row[name] for name in field_names])
            provider.addFeature(feature)
        memory_layer.updateExtents()

        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        for existing in list(QgsProject.instance().mapLayers().values()):
            source_path = existing.source().split("|")[0]
            try:
                same_path = Path(source_path).resolve() == target_path.resolve()
            except (OSError, RuntimeError):
                same_path = False
            if same_path and existing.name() == layer_name:
                QgsProject.instance().removeMapLayer(existing.id())

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = layer_name
        options.fileEncoding = "UTF-8"
        # 出力先は未作成の一意なGPKGファイルなので、レイヤ上書きではなく
        # ファイル新規作成を指定する。
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            memory_layer, str(target_path), QgsProject.instance().transformContext(), options
        )
        if result[0] != QgsVectorFileWriter.NoError:
            raise ValueError("結果GeoPackageを書き込めませんでした：{}".format(result[1]))

        saved_layer = QgsVectorLayer(
            "{}|layername={}".format(target_path, layer_name), layer_name, "ogr"
        )
        if not saved_layer.isValid():
            raise ValueError("保存したGeoPackageレイヤをQGISに読み込めませんでした。")
        self._apply_output_line_style(saved_layer, route=True)
        QgsProject.instance().addMapLayer(saved_layer)
