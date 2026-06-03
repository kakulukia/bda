from dataclasses import dataclass

from django.conf import settings


def graph_end_age(graph):
    current_age = max(graph.age or 0, 0)
    life_expectancy = graph_life_expectancy(graph)
    if life_expectancy is None:
        return current_age
    return max(current_age, life_expectancy)


def graph_life_expectancy(graph):
    if not getattr(graph, 'gender', None):
        return None

    expectancies = getattr(settings, 'LIFE_EXPECTANCY_BY_GENDER', {})
    return expectancies.get(graph.gender)


def effective_age_to(entry, following_entries):
    if entry.age_to > entry.age_from:
        return entry.age_to

    for following_entry in following_entries:
        if following_entry.age_from > entry.age_from:
            return following_entry.age_from

    return entry.age_from


@dataclass
class RenderedTimelineEntry:
    graph: object
    age_from: float
    age_to: float
    living_space: float
    number_of_people: int
    description: str = ''
    is_future: bool = False
    source_id: str = ''
    is_gap: bool = False
    is_projection: bool = False

    def __getitem__(self, key):
        return getattr(self, key)

    @property
    def id(self):
        if self.source_id:
            return self.source_id
        return f'{self.age_from:.2f}-{self.age_to:.2f}'

    @property
    def num_years(self):
        return self.age_to - self.age_from

    @property
    def years(self):
        diff = self.num_years
        if diff == 0:
            diff = 0.25
        return float(diff) / 0.8

    @property
    def small_entry(self):
        return 'small-entry' if not bool(self.age_to - self.age_from) else ''

    @property
    def age(self):
        if self.age_from is None:
            return ''
        return self.age_from or 'Baby'

    @property
    def percentage(self):
        if not self.living_space:
            return 0
        max_value = self.graph.max_space(stretched=getattr(self.graph, '_stretched', False))
        if not max_value:
            return 0
        return int(float(self.living_space) / float(max_value) * 100)

    @property
    def future(self):
        return 'future' if self.is_future else ''

    @property
    def person_percentage(self):
        if self.number_of_people:
            return int(float(100) / float(self.number_of_people))
        return 0

    @property
    def person_space(self):
        if self.number_of_people:
            return float(self.living_space) / float(self.number_of_people)
        return 0


def build_timeline_entries(
    graph,
    *,
    include_gaps=True,
    split_current_age=False,
    project_to_end_age=False,
):
    if graph.age is None:
        return []

    current_age = max(graph.age, 0)
    end_age = graph_end_age(graph)
    entries = list(graph.entries.order_by('age_from'))
    rendered = []
    last_age = 0
    latest_entry = None
    latest_age_to = 0

    for entry_index, entry in enumerate(entries):
        age_from = entry.age_from
        if entry_index == 0:
            age_from = 0

        age_to = min(effective_age_to(entry, entries[entry_index + 1:]), end_age)
        if age_to <= age_from:
            continue

        latest_entry = entry
        latest_age_to = max(latest_age_to, age_to)

        if include_gaps and age_from > last_age:
            rendered.append(
                _rendered_entry(
                    graph,
                    None,
                    last_age,
                    age_from,
                    0,
                    0,
                    '',
                    is_future=last_age >= current_age,
                    source_id=f'gap-{last_age:.2f}-{age_from:.2f}',
                    is_gap=True,
                )
            )

        part_ranges = [(age_from, age_to)]
        if split_current_age and age_from < current_age < age_to:
            part_ranges = [(age_from, current_age), (current_age, age_to)]

        for part_index, (part_from, part_to) in enumerate(part_ranges):
            rendered.append(
                _rendered_entry(
                    graph,
                    entry,
                    part_from,
                    part_to,
                    entry.living_space or 0,
                    entry.number_of_people or 0,
                    entry.description if part_index == 0 else '',
                    is_future=part_from >= current_age,
                    source_id=f'entry-{entry.pk}-{part_index}',
                )
            )

        last_age = max(last_age, age_to)

    if project_to_end_age and latest_entry and current_age < end_age and latest_age_to >= current_age and latest_age_to < end_age:
        projection_from = max(current_age, latest_age_to)
        if projection_from < end_age:
            rendered.append(
                _rendered_entry(
                    graph,
                    latest_entry,
                    projection_from,
                    end_age,
                    latest_entry.living_space or 0,
                    latest_entry.number_of_people or 0,
                    '',
                    is_future=True,
                    source_id=f'projection-{projection_from:.2f}-{end_age:.2f}',
                    is_projection=True,
                )
            )

    return rendered


def build_svg_axis_ages(graph, segments):
    ages = set()
    end_age = graph_end_age(graph)
    current_age = max(graph.age or 0, 0)
    if current_age:
        ages.add(current_age)
    for segment in segments:
        ages.add(segment.age_from)
        ages.add(segment.age_to)
    return sorted(
        age for age in ages
        if age is not None and age > 0 and age < end_age
    )


def build_svg_description_ages(segments):
    ages = {
        segment.age_from
        for segment in segments
        if segment.description and segment.age_from is not None and segment.age_from > 0
    }
    return sorted(ages)


def _rendered_entry(
    graph,
    _source_entry,
    age_from,
    age_to,
    living_space,
    number_of_people,
    description,
    *,
    is_future,
    source_id,
    is_gap=False,
    is_projection=False,
):
    return RenderedTimelineEntry(
        graph=graph,
        age_from=age_from,
        age_to=age_to,
        living_space=living_space,
        number_of_people=number_of_people,
        description=description,
        is_future=is_future,
        source_id=source_id,
        is_gap=is_gap,
        is_projection=is_projection,
    )
