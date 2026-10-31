"""音訊評分的規則：濾掉泛音假音、節拍器速度、突然變快變慢、上下對照樂譜。

不跑真正的音訊辨識，直接用音符列表測。
"""

import re

import pytest

pytest.importorskip("basic_pitch")
pytest.importorskip("music21")

from backend.audio_scoring import midi_test, scorer  # noqa: E402
from backend.audio_scoring.score_sheet import (  # noqa: E402
    COLOR_EXTRA,
    COLOR_RHYTHM,
    COLOR_WRONG,
    build_comparison_musicxml,
)

BPM = 120.0
BEAT = 60.0 / BPM


def _note(pitch, start, duration=0.45, amplitude=0.8):
    return {
        "pitch": pitch,
        "pitch_name": midi_test.pretty_midi.note_number_to_name(pitch),
        "start": round(start, 4),
        "end": round(start + duration, 4),
        "duration": duration,
        "amplitude": amplitude,
        "velocity": int(amplitude * 127),
    }


def _midi(notes):
    return {
        "notes": notes,
        "note_count": len(notes),
        "tempo_bpm": BPM,
        "time_signature": "4/4",
        "beats_per_bar": 4,
        "beat_unit": 4,
    }


def _scale(count=16, beats=1.0, scale=1.0, offset=0.0):
    """C 大調音階往上，每顆 beats 拍；scale 是速度倍數（2 代表慢一倍）。"""
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]
    return [
        _note(pitches[index % len(pitches)], offset + index * beats * BEAT * scale, duration=beats * BEAT * scale * 0.9)
        for index in range(count)
    ]


def _score(standard, student, metronome_bpm=None):
    standard_midi, student_midi = _midi(standard), _midi(student)
    alignment = midi_test.align_notes_with_dtw(standard, student)
    return standard_midi, student_midi, alignment, midi_test.score_performance(
        standard_midi, student_midi, alignment, metronome_bpm
    )


def test_泛音與殘響會被濾掉_真的多彈留下():
    main = _note(65, 1.0, duration=0.5, amplitude=0.8)  # F4
    overtone = _note(84, 1.02, duration=0.2, amplitude=0.28)  # 高 19 個半音、小聲：泛音
    ghost = _note(67, 1.2, duration=0.1, amplitude=0.3)  # 很小聲又很短：殘響
    real_extra = _note(67, 1.2, duration=0.3, amplitude=0.75)  # 大聲：真的多彈
    far_away = _note(100, 3.0, amplitude=0.9)  # 遠超過答案音域

    kept = midi_test.remove_false_notes([main, overtone, ghost, real_extra, far_away], (60, 72))
    assert kept == [main, real_extra]
    # 沒給答案音域時不限制音域
    assert far_away in midi_test.remove_false_notes([far_away], None)


def test_沒開節拍器照學生自己的速度_開了照節拍器():
    standard = _scale()
    slow_but_steady = _scale(scale=1.5)  # 整首都慢 1.5 倍、但很穩：80 BPM

    *_, result = _score(standard, slow_but_steady)
    assert result["tempo_source"] == "student"
    assert result["rhythm_score"] == midi_test.RHYTHM_SCORE_MAX
    assert result["played_bpm"] == pytest.approx(80, abs=1)

    # 開了 80 BPM 的節拍器、照著彈：滿分
    *_, result = _score(standard, slow_but_steady, metronome_bpm=80)
    assert result["tempo_source"] == "metronome"
    assert result["rhythm_score"] == midi_test.RHYTHM_SCORE_MAX

    # 開了 120 BPM 的節拍器、卻彈成 80：節奏拿不到分
    *_, result = _score(standard, slow_but_steady, metronome_bpm=120)
    assert result["rhythm_score"] == 0


