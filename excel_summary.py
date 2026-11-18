# -*- coding: utf-8 -*-
"""Dependency-free Japanese Excel summary writer for patrol results."""
import math
import os
import tempfile
import zipfile
from xml.sax.saxutils import escape
from .localization import translate_text


def _column_name(number):
    name = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _cell_xml(reference, value, style):
    style_attr = ' s="{}"'.format(style) if style is not None else ""
    if value is None or value == "":
        return '<c r="{}"{}/>'.format(reference, style_attr)
    if isinstance(value, bool):
        value = "はい" if value else "いいえ"
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return '<c r="{}"{}><v>{}</v></c>'.format(reference, style_attr, value)
    text = escape(str(value))
    return (
        '<c r="{}" t="inlineStr"{}><is><t xml:space="preserve">'
        '{}</t></is></c>'
    ).format(reference, style_attr, text)


def _worksheet_xml(title, rows, widths, table_sheet=True):
    max_columns = max([len(row) for row in rows] or [1])
    last_column = _column_name(max_columns)
    row_xml = []
    for row_number, row in enumerate(rows, 1):
        cells = []
        for column_number, value in enumerate(row, 1):
            if row_number == 1:
                style = 2
            elif table_sheet and row_number == 2:
                style = 1
            elif not table_sheet and row_number == 2:
                style = 1
            elif not table_sheet and column_number == 1:
                style = 3
            else:
                style = 4
            cells.append(_cell_xml("{}{}".format(_column_name(column_number), row_number), value, style))
        height = ' ht="30" customHeight="1"' if row_number == 1 else ""
        row_xml.append('<row r="{}"{}>{}</row>'.format(row_number, height, "".join(cells)))

    cols_xml = "".join(
        '<col min="{}" max="{}" width="{}" customWidth="1"/>'.format(i, i, width)
        for i, width in enumerate(widths, 1)
    )
    views = (
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="2" topLeftCell="A3" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        if table_sheet else
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="2" topLeftCell="A3" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
    )
    auto_filter = (
        '<autoFilter ref="A2:{}{}"/>'.format(last_column, len(rows))
        if table_sheet and len(rows) > 2 else ""
    )
    merges = '<mergeCells count="1"><mergeCell ref="A1:{}1"/></mergeCells>'.format(last_column)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '{}<cols>{}</cols><sheetData>{}</sheetData>{}{}{}</worksheet>'
    ).format(views, cols_xml, "".join(row_xml), auto_filter, merges,
             '<pageMargins left="0.3" right="0.3" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>')


def _styles_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="3"><font><sz val="11"/><name val="Yu Gothic"/></font>
<font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Yu Gothic"/></font>
<font><b/><sz val="16"/><name val="Yu Gothic"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF2F5597"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>
<border><left style="thin"><color rgb="FFD9E2F3"/></left><right style="thin"><color rgb="FFD9E2F3"/></right>
<top style="thin"><color rgb="FFD9E2F3"/></top><bottom style="thin"><color rgb="FFD9E2F3"/></bottom><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="5"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf></cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


def _xml_text(value):
    return escape(str(value), {'"': '&quot;'})


def _workbook_xml(sheets):
    sheet_elements = []
    rels = []
    overrides = []
    for index, (name, _rows, _widths, _table) in enumerate(sheets, 1):
        sheet_elements.append(
            '<sheet name="{}" sheetId="{}" r:id="rId{}"/>'.format(
                _xml_text(name), index, index
            )
        )
        rels.append(
            '<Relationship Id="rId{}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{}.xml"/>'.format(
                index, index
            )
        )
        overrides.append(
            '<Override PartName="/xl/worksheets/sheet{}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'.format(index)
        )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<bookViews><workbookView xWindow="0" yWindow="0" windowWidth="18000" windowHeight="9000"/></bookViews>'
        '<sheets>{}</sheets></workbook>'
    ).format("".join(sheet_elements))
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '{}<Relationship Id="rId{}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    ).format("".join(rels), len(sheets) + 1)
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '{}</Types>'
    ).format("".join(overrides))
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    return workbook, relationships, content_types, root_rels


def _format_number(value, digits=1):
    try:
        value = float(value)
        if math.isfinite(value):
            return round(value, digits)
    except (TypeError, ValueError):
        pass
    return value


