"""把評分結果畫成「上下對照」的樂譜（MusicXML）。

同一份譜裡兩行：上面是答案（老師的 MIDI），下面是學生這次彈的，每個小節上下對齊，
學生哪裡彈錯、漏掉、多彈、節奏不準，直接用顏色標出來。前端用 OpenSheetMusicDisplay 顯示。

學生的音照評分時的速度（節拍器或學生自己的整體速度）換成拍子，再對齊到格子上。
格子跟答案一樣細，最細到 16 分音符，不會出現 32 分音符。
"""

import copy

from music21 import chord, clef, key, meter, metadata, note, pitch, stream, tempo
from music21.musicxml.m21ToXml import GeneralObjectExporter

# 顏色：前端的圖例要跟這裡一致
COLOR_WRONG = "#d0342c"  # 學生彈錯音高；答案行代表學生沒彈對的音
COLOR_EXTRA = "#e08a00"  # 學生多彈
COLOR_RHYTHM = "#2f6fd0"  # 音高對，但時間跟答案不一樣

# 由粗到細試：答案的音都落在這個格子上，就用這個格子。最細 16 分音符（四分音符的 1/4）
GRID_CHOICES = (1.0, 0.5, 0.25)
GRID_TOLERANCE = 0.15

# 分段對齊：一段至少有幾顆配對到的音才算自己的速度，跟整體速度最多差多少
SEGMENT_MIN_NOTES = 4
SEGMENT_MAX_RATE_CHANGE = 0.15


def _choose_grid(values):
    for grid in GRID_CHOICES:
        if all(abs(value / grid - round(value / grid)) <= GRID_TOLERANCE for value in values):
            return grid
    return GRID_CHOICES[-1]


def _snap(value, grid):
    return round(value / grid) * grid


def _segment_rate(pairs, anchor_time, anchor_beat, default_rate):
    """這一段每秒幾拍：通過段落起點的最小平方法。音太少或差太多（真的忽快忽慢）就用整體速度。"""
    if len(pairs) < SEGMENT_MIN_NOTES:
        return default_rate
    seconds = sum((time - anchor_time) ** 2 for time, _beat in pairs)
    if seconds <= 0:
        return default_rate
    rate = sum((time - anchor_time) * (beat - anchor_beat) for time, beat in pairs) / seconds
    return rate if abs(rate / default_rate - 1) <= SEGMENT_MAX_RATE_CHANGE else default_rate


def _build_part(events, name, time_signature, key_signature, best_clef, grid):
    """events：(拍子位置, 長度, 音高, 顏色)。同一拍的音合成和弦；後一顆音開始時，前一顆就截斷，維持單一聲部。"""
    part = stream.Part()
    part.partName = name
    part.insert(0, best_clef)
    part.insert(0, key_signature)
    part.insert(0, time_signature)

    by_offset = {}
    for offset, length, pitch, color in events:
        by_offset.setdefault(offset, []).append((length, pitch, color))
    offsets = sorted(by_offset)
    for position, offset in enumerate(offsets):
        group = by_offset[offset]
        length = max(item[0] for item in group)
        if position + 1 < len(offsets):
            length = min(length, offsets[position + 1] - offset)
        length = max(length, grid)
        notes = []
        for _length, pitch, color in sorted(group, key=lambda item: item[1]):
            one = note.Note(_spell(pitch, key_signature))
            if color:
                one.style.color = color
            notes.append(one)
        element = notes[0] if len(notes) == 1 else chord.Chord(notes)
        if len(notes) > 1 and all(item.style.color == notes[0].style.color for item in notes):
            element.style.color = notes[0].style.color
        element.quarterLength = length
        part.insert(offset, element)
    # 自己分好小節、補休止符。交給匯出時才補的話，music21 會把休止符標成隱藏，譜上看不到
    part.makeMeasures(inPlace=True)
    part.makeTies(inPlace=True)  # 要先切開跨小節的長音，不然後半段的位置會被當成空的補上休止符
    part.makeRests(fillGaps=True, timeRangeFromBarDuration=True, inPlace=True)
    return part


def _spell(midi_number, key_signature):
    """降記號調裡，把 A# 這類音寫成 Bb，譜比較好讀。"""
    one = pitch.Pitch(midi=midi_number)
    if key_signature.sharps < 0 and one.accidental is not None and one.accidental.name == "sharp":
        one = one.getEnharmonic()
    return one