def test_中間突然變快會扣分_也會指出在哪幾小節():
    standard = _scale(count=24)
    # 前 8 顆和後 8 顆照 65 BPM 左右彈，中間 8 顆突然用 120 BPM
    slow = BPM / 65
    student = []
    time = 0.0
    for index, item in enumerate(standard):
        student.append(_note(item["pitch"], time, duration=0.3))
        time += BEAT * (1.0 if 8 <= index < 16 else slow)

    *_, result = _score(standard, student)
    assert result["rhythm_score"] < midi_test.RHYTHM_SCORE_MAX * 0.75
    changes = result["tempo_changes"]
    assert len(changes) == 1
    assert changes[0].direction == "faster"
    assert changes[0].start_measure == 3
    assert changes[0].factor == pytest.approx(1.8, abs=0.2)


def test_多彈不扣分():
    standard = _scale()
    student = _scale() + [_note(90, 2.0, amplitude=0.9), _note(91, 4.0, amplitude=0.9)]
    student.sort(key=midi_test.note_sort_key)
    *_, result = _score(standard, student)
    assert result["extra_notes"] == 2
    assert result["pitch_score"] == midi_test.PITCH_SCORE_MAX
    assert result["rhythm_score"] == midi_test.RHYTHM_SCORE_MAX


def test_對照樂譜上下兩行_顏色標出彈錯多彈與節奏_不會出現32分音符():
    standard = _scale(count=8)
    student = [dict(item) for item in standard]
    student[2] = _note(63, student[2]["start"])  # 彈錯音高（E 彈成 Eb）
    student[5] = _note(student[5]["pitch"], student[5]["start"] + 0.27)  # 晚了大約半拍
    student.append(_note(84, 1.06, duration=0.05, amplitude=0.9))  # 多彈、又很短
    student.sort(key=midi_test.note_sort_key)

    xml = build_comparison_musicxml(*_score(standard, student))
    assert xml is not None
    assert re.findall(r"<part-name>([^<]*)</part-name>", xml) == ["答案", "你的演奏"]
    colors = set(re.findall(r'<note color="(#[0-9A-F]+)"', xml))
    assert {COLOR_WRONG.upper(), COLOR_EXTRA.upper(), COLOR_RHYTHM.upper()} <= colors
    assert "<type>32nd</type>" not in xml
    # 答案都是四分音符，學生的譜也只對齊到四分音符（跟答案一樣細）
    assert "<type>16th</type>" not in xml
    assert "<type>eighth</type>" not in xml


def test_交給LLM的內容_全對時沒有問題_滿分寫清楚():
    standard = _scale()
    standard_midi, student_midi, alignment, result = _score(standard, _scale())
    report = midi_test.build_score_report("a.mid", "b.wav", standard_midi, student_midi, result)
    assert report.problems == []
    data = midi_test.json.loads(midi_test.feedback_input(report))
    assert data["節奏分數"] == "30 / 30（滿分）"
    assert data["problems"] == []


def test_交給LLM的內容_列出真正的問題():
    standard = _scale(count=24)
    slow = BPM / 65
    student, time = [], 0.0
    for index, item in enumerate(standard):
        if index == 2:
            time += BEAT * slow
            continue  # 漏彈第 3 顆
        student.append(_note(item["pitch"], time, duration=0.3))
        time += BEAT * (1.0 if 8 <= index < 16 else slow)
    standard_midi, student_midi, alignment, result = _score(standard, student)
    report = midi_test.build_score_report("a.mid", "b.wav", standard_midi, student_midi, result)
    assert report.problems[0] == "第 1 小節有漏掉或彈錯的音"
    assert any("突然變快" in item for item in report.problems)
    assert "滿分" not in midi_test.feedback_input(report).split("節奏分數")[1].split("\n")[0]


def test_規則產生的回饋不寫分數():
    standard = _scale()
    standard_midi, student_midi, alignment, result = _score(standard, _scale())
    report = midi_test.build_score_report("a.mid", "b.wav", standard_midi, student_midi, result)
    text = scorer._plain_feedback(report)
    assert "/ 70" not in text and "/ 30" not in text and "音高" not in text
