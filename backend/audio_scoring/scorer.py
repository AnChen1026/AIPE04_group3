"""網站用的評分入口：一筆錄音對一份參考 MIDI，回傳音高、節奏與文字回饋。

流程沿用 midi_test.py 的步驟。這裡不印東西，中間檔放在暫存資料夾，用完就刪。
音訊套件很重，所以等到真的要評分時才載入，網站啟動不受影響。
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path


class ScoringFailed(Exception):
    """這次錄音沒辦法評分。呼叫端要記成失敗，不能當成 0 分。"""


@dataclass
class ScoringResult:
    pitch_score: float
    rhythm_score: float
    feedback_text: str


def score_recording(midi_path: str | Path, audio_path: str | Path) -> ScoringResult:
    from backend.audio_scoring import midi_test

    midi_path = Path(midi_path)
    audio_path = Path(audio_path)
    if not midi_path.is_file():
        raise ScoringFailed("找不到這門課的參考 MIDI。")
    if not audio_path.is_file():
        raise ScoringFailed("找不到這次的錄音檔。")

    try:
        with tempfile.TemporaryDirectory(prefix="aipe04_scoring_") as work_dir:
            processed_path = Path(work_dir) / "processed.wav"
            converted_path = Path(work_dir) / "converted.mid"
            midi_test.preprocess_audio(audio_path, processed_path)
            midi_test.convert_audio_to_midi(processed_path, converted_path)
            standard_midi = midi_test.read_midi_notes(midi_path, "標準答案")
            student_midi = midi_test.read_midi_notes(converted_path, "學生演奏")
    except Exception as error:
        raise ScoringFailed("讀不到這段錄音的內容，可能是格式不支援或檔案損壞。") from error

    if standard_midi["note_count"] == 0:
        raise ScoringFailed("參考 MIDI 裡沒有音符。")
    if student_midi["note_count"] == 0:
        # 一個音都沒聽到時，分數沒有意義，記成失敗而不是 0 分
        raise ScoringFailed("這段錄音聽不出彈奏的音。")

    alignment = midi_test.align_notes_with_dtw(standard_midi["notes"], student_midi["notes"])
    score_result = midi_test.score_performance(standard_midi, student_midi, alignment)
    report = midi_test.build_score_report(midi_path, audio_path, standard_midi, student_midi, score_result)

    feedback_text, _ = midi_test.generate_feedback(report)
    if not feedback_text:
        feedback_text = _plain_feedback(report, midi_test.PITCH_SCORE_MAX, midi_test.RHYTHM_SCORE_MAX)

    return ScoringResult(
        pitch_score=report.pitch_score,
        rhythm_score=report.rhythm_score,
        feedback_text=feedback_text,
    )


def _plain_feedback(report, pitch_max: int, rhythm_max: int) -> str:
    """沒有設定 Gemini 或呼叫失敗時，只用這次評分結果寫一段簡短說明。"""
    lines = [
        f"這次彈對 {report.correct_pitch_count} / {report.standard_note_count} 個音，"
        f"漏掉 {report.missing_notes} 個，多彈 {report.extra_notes} 個。",
        f"音高 {report.pitch_score} / {pitch_max} 分，節奏 {report.rhythm_score} / {rhythm_max} 分。",
    ]
    problem_measures = [
        summary.measure_number
        for summary in report.measures
        if summary.missing_notes or summary.wrong_notes or summary.extra_notes
    ]
    if problem_measures:
        shown = "、".join(str(number) for number in problem_measures[:5])
        lines.append(f"可以先回頭練第 {shown} 小節。")
    return "\n".join(lines)
