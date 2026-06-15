# -*- coding: utf-8 -*-
import base64
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings

from areas.rendering import build_svg_axis_ages, build_svg_description_ages, build_timeline_entries


TOTAL_FILL = '#b4b4b4'
PERSON_FILL = '#000000'
FUTURE_FILL = '#fce903'
FUTURE_TOTAL_FILL = '#fefac0'
LINE_FILL = '#444444'

MM_PER_YEAR = 5
MM_PER_SQUARE_METER = 1

TOP_MARGIN = 25
RIGHT_MARGIN = 90
BOTTOM_MARGIN = 30
LEFT_MARGIN = 45
MIN_X_EXTENT = 60
DESCRIPTION_GAP = 4
Y_AXIS_TICK_LENGTH = 5

# Client asked to treat the previous 4px rendering as 11.3pt and scale it to 15pt.
LABEL_FONT_SCALE = 15 / 11.3
LABEL_FONT_SIZE = 4 * LABEL_FONT_SCALE
LABEL_BASELINE_OFFSET = 1.3 * LABEL_FONT_SCALE
X_AXIS_TOTAL_LABEL_OFFSET = 5 * LABEL_FONT_SCALE
X_AXIS_PERSONAL_LINE_OFFSET = 11 * LABEL_FONT_SCALE
X_AXIS_PERSONAL_LABEL_OFFSET = 16 * LABEL_FONT_SCALE


def render_area_bio_svg(graph):
    segments = _build_segments(graph)
    graph_end_age = graph.graph_end_age()
    max_living_space = max([segment['living_space'] for segment in segments] + [0])
    max_person_space = max([segment['person_space'] for segment in segments] + [0])
    x_extent = max(max_living_space / 2, max_person_space / 2, MIN_X_EXTENT)
    graph_height = graph_end_age * MM_PER_YEAR
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
        f'.label{{font-family:"Gravity Condensed",Arial,sans-serif;font-size:{_fmt(LABEL_FONT_SIZE)}px;font-weight:700;fill:#000;}}',
        '.axis{stroke:#444;stroke-width:.3;}',
        '.axis-grid{stroke:#c7c7c7;stroke-width:.25;}',
        '.axis-tick{stroke:#444;stroke-width:.3;}',
        '.area-measure{stroke:#000;stroke-width:.3;}',
        ']]></style>',
        '</defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]

    axis_ages = build_svg_axis_ages(graph, segments)
    for age in build_svg_description_ages(segments):
        y = _age_to_y(age, graph_top, graph_end_age)
        parts.append(
            f'<line class="axis-grid" data-kind="axis-grid" data-age="{_fmt(age)}" '
            f'x1="{_fmt(center_x)}" y1="{_fmt(y)}" '
            f'x2="{_fmt(width - RIGHT_MARGIN)}" y2="{_fmt(y)}"/>'
        )

    chart_right = width - RIGHT_MARGIN
    description_lines = []
    description_texts = []
    description_offsets = {}
    for segment in segments:
        if segment.description:
            offset_index = description_offsets.get(segment.age_from, 0)
            description_offsets[segment.age_from] = offset_index + 1
            description_y_offset = offset_index * LABEL_FONT_SIZE
            description_line, description_text = _description_parts(
                segment,
                center_x,
                graph_top,
                chart_right,
                graph_end_age,
                description_y_offset,
            )
            description_lines.append(description_line)
            description_texts.append(description_text)

    parts.extend(description_lines)

    parts.append(
        f'<line class="axis" x1="{_fmt(center_x)}" y1="{_fmt(graph_top)}" '
        f'x2="{_fmt(center_x)}" y2="{_fmt(graph_bottom)}"/>'
    )

    for age in axis_ages:
        y = _age_to_y(age, graph_top, graph_end_age)
        parts.append(
            f'<line class="axis-tick" data-kind="axis-tick" data-age="{_fmt(age)}" '
            f'x1="{_fmt(LEFT_MARGIN)}" y1="{_fmt(y)}" '
            f'x2="{_fmt(LEFT_MARGIN + Y_AXIS_TICK_LENGTH)}" y2="{_fmt(y)}"/>'
        )
        parts.append(
            f'<text class="label" text-anchor="end" x="{_fmt(LEFT_MARGIN - 2)}" '
            f'y="{_fmt(y + LABEL_BASELINE_OFFSET)}">{_age_label(age)}</text>'
        )

    for segment in segments:
        parts.extend(_segment_rects(segment, center_x, graph_top, chart_right, graph_end_age))

    parts.extend(description_texts)

    parts.extend(_x_axis_labels(center_x, graph_bottom, max_living_space, max_person_space))
    parts.append('</svg>')
    return '\n'.join(parts)


