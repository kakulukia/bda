# -*- coding: utf-8 -*-
import base64
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings


TOTAL_FILL = '#b4b4b4'
PERSON_FILL = '#000000'
FUTURE_FILL = '#fce903'
FUTURE_TOTAL_FILL = '#fefac0'
LINE_FILL = '#444444'

YEARS_MAX = 100
MM_PER_YEAR = 5
MM_PER_SQUARE_METER = 1

TOP_MARGIN = 25
RIGHT_MARGIN = 90
BOTTOM_MARGIN = 30
LEFT_MARGIN = 45
MIN_X_EXTENT = 60
DESCRIPTION_GAP = 4


def render_area_bio_svg(graph):
    segments = _build_segments(graph)
    max_living_space = max([segment['living_space'] for segment in segments] + [0])
    max_person_space = max([segment['person_space'] for segment in segments] + [0])
    x_extent = max(max_living_space / 2, max_person_space / 2, MIN_X_EXTENT)
    graph_height = YEARS_MAX * MM_PER_YEAR
    width = LEFT_MARGIN + x_extent * 2 + RIGHT_MARGIN
    height = TOP_MARGIN + graph_height + BOTTOM_MARGIN
    center_x = LEFT_MARGIN + x_extent
    graph_top = TOP_MARGIN
    graph_bottom = TOP_MARGIN + graph_height

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt(width)}mm" '
            f'height="{_fmt(height)}mm" viewBox="0 0 {_fmt(width)} {_fmt(height)}" '
            'role="img" aria-labelledby="title desc">'
        ),
        f'<title id="title">{escape(str(graph))}</title>',
        '<desc id="desc">Wohnbiografie als maßstäbliches SVG-Diagramm.</desc>',
        '<defs>',
        '<style><![CDATA[',
        _font_css(),
        '.label{font-family:"Gravity Condensed",Arial,sans-serif;font-size:4px;font-weight:700;fill:#292b2c;}',
        '.title{font-family:"Gravity Wide",Arial,sans-serif;font-size:7px;font-weight:700;fill:#000;}',
        '.axis{stroke:#444;stroke-width:.3;}',
        '.axis-light{stroke:#c7c7c7;stroke-width:.25;}',
        ']]></style>',
        '</defs>',
        f'<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text class="title" x="{_fmt(LEFT_MARGIN)}" y="12">{escape(str(graph))}</text>',
    ]

    for age in _axis_ages(segments, graph.age):
        y = _age_to_y(age, graph_top)
        line_class = 'axis' if age in (0, YEARS_MAX) else 'axis-light'
        parts.append(
            f'<line class="{line_class}" x1="{_fmt(LEFT_MARGIN)}" y1="{_fmt(y)}" '
            f'x2="{_fmt(width - RIGHT_MARGIN)}" y2="{_fmt(y)}"/>'
        )
        parts.append(
            f'<text class="label" text-anchor="end" x="{_fmt(LEFT_MARGIN - 2)}" '
            f'y="{_fmt(y + 1.3)}">{_age_label(age)}</text>'
        )

    parts.append(
        f'<line class="axis" x1="{_fmt(center_x)}" y1="{_fmt(graph_top)}" '
        f'x2="{_fmt(center_x)}" y2="{_fmt(graph_bottom)}"/>'
    )

    chart_right = width - RIGHT_MARGIN
    for segment in segments:
        parts.extend(_segment_rects(segment, center_x, graph_top, chart_right))

    parts.extend(_x_axis_labels(center_x, graph_bottom, max_living_space, max_person_space))
    parts.append('</svg>')
    return '\n'.join(parts)


def _build_segments(graph):
    if graph.age is None:
        return []

    birth_year = graph.get_birth_year()
    current_age = min(max(graph.age, 0), YEARS_MAX)
    entries = list(graph.entries.order_by('year_from'))
    segments = []
    latest_entry = None
    latest_age_to = 0

    for entry_index, entry in enumerate(entries):
        age_from = max(entry.year_from - birth_year, 0)
        if entry_index == 0:
            age_from = 0
        year_to = _effective_year_to(entry, entries[entry_index + 1:])
        age_to = min(year_to - birth_year, YEARS_MAX)
        if age_to <= age_from:
            continue

        latest_entry = entry
        latest_age_to = max(latest_age_to, age_to)
        split_points = [age_from, age_to]
        if age_from < current_age < age_to:
            split_points.insert(1, current_age)

        for split_index in range(len(split_points) - 1):
            split_from = split_points[split_index]
            split_to = split_points[split_index + 1]
            if split_to <= split_from:
                continue
            segments.append(
                _segment(
                    entry,
                    split_from,
                    split_to,
                    split_from >= current_age,
                    show_description=split_index == 0,
                )
            )

    if latest_entry and current_age < YEARS_MAX and latest_age_to < YEARS_MAX:
        projection_from = max(current_age, latest_age_to)
        if projection_from < YEARS_MAX:
            segments.append(
                _segment(latest_entry, projection_from, YEARS_MAX, True, show_description=False)
            )

    return segments