def write_patrol_summary(path, run_info, teams, stops, language="ja"):
    """Write a Japanese multi-sheet XLSX from the same rows used by CSV/GPKG."""
    visited = [row for row in stops if row.get("status") == "訪問予定"]
    unvisited = [row for row in stops if row.get("status") == "未訪問"]
    total_sites = int(run_info.get("訪問候補数", len(stops)))
    active_teams = [row for row in teams if int(row.get("stop_count", 0) or 0) > 0]
    within_shift = all(bool(row.get("within_shift")) for row in active_teams)
    total_distance_km = sum(float(row.get("distance_m", 0) or 0) for row in teams) / 1000.0
    total_travel = sum(float(row.get("travel_min", 0) or 0) for row in teams)
    total_service = sum(float(row.get("service_min", 0) or 0) for row in teams)
    total_break = sum(float(row.get("break_min", 0) or 0) for row in teams)
    total_work = sum(float(row.get("work_min", 0) or 0) for row in teams)

    overview_items = [
        ("解析の種類", run_info.get("分析種類", "")),
        ("解析日時", run_info.get("解析日時", "")),
        ("出発拠点", run_info.get("出発拠点", "")),
        ("道路ネットワーク", run_info.get("道路ネットワーク", "")),
        ("道路ネットワークの座標系", run_info.get("座標系", "")),
        ("移動速度", run_info.get("移動速度", "")),
        ("訪問先候補数", total_sites),
        ("訪問予定数", len(visited)),
        ("未訪問数", len(unvisited)),
        ("訪問率", "{:.1f}%".format(len(visited) / total_sites * 100.0 if total_sites else 0.0)),
        ("設定チーム数（調整前→後）", "{} → {}".format(
            run_info.get("設定チーム数（調整前）", run_info.get("設定チーム数", "")),
            run_info.get("設定チーム数（調整後）", run_info.get("設定チーム数", "")))),
        ("訪問を担当したチーム数", len(active_teams)),
        ("1チームあたりの人数", run_info.get("1チームあたりの人数", "")),
        ("行動可能時間（調整前→後）", "{}分 → {}分".format(
            run_info.get("行動可能時間（調整前）", ""),
            run_info.get("行動可能時間（調整後）", run_info.get("行動可能時間", "")))),
        ("チームごとの休憩時間", "{}分".format(run_info.get("休憩時間", ""))),
        ("共通対応時間（調整前→後）", "{}分 → {}分".format(
            run_info.get("共通対応時間（調整前）", ""),
            run_info.get("共通対応時間（調整後）", ""))),
        ("訪問先の対応時間の集計方法", run_info.get("集計単位", "")),
        ("移動距離の合計", "{:.2f} km".format(total_distance_km)),
        ("移動時間の合計", "{:.1f}分".format(total_travel)),
        ("訪問対応時間の合計", "{:.1f}分".format(total_service)),
        ("休憩時間の合計", "{:.1f}分".format(total_break)),
        ("全チームの勤務時間合計", "{:.1f}分".format(total_work)),
        ("各チームの時間上限", "全チーム内" if within_shift else "上限超過あり"),
        ("自動調整の結果", run_info.get("調整内容", "")),
        ("出力レイヤ名", run_info.get("出力レイヤ名", "")),
    ]
    overview = [["巡回計画の全体サマリー"], ["項目", "結果"]]
    overview.extend([[label, value] for label, value in overview_items])

    team_headers = [
        "チーム", "チーム人数", "訪問先数", "訪問先構成比（%）", "対応人数・単位",
        "優先度加重値", "移動距離（km・帰着含む）", "移動時間（分・帰着含む）",
        "訪問対応時間（分）", "休憩時間（分）", "勤務時間（分）",
        "行動可能時間（分）", "残り時間（分）", "時間上限内",
        "訪問順",
    ]
    team_rows = [["チーム別の実績"], team_headers]
    for item in teams:
        count = int(item.get("stop_count", 0) or 0)
        limit = float(item.get("shift_limit_min", run_info.get("行動可能時間", 0)) or 0)
        work = float(item.get("work_min", 0) or 0)
        team_rows.append([
            "チーム{}".format(item.get("team_id", "")), item.get("team_size", 0), count,
            _format_number(item.get("visit_rate_percent", 0), 1),
            _format_number(item.get("people", 0), 1),
            _format_number(item.get("priority_weighted_people", 0), 1),
            _format_number(float(item.get("distance_m", 0) or 0) / 1000.0, 2),
            _format_number(item.get("travel_min", 0), 1),
            _format_number(item.get("service_min", 0), 1),
            _format_number(item.get("break_min", 0), 1),
            _format_number(work, 1), _format_number(limit, 1),
            _format_number(max(0.0, limit - work), 1),
            "はい" if item.get("within_shift") else "いいえ",
            item.get("visit_order", ""),
        ])
    team_rows.append([
        "合計", "", len(visited), "100.0%",
        _format_number(sum(float(item.get("people", 0) or 0) for item in teams), 1),
        _format_number(sum(float(item.get("priority_weighted_people", 0) or 0) for item in teams), 1),
        _format_number(total_distance_km, 2), _format_number(total_travel, 1),
        _format_number(total_service, 1), _format_number(total_break, 1),
        _format_number(total_work, 1), "", "", "", "",
    ])

    visit_headers = [
        "状態", "チーム", "訪問順", "訪問先名", "元レイヤの地物ID",
        "対応人数・単位", "優先度", "対応時間（分）", "直前地点からの移動時間（分）",
        "出発後の到着時刻（分）", "対応終了時刻（分）", "未訪問の理由",
    ]
    visit_rows = [["訪問先ごとの結果"], visit_headers]
    for row in stops:
        visit_rows.append([
            row.get("status", ""), row.get("team_id", ""), row.get("visit_order", ""),
            row.get("origin_location", ""), row.get("origin_record_id", ""),
            row.get("people", ""), row.get("priority", ""),
            _format_number(row.get("service_min", ""), 1),
            _format_number(row.get("travel_from_previous_min", ""), 1),
            _format_number(row.get("arrival_min_from_start", ""), 1),
            _format_number(row.get("service_end_min_from_start", ""), 1),
            row.get("reason", ""),
        ])

    unvisited_headers = ["訪問先名", "元レイヤの地物ID", "対応人数・単位", "優先度", "対応時間（分）", "未訪問の理由"]
    unvisited_rows = [["未訪問先の確認"], unvisited_headers]
    if unvisited:
        for row in unvisited:
            unvisited_rows.append([
                row.get("origin_location", ""), row.get("origin_record_id", ""),
                row.get("people", ""), row.get("priority", ""),
                _format_number(row.get("service_min", ""), 1), row.get("reason", ""),
            ])
    else:
        unvisited_rows.append(["未訪問先はありません。"])

    notes_rows = [
        ["集計項目の見方と注意点"], ["項目", "説明"],
        ["移動距離・移動時間", "チーム別の移動距離と移動時間には、設定がオンの場合、最後の訪問先から拠点へ戻る分を含みます。訪問先一覧の移動時間は、直前の地点から各訪問先までです。"],
        ["勤務時間", "移動時間＋訪問先での対応時間＋休憩時間です。移動時間は選択した速度をルート全体に一律適用した参考値です。"],
        ["対応人数・単位", run_info.get("集計単位", "")],
        ["自動調整", "初期設定と最終設定を全体サマリーに記録します。チーム人数は固定です。共通対応時間の調整は、訪問先ごとの対応時間カラムを選択していない場合に限ります。"],
        ["訪問先の割当", "各訪問先は訪問するか訪問しないかの二択で扱い、訪問先内での部分的な対応人数配分は行いません。"],
        ["最適性", "巡回順は挿入法と2-optによる試作ヒューリスティックです。全体最適を保証しません。"],
        ["道路条件", "一方通行、車両通行規制、時間帯別の道路速度変化、交差点遅延は再現しません。"],
        ["出力レイヤ", "チーム経路レイヤは、少なくとも1件を担当したチームのみ地物を作成します。未使用チームはチーム別集計に0件として表示します。"],
    ]

    sheets = [
        ("全体サマリー", overview, [34, 100], False),
        ("チーム別実績", team_rows, [13, 12, 12, 15, 18, 16, 23, 22, 18, 15, 15, 18, 16, 13, 60], True),
        ("訪問先一覧", visit_rows, [14, 12, 10, 42, 18, 17, 12, 16, 24, 20, 20, 60], True),
        ("未訪問先", unvisited_rows, [42, 18, 17, 12, 16, 65], True),
        ("見方・注意点", notes_rows, [28, 110], False),
    ]
    if language == "en":
        sheets = [
            (translate_text(name, "en"),
             [[translate_text(value, "en") for value in row] for row in rows],
             widths, table_sheet)
            for name, rows, widths, table_sheet in sheets
        ]
    workbook, workbook_rels, content_types, root_rels = _workbook_xml(sheets)
    output = os.path.abspath(str(path))
    directory = os.path.dirname(output) or "."
    if not os.path.isdir(directory):
        os.makedirs(directory)
    fd, temporary_path = tempfile.mkstemp(prefix=".patrol_summary_", suffix=".xlsx", dir=directory)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("_rels/.rels", root_rels)
            archive.writestr("xl/workbook.xml", workbook)
            archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
            archive.writestr("xl/styles.xml", _styles_xml())
            for index, (name, rows, widths, table_sheet) in enumerate(sheets, 1):
                archive.writestr(
                    "xl/worksheets/sheet{}.xml".format(index),
                    _worksheet_xml(name, rows, widths, table_sheet),
                )
        os.replace(temporary_path, output)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
    return output
