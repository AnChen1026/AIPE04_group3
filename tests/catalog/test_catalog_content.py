"""Editorial quality checks run without application/database startup."""
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import re

from scripts.build_demo_catalog import compile_catalog
from scripts.demo_catalog import course_description, course_fields, teacher_fields

DATA = Path(__file__).resolve().parents[2] / 'scripts/data'
SOURCE = json.loads((DATA / 'aicourse-demo.json').read_text())
CURRICULUM = json.loads((DATA / 'piano-curriculum.json').read_text())


def test_catalog_has_four_levels_and_bounded_theme_concentration():
    courses = SOURCE['courses']
    assert len(courses) == 426
    assert Counter(c['level'] for c in courses) == {
        'intro': 107, 'beginner': 107, 'intermediate': 106, 'advanced': 106,
    }
    themes = Counter(c['curriculum_key'] for c in courses)
    assert len(themes) == 80
    assert max(themes.values()) <= 6
    assert len({c['title'] for c in courses}) == 426
    assert len({c['description'] for c in courses}) == 426
    assert len({c['teaching_profile'] for c in courses}) == 426


def test_profiles_match_courses_and_have_unique_names():
    teachers = {t['id']: t for t in SOURCE['teachers']}
    assert len(teachers) == 226
    assert len({t['display_name'] for t in teachers.values()}) == 226
    chinese_given_names = []
    english_names = []
    for teacher in teachers.values():
        name = teacher['display_name'].removesuffix('老師')
        if ' ' in name:
            english_names.append(name.split()[0])
        else:
            chinese_given_names.append(name[1:])
    assert len(chinese_given_names) == len(set(chinese_given_names)) == 170
    assert len(english_names) == len(set(english_names)) == 56
    assert len({t['biography'] for t in teachers.values()}) == 226
    for course in SOURCE['courses']:
        teacher = teachers[course['public_teacher_id'] or course['teacher_id']]
        assert course['teacher_name'] == teacher['display_name']
        assert course['curriculum_key'] == teacher['curriculum_key']
        assert course['title'] in teacher['specialties']
    for teacher in teachers.values():
        fields = teacher_fields(teacher)
        assert len(fields['short_intros']) <= 200
        assert len(fields['expertise']) <= 200
        assert len(fields['teaching_method']) <= 255


def test_details_have_prerequisites_tasks_outcomes_and_lesson_arrangements():
    for course in SOURCE['courses']:
        text = course_description(course)
        for label in ('先備能力：', '課堂重點：', '練習安排：', '成果檢核：', '授課安排：'):
            assert label in text
        assert len(text) <= 1000  # all content is included in course_text embeddings
        assert len(course_fields(course)['style']) <= 100
        for unwanted in ('虛構測試資料', '原型有效期限', '來源課程', '示範老師', '示範教師'):
            assert unwanted not in text
        if course['level'] == 'advanced':
            prerequisite = next(t['prerequisite'] for t in CURRICULUM if t['key'] == course['curriculum_key'])
            assert '零基礎' not in prerequisite
            assert any(skill in prerequisite for skill in ("能", "熟悉", "具", "掌握"))


def test_full_descriptions_do_not_retain_near_duplicate_boilerplate():
    bags = []
    for course in SOURCE['courses']:
        text = re.sub(r'\s+', '', course_description(course))
        bags.append({text[i:i+3] for i in range(len(text)-2)})
    for left, right in combinations(range(len(bags)), 2):
        overlap = len(bags[left] & bags[right]) / len(bags[left] | bags[right])
        assert overlap < .8, (SOURCE['courses'][left]['title'], SOURCE['courses'][right]['title'], overlap)


def test_course_catalog_rebuild_is_deterministic():
    assert compile_catalog(SOURCE, CURRICULUM) == SOURCE


def test_search_scenarios_have_specific_matches_across_levels():
    scenarios = {
        'intro': ['樂齡', '親子', '復學', '聽覺', '五線譜', '到府'],
        'beginner': ['自彈自唱', '台語', '吉他', '司琴', 'Trinity', 'ABRSM'],
        'intermediate': ['R&B', '器樂', '聲樂', 'Bossa', 'MIDI', 'lead sheet'],
        'advanced': ['賦格', '協奏曲', '室內樂', 'LRSM', 'ARSM', 'Bebop', '婚宴', '術科'],
    }
    for level, terms in scenarios.items():
        texts = [c['title'] + course_description(c) for c in SOURCE['courses'] if c['level'] == level]
        for term in terms:
            assert any(term in text for text in texts), (level, term)


def test_lesson_locations_are_diverse_and_match_structured_delivery_modes():
    counts = Counter(c['location_type'] for c in SOURCE['courses'])
    assert counts == {'online': 147, 'studio_or_online': 135, 'studio': 96, 'home_visit': 48}
    for course in SOURCE['courses']:
        if course['location_type'] in {'home_visit', 'studio'}:
            assert course['delivery_mode'] == 'onsite'
            assert course['area']
            assert course['area'] in course['teaching_profile']
        if course['location_type'] == 'online':
            assert course['delivery_mode'] == 'online'
            assert '自備' in course['teaching_profile']