def _segment(entry, age_from, age_to, future, show_description):
    living_space = max(entry.living_space or 0, 0) * MM_PER_SQUARE_METER
    person_space = 0
    if entry.number_of_people:
        person_space = living_space / entry.number_of_people
    return {
        'age_from': age_from,
        'age_to': age_to,
        'living_space': living_space,
        'person_space': person_space,
        'future': future,
        'description': entry.description if show_description else '',
    }


def _effective_year_to(entry, following_entries):
    if entry.year_to > entry.year_from:
        return entry.year_to

    for following_entry in following_entries:
        if following_entry.year_from > entry.year_from:
            return following_entry.year_from

    return entry.year_from


def _segment_rects(segment, center_x, graph_top, chart_right):
    y = _age_to_y(segment['age_to'], graph_top)
    height = (segment['age_to'] - segment['age_from']) * MM_PER_YEAR
    fill = FUTURE_TOTAL_FILL if segment['future'] else TOTAL_FILL
    person_fill = FUTURE_FILL if segment['future'] else PERSON_FILL
    parts = [
        _rect(
            center_x - segment['living_space'] / 2,
            y,
            segment['living_space'],
            height,
            fill,
            'total',
            segment,
        )
    ]
    if segment['person_space']:
        parts.append(
            _rect(
                center_x - segment['person_space'] / 2,
                y,
                segment['person_space'],
                height,
                person_fill,
                'personal',
                segment,
            )
        )
    if segment['description']:
        parts.extend(_description_label(segment, center_x, graph_top, chart_right))
    return parts


def _description_label(segment, center_x, graph_top, chart_right):
    y = _age_to_y(segment['age_from'], graph_top)
    line_start = min(center_x + segment['living_space'] / 2 + 1, chart_right)
    line_end = chart_right
    label_x = line_end + DESCRIPTION_GAP
    return [
        f'<line class="axis-light" data-kind="description-line" data-age="{_fmt(segment["age_from"])}" '
        f'x1="{_fmt(line_start)}" y1="{_fmt(y)}" x2="{_fmt(line_end)}" y2="{_fmt(y)}"/>',
        f'<text class="label" data-kind="description" data-age="{_fmt(segment["age_from"])}" '
        f'x="{_fmt(label_x)}" y="{_fmt(y + 1.3)}">{escape(segment["description"])}</text>',
    ]


def _rect(x, y, width, height, fill, kind, segment):
    return (
        f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(width)}" height="{_fmt(height)}" '
        f'fill="{fill}" data-kind="{kind}" data-age-from="{_fmt(segment["age_from"])}" '
        f'data-age-to="{_fmt(segment["age_to"])}" shape-rendering="crispEdges"/>'
    )


def _axis_ages(segments, current_age):
    ages = {0, YEARS_MAX}
    if current_age:
        ages.add(min(max(current_age, 0), YEARS_MAX))
    for segment in segments:
        ages.add(segment['age_from'])
        ages.add(segment['age_to'])
    return sorted(ages)


def _x_axis_labels(center_x, graph_bottom, max_living_space, max_person_space):
    if not max_living_space and not max_person_space:
        return []

    y = graph_bottom
    parts = [
        f'<line class="axis" data-kind="x-axis-total" x1="{_fmt(center_x - max_living_space / 2)}" y1="{_fmt(y)}" '
        f'x2="{_fmt(center_x + max_living_space / 2)}" y2="{_fmt(y)}"/>',
        f'<text class="label" text-anchor="middle" x="{_fmt(center_x)}" '
        f'y="{_fmt(y + 5)}">{_space_label(max_living_space)}</text>',
    ]
    if round(max_person_space, 2) != round(max_living_space, 2):
        y_person = y + 11
        parts.extend([
            f'<line class="axis-light" data-kind="x-axis-personal" x1="{_fmt(center_x - max_person_space / 2)}" y1="{_fmt(y_person)}" '
            f'x2="{_fmt(center_x + max_person_space / 2)}" y2="{_fmt(y_person)}"/>',
            f'<text class="label" text-anchor="middle" x="{_fmt(center_x)}" '
            f'y="{_fmt(y_person + 5)}">{_space_label(max_person_space)}</text>',
        ])
    return parts


def _age_to_y(age, graph_top):
    return graph_top + (YEARS_MAX - age) * MM_PER_YEAR


def _age_label(age):
    return f'{_number_label(age)} Jahre'


def _space_label(value):
    return f'{_number_label(value)} m²'


def _number_label(value):
    if float(value).is_integer():
        return str(int(value))
    return f'{value:.1f}'.rstrip('0').rstrip('.')


def _fmt(value):
    return f'{value:.2f}'


@lru_cache(maxsize=1)
def _font_css():
    wide = _font_data('ABCGravity-Wide.otf')
    condensed = _font_data('ABCGravity-Condensed.otf')
    return (
        '@font-face{font-family:"Gravity Wide";src:url(data:font/otf;base64,'
        + wide
        + ') format("opentype");font-weight:700;}'
        + '@font-face{font-family:"Gravity Condensed";src:url(data:font/otf;base64,'
        + condensed
        + ') format("opentype");font-weight:700;}'
    )


def _font_data(filename):
    path = Path(settings.BASE_DIR) / 'assets' / 'fonts' / filename
    return base64.b64encode(path.read_bytes()).decode('ascii')