def _build_segments(graph):
    return build_timeline_entries(graph, include_gaps=False, split_current_age=True, project_to_end_age=True)


def _segment_rects(segment, center_x, graph_top, chart_right, graph_end_age):
    y = _age_to_y(segment.age_to, graph_top, graph_end_age)
    height = (segment.age_to - segment.age_from) * MM_PER_YEAR
    fill = FUTURE_TOTAL_FILL if segment.is_future else TOTAL_FILL
    person_fill = FUTURE_FILL if segment.is_future else PERSON_FILL
    parts = [
        _rect(
            center_x - segment.living_space / 2,
            y,
            segment.living_space,
            height,
            fill,
            'total',
            segment,
        )
    ]
    if segment.person_space:
        parts.append(
            _rect(
                center_x - segment.person_space / 2,
                y,
                segment.person_space,
                height,
                person_fill,
                'personal',
                segment,
            )
        )
    return parts


def _description_parts(segment, center_x, graph_top, chart_right, graph_end_age, y_offset=0):
    y = _age_to_y(segment.age_from, graph_top, graph_end_age) + y_offset
    line_start = min(center_x + segment.living_space / 2 + 1, chart_right)
    line_end = chart_right
    label_x = line_end + DESCRIPTION_GAP
    line = (
        f'<line class="axis-grid" data-kind="description-line" data-age="{_fmt(segment.age_from)}" '
        f'x1="{_fmt(line_start)}" y1="{_fmt(y)}" x2="{_fmt(line_end)}" y2="{_fmt(y)}"/>'
    )
    text = (
        f'<text class="label" data-kind="description" data-age="{_fmt(segment.age_from)}" '
        f'x="{_fmt(label_x)}" y="{_fmt(y + LABEL_BASELINE_OFFSET)}">{escape(segment.description)}</text>'
    )
    return line, text


def _rect(x, y, width, height, fill, kind, segment):
    return (
        f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(width)}" height="{_fmt(height)}" '
        f'fill="{fill}" data-kind="{kind}" data-age-from="{_fmt(segment["age_from"])}" '
        f'data-age-to="{_fmt(segment["age_to"])}" shape-rendering="crispEdges"/>'
    )


def _x_axis_labels(center_x, graph_bottom, max_living_space, max_person_space):
    if not max_living_space and not max_person_space:
        return []

    total_label_y = graph_bottom + X_AXIS_TOTAL_LABEL_OFFSET
    personal_line_y = graph_bottom + X_AXIS_PERSONAL_LINE_OFFSET
    personal_label_y = graph_bottom + X_AXIS_PERSONAL_LABEL_OFFSET

    parts = [
        f'<text class="label" data-kind="area-measure-total-label" text-anchor="middle" '
        f'x="{_fmt(center_x)}" y="{_fmt(total_label_y)}">{_space_label(max_living_space)}</text>',
    ]
    if max_person_space:
        parts.extend([
            f'<line class="area-measure" data-kind="area-measure-personal-line" '
            f'x1="{_fmt(center_x - max_person_space / 2)}" y1="{_fmt(personal_line_y)}" '
            f'x2="{_fmt(center_x + max_person_space / 2)}" y2="{_fmt(personal_line_y)}"/>',
            f'<text class="label" data-kind="area-measure-personal-label" text-anchor="middle" '
            f'x="{_fmt(center_x)}" y="{_fmt(personal_label_y)}">{_space_label(max_person_space)}</text>',
        ])
    return parts


def _age_to_y(age, graph_top, graph_end_age):
    return graph_top + (graph_end_age - age) * MM_PER_YEAR


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