def build_comparison_musicxml(standard_midi, student_midi, alignment, score_result, title="對照樂譜"):
    """回傳 MusicXML 字串。答案或學生一個音都沒有時回傳 None。"""
    standard_notes = standard_midi["notes"]
    student_notes = student_midi["notes"]
    if not standard_notes or not student_notes:
        return None

    seconds_per_beat = 60.0 / standard_midi["tempo_bpm"]
    first_start = standard_notes[0]["start"]
    standard_offsets = [(item["start"] - first_start) / seconds_per_beat for item in standard_notes]
    standard_lengths = [max(item["duration"] / seconds_per_beat, 0.01) for item in standard_notes]
    # 格子只看音的起點。MIDI 的音長常比記譜短一點（例如 3.8 拍），拿來選格子會變太細，多出假的休止符
    grid = _choose_grid(standard_offsets)

    # 學生的秒數換成答案的拍子：除以評分用的速度比例，再分段對齊。
    # 第一段從第一組配對到的音開始，學生第一個音就落在答案第一個音上；開頭多彈的雜音不會把整行推走。
    # 休止符沒休滿或休太久時，從下一顆音開新的一段，後面彈對的音才不會整段被標成錯
    tempo_ratio = score_result.get("tempo_ratio") or 1.0
    student_seconds_per_beat = seconds_per_beat * tempo_ratio
    standard_to_student = alignment["standard_to_student"]
    student_to_standard = {student_index: standard_index for standard_index, student_index in enumerate(standard_to_student)}
    student_to_standard.pop(-1, None)
    rest_changes = score_result.get("rest_changes") or []
    realign_notes = {change.student_index for change in rest_changes}

    matched = sorted(
        (student_notes[student_index]["start"], standard_offsets[standard_index])
        for student_index, standard_index in student_to_standard.items()
    )
    anchors = [matched[0] if matched else (student_notes[0]["start"], 0.0)]
    for change in rest_changes:
        standard_index = student_to_standard[change.student_index]
        anchor_time = (standard_notes[standard_index]["start"] / seconds_per_beat + change.drift_beats) * student_seconds_per_beat
        anchors.append((anchor_time, standard_offsets[standard_index]))

    # 沒開節拍器時，每段照學生那段自己的速度換算，整段慢慢偏快或偏慢不會被標成時間不對
    follow_student = score_result.get("tempo_source") != "metronome"
    segments = []
    for position, (anchor_time, anchor_beat) in enumerate(anchors):
        next_time = anchors[position + 1][0] if position + 1 < len(anchors) else float("inf")
        pairs = [item for item in matched if anchor_time <= item[0] < next_time]
        rate = _segment_rate(pairs, anchor_time, anchor_beat, 1 / student_seconds_per_beat) if follow_student else 1 / student_seconds_per_beat
        segments.append((anchor_time, anchor_beat, rate))

    def student_offset(item):
        anchor_time, anchor_beat, rate = segments[0]
        for segment in segments:
            if item["start"] >= segment[0]:
                anchor_time, anchor_beat, rate = segment
        return max(0.0, _snap(anchor_beat + (item["start"] - anchor_time) * rate, grid))

    standard_snapped = [_snap(value, grid) for value in standard_offsets]

    # 沒配到的答案音，如果學生在同一個位置（前後一格內）彈了別的音，就當成「彈錯音高」，不是漏彈＋多彈
    matched_student = {index for index in standard_to_student if index != -1}
    extra_indexes = [index for index in range(len(student_notes)) if index not in matched_student]
    wrong_student = set()
    for standard_index, student_index in enumerate(standard_to_student):
        if student_index != -1:
            continue
        for candidate in extra_indexes:
            if candidate in wrong_student:
                continue
            if abs(student_offset(student_notes[candidate]) - standard_snapped[standard_index]) <= grid:
                wrong_student.add(candidate)
                break

    standard_events = []
    for index, item in enumerate(standard_notes):
        color = COLOR_WRONG if standard_to_student[index] == -1 else None
        standard_events.append((standard_snapped[index], _snap(standard_lengths[index], grid) or grid, item["pitch"], color))

    student_events = []
    for index, item in enumerate(student_notes):
        offset = student_offset(item)
        length = _snap(item["duration"] / student_seconds_per_beat, grid) or grid
        if index in student_to_standard:
            on_time = offset == standard_snapped[student_to_standard[index]] and index not in realign_notes
            color = None if on_time else COLOR_RHYTHM
        elif index in wrong_student:
            color = COLOR_WRONG
        else:
            color = COLOR_EXTRA
        student_events.append((offset, length, item["pitch"], color))

    ratio = f"{standard_midi['beats_per_bar']}/{standard_midi['beat_unit']}"
    # 調號依答案的音判斷；兩行用同一個譜號，上下才好對照
    reference = stream.Stream([note.Note(midi=item["pitch"]) for item in standard_notes])
    sharps = reference.analyze("key").sharps
    best_clef = clef.bestClef(reference)

    def part(events, name):
        return _build_part(events, name, meter.TimeSignature(ratio), key.KeySignature(sharps), copy.deepcopy(best_clef), grid)

    answer = part(standard_events, "答案")
    answer.insert(0, tempo.MetronomeMark(number=round(standard_midi["tempo_bpm"])))
    score = stream.Score()
    score.metadata = metadata.Metadata(title=title)
    score.insert(0, answer)
    score.insert(0, part(student_events, "你的演奏"))
    return GeneralObjectExporter(score).parse().decode("utf-8")
