'''
演奏評分測試：目前做到步驟 1～13
1. 準備標準答案 MIDI
2. 準備測試音檔（先用現成檔，不用瀏覽器錄音）
3. 讀取標準答案 MIDI
4. 音訊前處理
5. 把處理後的音檔轉成 MIDI
6. 讀取轉出來的學生 MIDI
7. 用 DTW 把學生音符對到標準答案
8. 比對音高
9. 比對節奏（先估整體速度，再比 IOI 比例）
10. 依標準答案切小節（不支援弱起）
11. 計算整首總分與每小節摘要
12. 用 Pydantic 整理成結構化結果
13. 把結構化結果交給 LLM，產生文字回饋

使用方式：
  1. 把標準答案 MIDI 放到 backend/audio_scoring/midi_test_data/
  2. 把測試音檔放到 backend/audio_scoring/audio_test_data/
  3. 先安裝套件：pip install -r requirements.txt
  4. 若要產生 AI 回饋，在專案根目錄 .env 寫入 GEMINI_API_KEY（或設定 PRACTICE_FEEDBACK_LLM_PROVIDER=openai 與 OPENAI_API_KEY）
  5. 在專案根目錄執行：python backend/audio_scoring/midi_test.py
'''

from pathlib import Path  # 處理檔案路徑，避免自己拼字串
import argparse  # 讀取指令列參數，例如 --midi、--audio
import json  # 把交給 LLM 的內容轉成 JSON 字串
import os  # 設定環境變數，例如 numba 快取目錄、Gemini API key
import shutil  # 找 ffmpeg 在哪裡
import subprocess  # 瀏覽器錄的 webm／m4a 先用 ffmpeg 轉成 wav
import sys  # 結束程式時回傳成功或失敗代碼
import tempfile  # 取得系統暫存資料夾
import time  # 計算整支程式執行秒數

import librosa  # 讀取音檔、轉單聲道、去掉靜音；後面也用來做 DTW
import numpy  # 建立 DTW 需要的成本矩陣
import pretty_midi  # 讀取與解析 MIDI 檔
import soundfile  # 把處理後的音波寫回 wav 檔
from basic_pitch import FilenameSuffix, build_icassp_2022_model_path  # 選 ONNX 模型，避開 TensorFlow
from basic_pitch.inference import predict  # 把音檔轉成 MIDI / 音符
from pydantic import BaseModel  # 步驟 12：把評分結果整理成固定格式

# librosa / numba 需要可寫入的快取目錄，否則轉 MIDI 可能失敗
numba_cache_dir = Path(tempfile.gettempdir()) / "numba_cache"
os.environ.setdefault("NUMBA_CACHE_DIR", str(numba_cache_dir))

# 這個 .py 所在的資料夾（backend/audio_scoring/），用來組相對路徑
BASE_DIR = Path(__file__).resolve().parent
MIDI_DIR = BASE_DIR / "midi_test_data"
AUDIO_DIR = BASE_DIR / "audio_test_data"
PROCESSED_DIR = BASE_DIR / "processed_audio"
CONVERTED_DIR = BASE_DIR / "converted_midi"

# ======================================================
# 步驟 1：標準答案 MIDI（請把檔案放到這個相對路徑）
# ======================================================
MIDI_PATH = MIDI_DIR / "test2.mid"

# ======================================================
# 步驟 2：測試音檔（請把檔案放到這個相對路徑）
# ======================================================
AUDIO_PATH = AUDIO_DIR / "test1.wav"

# 前處理後的音檔，會用這個取樣率存檔
PROCESS_SAMPLE_RATE = 22050

# 檢查副檔名時使用
MIDI_SUFFIXES = {".mid", ".midi"}
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

# 步驟 8、11：音高最多 70 分，必須 MIDI number 完全相同
PITCH_SCORE_MAX = 70

# 步驟 9、11：節奏最多 30 分
RHYTHM_SCORE_MAX = 30

# 節奏誤差門檻：10% 滿分、20% 一半；另外給 50 毫秒的最小容忍
RHYTHM_FULL_RATIO = 0.10
RHYTHM_HALF_RATIO = 0.20
RHYTHM_MIN_TOLERANCE_SECONDS = 0.05

# DTW 時，音高不同的配對成本要明顯比較大
DTW_SAME_PITCH_COST = 1.0
DTW_DIFFERENT_PITCH_COST = 100.0

# 標準 MIDI 沒有 Tempo 時的預設速度
DEFAULT_TEMPO_BPM = 120.0

# 步驟 5：過濾 Basic Pitch 把泛音、殘響當成音符的假音（見開發紀錄 2026-09-29）
# 只保留標準答案音域上下一個八度內的音
PITCH_RANGE_MARGIN = 12
# 同時有一顆比較大聲的音在響，而且剛好高出這些半音數（八度、十二度、兩個八度…），就當成泛音
OVERTONE_INTERVALS = {12, 19, 24, 28, 31, 36}
OVERTONE_MAX_AMPLITUDE_RATIO = 0.6
# 很小聲又很短、旁邊有大聲的音在響：多半是殘響或鍵盤雜音
GHOST_MAX_AMPLITUDE = 0.4
GHOST_MAX_SECONDS = 0.15
GHOST_MAX_AMPLITUDE_RATIO = 0.5
# 判斷「同時在響」時，允許這顆音比較早一點點出現
SOUNDING_EARLY_SECONDS = 0.05

# 步驟 9：找出「突然變快／變慢」的段落。連續幾個間隔都比整體速度快或慢超過這個倍數，就寫進回饋
TEMPO_CHANGE_FACTOR = 1.35
TEMPO_CHANGE_MIN_INTERVALS = 3



# ======================================================
# 步驟 12：評分結果的固定格式
# 之後 LLM 與 API 都讀這個結構，不要再自己拼不固定的 dict
# ======================================================
class ErrorNote(BaseModel):
    """一筆錯音：在第幾小節、是哪個音、發生什麼問題。"""

    measure_number: int
    note_in_measure: int | None = None
    pitch_name: str
    reason: str


class TempoChange(BaseModel):
    """一段突然變快或變慢的地方。factor 是比整體速度快（或慢）幾倍。"""

    start_measure: int
    end_measure: int
    direction: str  # "faster" 或 "slower"
    factor: float


class MeasureSummary(BaseModel):
    """一個小節的摘要，用來指出問題位置。"""

    measure_number: int
    standard_note_count: int
    correct_pitch_count: int
    missing_notes: int
    wrong_notes: int
    extra_notes: int
    pitch_text: str
    rhythm_text: str
    # 這小節有間隔沒拿到滿分
    rhythm_issue: bool = False


class ScoreReport(BaseModel):
    """整首評分的結構化結果。"""

    standard_midi: str
    student_audio: str
    time_signature: str
    tempo_bpm: float
    pickup_supported: bool
    standard_note_count: int
    student_note_count: int
    correct_pitch_count: int
    missing_notes: int
    extra_notes: int
    pitch_score: float
    rhythm_score: float
    # 滿分：音高 70、節奏 30。LLM 要知道 30 分是節奏滿分，不是低分
    pitch_score_max: int = PITCH_SCORE_MAX
    rhythm_score_max: int = RHYTHM_SCORE_MAX
    tempo_ratio: float
    # 節奏用哪個速度當標準："metronome"＝學生開的節拍器，"student"＝學生自己的整體速度
    tempo_source: str = "student"
    metronome_bpm: float | None = None
    # 學生這次整體大約彈幾 BPM（依音和音的間隔推算）
    played_bpm: float | None = None
    tempo_changes: list[TempoChange] = []
    # 程式整理好的「這次真正的問題」，LLM 回饋只能提到這裡面的事；空的代表全對
    problems: list[str] = []
    raw_total: float
    final_score: int
    measures: list[MeasureSummary]
    error_notes: list[ErrorNote]


# ======================================================
# 檢查使用者提供的輸入檔：必須存在、是檔案、副檔名正確
# 之後才會讀 MIDI / 音訊內容，這裡先擋掉路徑錯誤
# ======================================================
def check_input_file(file_path, allowed_suffixes, label):
    """確認輸入檔可以用，避免後面步驟讀到空路徑或錯副檔名。"""
    if not file_path.exists():
        print(f"[失敗] 找不到{label}：{file_path.resolve()}")
        print("請確認路徑寫對，或把檔案放到這個位置。")
        return False

    if not file_path.is_file():
        print(f"[失敗] {label} 不是檔案：{file_path}")
        return False

    suffix = file_path.suffix.lower()
    if suffix not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        print(f"[失敗] {label} 副檔名應為 {allowed}，現在是 {suffix or '（沒有副檔名）'}")
        return False

    return True


# ======================================================
# 讀取指令列參數：可用 --midi、--audio 覆蓋檔案上方的預設路徑
# ======================================================
def parse_args():
    """解析指令列，讓測試時不必改程式裡的預設路徑。"""
    parser = argparse.ArgumentParser(description="載入標準 MIDI、前處理音檔、轉 MIDI，並讀取兩個 MIDI")
    parser.add_argument("--midi", type=Path, default=MIDI_PATH, help="標準答案 MIDI 檔")
    parser.add_argument("--audio", type=Path, default=AUDIO_PATH, help="測試用音檔")
    return parser.parse_args()


# ======================================================
# 步驟 4：音訊前處理
# 先把音檔整理成「單聲道、固定取樣率、去掉頭尾靜音、音量不要太小」
# 再拿去給 Basic Pitch 轉 MIDI
# ======================================================
def preprocess_audio(audio_path, output_path):
    """讀取測試音檔，做基本前處理，並存成新的 wav。"""
    # sr=PROCESS_SAMPLE_RATE：統一取樣率
    # mono=True：如果是左右聲道，合成一條聲音
    waveform, sample_rate = load_audio(audio_path)
    original_seconds = len(waveform) / sample_rate

    # 去掉開頭和結尾比較安靜的部分
    waveform_without_silence, _trim_index = librosa.effects.trim(
        waveform,
        top_db=30,
    )
    trimmed_seconds = len(waveform_without_silence) / sample_rate

    # 找出最大振幅，把音量拉到接近 0.9，避免錄音太小聲
    peak = float(abs(waveform_without_silence).max())
    if peak > 0:
        waveform_ready = waveform_without_silence / peak * 0.9
    else:
        waveform_ready = waveform_without_silence

    output_path.parent.mkdir(parents=True, exist_ok=True)
    soundfile.write(str(output_path), waveform_ready, PROCESS_SAMPLE_RATE)

    return {
        "source_audio": str(audio_path),
        "processed_audio": str(output_path),
        "sample_rate": PROCESS_SAMPLE_RATE,
        "original_seconds": round(original_seconds, 4),
        "trimmed_seconds": round(trimmed_seconds, 4),
    }


def load_audio(audio_path):
    """讀音檔並轉成單聲道、統一取樣率。

    librosa 1.0 只認 wav、mp3、flac、ogg 這類格式；瀏覽器錄的 webm、手機的 m4a 先用 ffmpeg 轉成 wav 再讀。
    """
    try:
        return librosa.load(str(audio_path), sr=PROCESS_SAMPLE_RATE, mono=True)
    except Exception:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise
    with tempfile.TemporaryDirectory(prefix="aipe04_decode_") as work_dir:
        wav_path = Path(work_dir) / "decoded.wav"
        subprocess.run(
            [ffmpeg, "-loglevel", "error", "-y", "-i", str(audio_path), "-ac", "1", "-ar", str(PROCESS_SAMPLE_RATE), str(wav_path)],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return librosa.load(str(wav_path), sr=PROCESS_SAMPLE_RATE, mono=True)


# ======================================================
# 把 Basic Pitch 的 note_events 轉成字典，方便之後比對
# 原始格式是 tuple，不好閱讀
# ======================================================
def note_events_to_dicts(note_events):
    """把模型輸出的音符 tuple 轉成統一的字典列表。"""
    notes = []

    for event in note_events:
        start = float(event[0])
        end = float(event[1])
        pitch = int(event[2])
        amplitude = float(event[3])
        pitch_name = pretty_midi.note_number_to_name(pitch)

        note = {
            "pitch": pitch,
            "pitch_name": pitch_name,
            "start": round(start, 4),
            "end": round(end, 4),
            "duration": round(end - start, 4),
            "amplitude": round(amplitude, 4),
        }
        notes.append(note)

    return notes


# ======================================================
# 步驟 5：用 Basic Pitch 把「前處理後的音檔」轉成 MIDI 並存檔
# ======================================================
def convert_audio_to_midi(audio_path, output_midi_path, reference_pitch_range=None):
    """把音檔轉成 MIDI，濾掉泛音等假音後存檔，並回傳留下來的音符。

    reference_pitch_range 是標準答案的 (最低音, 最高音)，有給才會限制音域。
    """
    # 一定要指定 ONNX 模型：basic-pitch 預設是 TensorFlow 版，在 Python 3.12 裝不起來
    onnx_model_path = build_icassp_2022_model_path(FilenameSuffix.onnx)
    model_output, _midi_data, note_events = predict(str(audio_path), onnx_model_path)

    raw_notes = note_events_to_dicts(note_events)
    notes = remove_false_notes(raw_notes, reference_pitch_range)
    write_notes_to_midi(notes, output_midi_path)

    model_output_keys = []
    if isinstance(model_output, dict):
        model_output_keys = list(model_output.keys())

    return {
        "source_audio": str(audio_path),
        "output_midi": str(output_midi_path),
        "model_output_keys": model_output_keys,
        "raw_note_count": len(raw_notes),
        "note_count": len(notes),
        "notes": notes,
    }


def remove_false_notes(notes, reference_pitch_range=None):
    """拿掉模型多抓的假音：音域外的音、泛音、很小聲又很短的殘響。真的多彈的音音量夠大，會留下來。"""
    kept = []
    for note in notes:
        if reference_pitch_range is not None:
            lowest, highest = reference_pitch_range
            if note["pitch"] < lowest - PITCH_RANGE_MARGIN or note["pitch"] > highest + PITCH_RANGE_MARGIN:
                continue

        louder_notes = [
            other
            for other in notes
            if other is not note
            and other["start"] <= note["start"] + SOUNDING_EARLY_SECONDS
            and note["start"] < other["end"]
            and other["amplitude"] > note["amplitude"]
        ]
        is_overtone = any(
            note["pitch"] - other["pitch"] in OVERTONE_INTERVALS
            and note["amplitude"] / other["amplitude"] < OVERTONE_MAX_AMPLITUDE_RATIO
            for other in louder_notes
        )
        is_ghost = (
            note["amplitude"] < GHOST_MAX_AMPLITUDE
            and note["duration"] < GHOST_MAX_SECONDS
            and any(note["amplitude"] / other["amplitude"] < GHOST_MAX_AMPLITUDE_RATIO for other in louder_notes)
        )
        if not is_overtone and not is_ghost:
            kept.append(note)
    return kept


def write_notes_to_midi(notes, output_midi_path):
    """把音符列表存成單一鋼琴軌的 MIDI。"""
    midi_data = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0)
    for note in notes:
        velocity = max(1, min(127, int(round(note.get("amplitude", 0.6) * 127))))
        piano.notes.append(pretty_midi.Note(velocity=velocity, pitch=note["pitch"], start=note["start"], end=note["end"]))
    midi_data.instruments.append(piano)
    output_midi_path.parent.mkdir(parents=True, exist_ok=True)
    midi_data.write(str(output_midi_path))


def pitch_range_of(notes):
    """標準答案的最低音與最高音；沒有音符時回傳 None（不限制音域）。"""
    if not notes:
        return None
    pitches = [note["pitch"] for note in notes]
    return (min(pitches), max(pitches))


# ======================================================
# 給 notes.sort 用的排序條件：先比開始時間，再比音高
# ======================================================
def note_sort_key(note):
    """決定音符列表的排列順序。"""
    return (note["start"], note["pitch"])


# ======================================================
# 步驟 3、6：用 pretty_midi 讀取 MIDI，整理成之後可比對的音符列表
# ======================================================
def read_midi_notes(midi_path, label):
    """讀取一個 MIDI 檔，回傳音高、開始時間、結束時間等欄位。"""
    midi_data = pretty_midi.PrettyMIDI(str(midi_path))
    notes = []

    for instrument in midi_data.instruments:
        if instrument.is_drum:
            instrument_name = "Drum"
        elif instrument.name:
            instrument_name = instrument.name
        else:
            instrument_name = "program_" + str(instrument.program)

        for note in instrument.notes:
            one_note = {
                "instrument": instrument_name,
                "pitch": note.pitch,
                "pitch_name": pretty_midi.note_number_to_name(note.pitch),
                "start": round(note.start, 4),
                "end": round(note.end, 4),
                "duration": round(note.end - note.start, 4),
                "velocity": note.velocity,
            }
            notes.append(one_note)

    notes.sort(key=note_sort_key)

    time_signature_text, beats_per_bar, beat_unit = read_time_signature(midi_data)
    tempo_bpm = read_tempo_bpm(midi_data)

    return {
        "label": label,
        "file": str(midi_path),
        "duration_seconds": round(midi_data.get_end_time(), 4),
        "instrument_count": len(midi_data.instruments),
        "note_count": len(notes),
        "time_signature": time_signature_text,
        "beats_per_bar": beats_per_bar,
        "beat_unit": beat_unit,
        "tempo_bpm": tempo_bpm,
        "notes": notes,
    }


# ======================================================
# 步驟 10：讀標準答案的拍號；沒有就用 4/4
# 學生 MIDI 的拍號不使用
# ======================================================
def read_time_signature(midi_data):
    """回傳拍號文字、每小節幾拍、以幾分音符當一拍。"""
    if len(midi_data.time_signature_changes) == 0:
        return "4/4", 4, 4

    first_time_signature = midi_data.time_signature_changes[0]
    beats_per_bar = first_time_signature.numerator
    beat_unit = first_time_signature.denominator
    time_signature_text = str(beats_per_bar) + "/" + str(beat_unit)
    return time_signature_text, beats_per_bar, beat_unit


# ======================================================
# 步驟 10：讀標準答案的 Tempo；沒有就用 120
# ======================================================
def read_tempo_bpm(midi_data):
    """回傳標準答案第一個 Tempo。"""
    _tempo_times, tempo_values = midi_data.get_tempo_changes()
    if len(tempo_values) == 0:
        return DEFAULT_TEMPO_BPM
    return float(tempo_values[0])


# ======================================================
# 一小節有幾秒：依拍號與 Tempo 計算
# 例如 4/4、120 BPM → 一拍 0.5 秒，一小節 2 秒
# ======================================================
def get_measure_duration_seconds(beats_per_bar, beat_unit, tempo_bpm):
    """算出標準答案一小節的秒數。"""
    seconds_per_quarter_note = 60.0 / tempo_bpm
    quarter_notes_in_one_measure = beats_per_bar * (4.0 / beat_unit)
    measure_seconds = quarter_notes_in_one_measure * seconds_per_quarter_note
    return measure_seconds


# ======================================================
# 這顆標準音符屬於第幾小節
# 第一顆音就是第 1 小節開頭，MVP 不處理弱起
# ======================================================
def get_measure_number(note_start, first_note_start, measure_seconds):
    """依標準答案時間，算出音符在第幾小節。"""
    elapsed = note_start - first_note_start
    if elapsed < 0:
        elapsed = 0
    measure_index = int(elapsed / measure_seconds + 0.000001)
    return measure_index + 1


# ======================================================
# 步驟 7：建立 DTW 成本矩陣
# 音高相同成本小，音高不同成本大
# ======================================================
def build_dtw_cost_matrix(standard_notes, student_notes):
    """比較每一顆標準音和每一顆學生音，算出配對成本。"""
    standard_count = len(standard_notes)
    student_count = len(student_notes)
    cost_matrix = numpy.zeros((standard_count, student_count))

    standard_index = 0
    while standard_index < standard_count:
        student_index = 0
        while student_index < student_count:
            standard_pitch = standard_notes[standard_index]["pitch"]
            student_pitch = student_notes[student_index]["pitch"]
            if standard_pitch == student_pitch:
                cost_matrix[standard_index, student_index] = DTW_SAME_PITCH_COST
            else:
                cost_matrix[standard_index, student_index] = DTW_DIFFERENT_PITCH_COST
            student_index = student_index + 1
        standard_index = standard_index + 1

    return cost_matrix


# ======================================================
# 步驟 7：用 DTW 路徑決定「學生哪一顆音對到標準哪一顆音」
# 只接受音高完全相同的配對；多出來的學生音記成 extra
# ======================================================
def align_notes_with_dtw(standard_notes, student_notes):
    """回傳每顆標準音對應的學生音編號，以及多彈的音。"""
    standard_count = len(standard_notes)
    student_count = len(student_notes)

    if standard_count == 0 or student_count == 0:
        return {
            "pairs": [],
            "standard_to_student": [-1] * standard_count,
            "extra_student_indexes": list(range(student_count)),
        }

    cost_matrix = build_dtw_cost_matrix(standard_notes, student_notes)
    _distance_matrix, warp_path = librosa.sequence.dtw(C=cost_matrix)

    # librosa 的路徑是從最後一格走回第一格，這裡改成從頭到尾
    ordered_path = []
    path_index = len(warp_path) - 1
    while path_index >= 0:
        standard_index = int(warp_path[path_index][0])
        student_index = int(warp_path[path_index][1])
        ordered_path.append((standard_index, student_index))
        path_index = path_index - 1

    standard_to_student = [-1] * standard_count
    used_student = [False] * student_count

    pair_index = 0
    while pair_index < len(ordered_path):
        standard_index, student_index = ordered_path[pair_index]
        already_has_standard = standard_to_student[standard_index] != -1
        already_has_student = used_student[student_index]
        same_pitch = standard_notes[standard_index]["pitch"] == student_notes[student_index]["pitch"]

        if (already_has_standard is False) and (already_has_student is False) and same_pitch:
            standard_to_student[standard_index] = student_index
            used_student[student_index] = True

        pair_index = pair_index + 1

    extra_student_indexes = []
    student_index = 0
    while student_index < student_count:
        if used_student[student_index] is False:
            extra_student_indexes.append(student_index)
        student_index = student_index + 1

    pairs = []
    standard_index = 0
    while standard_index < standard_count:
        student_index = standard_to_student[standard_index]
        pair = {
            "standard_index": standard_index,
            "student_index": student_index,
            "standard_pitch": standard_notes[standard_index]["pitch"],
            "standard_pitch_name": standard_notes[standard_index]["pitch_name"],
            "standard_start": standard_notes[standard_index]["start"],
        }
        if student_index == -1:
            pair["matched"] = False
            pair["student_pitch"] = None
            pair["student_start"] = None
        else:
            pair["matched"] = True
            pair["student_pitch"] = student_notes[student_index]["pitch"]
            pair["student_start"] = student_notes[student_index]["start"]
        pairs.append(pair)
        standard_index = standard_index + 1

    return {
        "pairs": pairs,
        "standard_to_student": standard_to_student,
        "extra_student_indexes": extra_student_indexes,
    }


# ======================================================
# 步驟 9：用已配對音符的 IOI 比例，估算學生整首彈快或彈慢多少
# ======================================================
def get_median(numbers):
    """算出中位數。沒有數字時回傳 1，代表先當速度相同。"""
    if len(numbers) == 0:
        return 1.0

    sorted_numbers = sorted(numbers)
    count = len(sorted_numbers)
    middle = count // 2
    if count % 2 == 1:
        return sorted_numbers[middle]

    left = sorted_numbers[middle - 1]
    right = sorted_numbers[middle]
    return (left + right) / 2.0


def estimate_tempo_ratio(standard_notes, standard_to_student, student_notes):
    """學生 IOI 除以標準 IOI，再用中位數當整體速度比例。"""
    ratios = []
    note_index = 0
    last_index = len(standard_notes) - 1

    while note_index < last_index:
        this_student_index = standard_to_student[note_index]
        next_student_index = standard_to_student[note_index + 1]

        if this_student_index != -1 and next_student_index != -1:
            standard_ioi = standard_notes[note_index + 1]["start"] - standard_notes[note_index]["start"]
            student_ioi = student_notes[next_student_index]["start"] - student_notes[this_student_index]["start"]
            if standard_ioi > 0 and student_ioi > 0:
                ratios.append(student_ioi / standard_ioi)

        note_index = note_index + 1

    return get_median(ratios)


# ======================================================
# 步驟 9：一組相鄰音符的節奏得分權重：1、0.5 或 0
# ======================================================
def score_one_ioi(standard_ioi, student_ioi, tempo_ratio):
    """先排除整體速度差，再看這一間隔的比例誤差。"""
    if standard_ioi <= 0:
        return 0.0

    if student_ioi is None:
        return 0.0

    normalized_student_ioi = student_ioi / tempo_ratio
    absolute_error = abs(normalized_student_ioi - standard_ioi)
    ratio_error = absolute_error / standard_ioi

    if absolute_error <= RHYTHM_MIN_TOLERANCE_SECONDS:
        return 1.0
    if ratio_error <= RHYTHM_FULL_RATIO:
        return 1.0
    if ratio_error <= RHYTHM_HALF_RATIO:
        return 0.5
    return 0.0


# ======================================================
# 步驟 8、9、11：用整首標準音符算總分，並順便做每小節摘要
# ======================================================
def score_performance(standard_midi, student_midi, alignment, metronome_bpm=None):
    """依規格計算音高 70、節奏 30，以及每小節紀錄。

    有開節拍器時，節奏照節拍器速度比；沒開時，照學生自己的整體速度（中位數）按比例比。
    """
    standard_notes = standard_midi["notes"]
    student_notes = student_midi["notes"]
    standard_to_student = alignment["standard_to_student"]
    extra_student_indexes = alignment["extra_student_indexes"]

    standard_count = len(standard_notes)
    correct_pitch_count = 0
    missing_count = 0
    extra_count = len(extra_student_indexes)

    standard_index = 0
    while standard_index < standard_count:
        student_index = standard_to_student[standard_index]
        if student_index == -1:
            missing_count = missing_count + 1
        else:
            correct_pitch_count = correct_pitch_count + 1
        standard_index = standard_index + 1

    if standard_count == 0:
        pitch_score = 0.0
    else:
        pitch_score = correct_pitch_count / standard_count * PITCH_SCORE_MAX

    played_ratio = estimate_tempo_ratio(standard_notes, standard_to_student, student_notes)
    if metronome_bpm:
        # 標準音之間的秒數是照 MIDI 速度算的；換成節拍器速度後，每個間隔應該是原本的 MIDI 速度 / 節拍器速度 倍
        tempo_ratio = standard_midi["tempo_bpm"] / metronome_bpm
        tempo_source = "metronome"
    else:
        tempo_ratio = played_ratio
        tempo_source = "student"

    ioi_weights = []
    ioi_details = []
    note_index = 0
    last_index = standard_count - 1
    while note_index < last_index:
        this_student_index = standard_to_student[note_index]
        next_student_index = standard_to_student[note_index + 1]
        standard_ioi = standard_notes[note_index + 1]["start"] - standard_notes[note_index]["start"]

        if this_student_index == -1 or next_student_index == -1:
            student_ioi = None
        else:
            student_ioi = student_notes[next_student_index]["start"] - student_notes[this_student_index]["start"]

        weight = score_one_ioi(standard_ioi, student_ioi, tempo_ratio)
        ioi_weights.append(weight)
        ioi_details.append(
            {
                "from_standard_index": note_index,
                "to_standard_index": note_index + 1,
                "standard_ioi": round(standard_ioi, 4),
                "student_ioi": None if student_ioi is None else round(student_ioi, 4),
                "weight": weight,
            }
        )
        note_index = note_index + 1

    ioi_count = len(ioi_weights)
    if ioi_count == 0:
        rhythm_score = RHYTHM_SCORE_MAX
    else:
        weight_sum = 0.0
        weight_index = 0
        while weight_index < ioi_count:
            weight_sum = weight_sum + ioi_weights[weight_index]
            weight_index = weight_index + 1
        rhythm_score = (weight_sum / ioi_count) * RHYTHM_SCORE_MAX

    raw_total = pitch_score + rhythm_score
    final_score = int(round(raw_total))

    measure_summaries = build_measure_summaries(
        standard_midi,
        student_notes,
        standard_to_student,
        extra_student_indexes,
        ioi_details,
    )

    return {
        "standard_note_count": standard_count,
        "correct_pitch_count": correct_pitch_count,
        "missing_notes": missing_count,
        "wrong_notes": 0,
        "extra_notes": extra_count,
        "pitch_score": round(pitch_score, 2),
        "rhythm_score": round(rhythm_score, 2),
        "tempo_ratio": round(tempo_ratio, 4),
        "tempo_source": tempo_source,
        "metronome_bpm": metronome_bpm,
        "played_bpm": round(standard_midi["tempo_bpm"] / played_ratio, 1) if played_ratio > 0 else None,
        "tempo_changes": find_tempo_changes(standard_midi, ioi_details, tempo_ratio),
        "ioi_details": ioi_details,
        "ioi_count": ioi_count,
        "raw_total": round(raw_total, 2),
        "final_score": final_score,
        "measures": measure_summaries,
        "error_notes": build_error_notes(
            standard_midi,
            student_notes,
            standard_to_student,
            extra_student_indexes,
            ioi_details,
            tempo_ratio,
        ),
    }


def find_tempo_changes(standard_midi, ioi_details, tempo_ratio):
    """找出連續好幾個間隔都明顯比整體速度快或慢的段落，例如前面 65 BPM、中間突然 120 BPM。

    這些間隔在節奏分數裡本來就拿不到分；這裡只是把位置找出來，寫進回饋讓學生知道。
    """
    changes = []
    run = []
    run_direction = None

    def close_run():
        if len(run) >= TEMPO_CHANGE_MIN_INTERVALS:
            local = get_median([item["local"] for item in run])
            factor = 1 / local if run_direction == "faster" else local
            start = get_standard_note_location(standard_midi, run[0]["from_standard_index"])["measure_number"]
            end = get_standard_note_location(standard_midi, run[-1]["to_standard_index"])["measure_number"]
            changes.append(
                TempoChange(start_measure=start, end_measure=end, direction=run_direction, factor=round(factor, 1))
            )

    for detail in ioi_details:
        direction = None
        if detail["student_ioi"] and detail["standard_ioi"] > 0 and tempo_ratio > 0:
            # 1 代表和整體速度一樣，0.5 代表這一段快了一倍
            local = detail["student_ioi"] / detail["standard_ioi"] / tempo_ratio
            if local < 1 / TEMPO_CHANGE_FACTOR:
                direction = "faster"
            elif local > TEMPO_CHANGE_FACTOR:
                direction = "slower"
        if direction is not None and direction == run_direction:
            run.append({**detail, "local": local})
            continue
        close_run()
        run = [{**detail, "local": local}] if direction else []
        run_direction = direction
    close_run()
    return changes


# ======================================================
# 步驟 10、11：小節永遠依標準答案切；學生音跟著它配對到的標準音走
# ======================================================
def build_measure_summaries(
    standard_midi,
    student_notes,
    standard_to_student,
    extra_student_indexes,
    ioi_details,
):
    """整理每個小節的音高與節奏摘要，給之後 LLM 回饋用。"""
    standard_notes = standard_midi["notes"]
    if len(standard_notes) == 0:
        return []

    first_note_start = standard_notes[0]["start"]
    measure_seconds = get_measure_duration_seconds(
        standard_midi["beats_per_bar"],
        standard_midi["beat_unit"],
        standard_midi["tempo_bpm"],
    )

    measure_map = {}

    standard_index = 0
    while standard_index < len(standard_notes):
        measure_number = get_measure_number(
            standard_notes[standard_index]["start"],
            first_note_start,
            measure_seconds,
        )
        if measure_number not in measure_map:
            measure_map[measure_number] = {
                "measure_number": measure_number,
                "standard_note_count": 0,
                "correct_pitch_count": 0,
                "missing_notes": 0,
                "extra_notes": 0,
                "ioi_weight_sum": 0.0,
                "ioi_count": 0,
            }

        measure_map[measure_number]["standard_note_count"] += 1
        if standard_to_student[standard_index] == -1:
            measure_map[measure_number]["missing_notes"] += 1
        else:
            measure_map[measure_number]["correct_pitch_count"] += 1

        standard_index = standard_index + 1

    extra_index = 0
    while extra_index < len(extra_student_indexes):
        student_index = extra_student_indexes[extra_index]
        nearest_standard_index = find_nearest_standard_index(
            student_notes[student_index]["start"],
            standard_notes,
        )
        measure_number = get_measure_number(
            standard_notes[nearest_standard_index]["start"],
            first_note_start,
            measure_seconds,
        )
        if measure_number not in measure_map:
            measure_map[measure_number] = {
                "measure_number": measure_number,
                "standard_note_count": 0,
                "correct_pitch_count": 0,
                "missing_notes": 0,
                "extra_notes": 0,
                "ioi_weight_sum": 0.0,
                "ioi_count": 0,
            }
        measure_map[measure_number]["extra_notes"] += 1
        extra_index = extra_index + 1

    ioi_index = 0
    while ioi_index < len(ioi_details):
        from_index = ioi_details[ioi_index]["from_standard_index"]
        measure_number = get_measure_number(
            standard_notes[from_index]["start"],
            first_note_start,
            measure_seconds,
        )
        measure_map[measure_number]["ioi_weight_sum"] += ioi_details[ioi_index]["weight"]
        measure_map[measure_number]["ioi_count"] += 1
        ioi_index = ioi_index + 1

    summaries = []
    measure_numbers = sorted(measure_map.keys())
    number_index = 0
    while number_index < len(measure_numbers):
        measure_number = measure_numbers[number_index]
        item = measure_map[measure_number]
        ioi_count = item["ioi_count"]
        if ioi_count == 0:
            # 這小節沒有可以比的間隔（例如只有最後一顆音），不是節奏不好
            rhythm_text = "沒有可比的間隔"
        else:
            rhythm_text = str(item["ioi_weight_sum"]) + " / " + str(ioi_count)

        summaries.append(
            {
                "measure_number": measure_number,
                "standard_note_count": item["standard_note_count"],
                "correct_pitch_count": item["correct_pitch_count"],
                "missing_notes": item["missing_notes"],
                "wrong_notes": 0,
                "extra_notes": item["extra_notes"],
                "pitch_text": str(item["correct_pitch_count"]) + " / " + str(item["standard_note_count"]),
                "rhythm_text": rhythm_text,
                "rhythm_issue": ioi_count > 0 and item["ioi_weight_sum"] < ioi_count,
            }
        )
        number_index = number_index + 1

    return summaries


# ======================================================
# 多彈的音沒有配對對象時，先掛到時間最近的標準音那一小節
# 只是方便回饋，不會因此扣總分
# ======================================================
def find_nearest_standard_index(student_start, standard_notes):
    """找出開始時間最接近的標準音符編號。"""
    nearest_index = 0
    nearest_distance = abs(standard_notes[0]["start"] - student_start)
    note_index = 1
    while note_index < len(standard_notes):
        distance = abs(standard_notes[note_index]["start"] - student_start)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_index = note_index
        note_index = note_index + 1
    return nearest_index


# ======================================================
# 查出標準音符在第幾小節、是該小節第幾顆
# ======================================================
def get_standard_note_location(standard_midi, standard_index):
    """回傳小節編號、該小節第幾顆、音名。"""
    standard_notes = standard_midi["notes"]
    first_note_start = standard_notes[0]["start"]
    measure_seconds = get_measure_duration_seconds(
        standard_midi["beats_per_bar"],
        standard_midi["beat_unit"],
        standard_midi["tempo_bpm"],
    )
    measure_number = get_measure_number(
        standard_notes[standard_index]["start"],
        first_note_start,
        measure_seconds,
    )

    note_in_measure = 0
    note_index = 0
    while note_index <= standard_index:
        this_measure = get_measure_number(
            standard_notes[note_index]["start"],
            first_note_start,
            measure_seconds,
        )
        if this_measure == measure_number:
            note_in_measure = note_in_measure + 1
        note_index = note_index + 1

    return {
        "measure_number": measure_number,
        "note_in_measure": note_in_measure,
        "pitch_name": standard_notes[standard_index]["pitch_name"],
    }


# ======================================================
# 整理需要印出來的錯音：漏音、節奏不對、多彈
# ======================================================
def build_error_notes(
    standard_midi,
    student_notes,
    standard_to_student,
    extra_student_indexes,
    ioi_details,
    tempo_ratio,
):
    """回傳錯音列表，方便 main 直接印出來。"""
    error_notes = []
    standard_notes = standard_midi["notes"]

    standard_index = 0
    while standard_index < len(standard_notes):
        if standard_to_student[standard_index] == -1:
            location = get_standard_note_location(standard_midi, standard_index)
            error_notes.append(
                {
                    "measure_number": location["measure_number"],
                    "note_in_measure": location["note_in_measure"],
                    "pitch_name": location["pitch_name"],
                    "reason": "漏音",
                }
            )
        standard_index = standard_index + 1

    ioi_index = 0
    while ioi_index < len(ioi_details):
        detail = ioi_details[ioi_index]
        from_index = detail["from_standard_index"]
        to_index = detail["to_standard_index"]
        both_matched = (
            standard_to_student[from_index] != -1
            and standard_to_student[to_index] != -1
        )
        if both_matched and detail["weight"] < 1.0:
            location = get_standard_note_location(standard_midi, from_index)
            next_name = standard_notes[to_index]["pitch_name"]
            reason = describe_rhythm_error(detail, tempo_ratio)
            error_notes.append(
                {
                    "measure_number": location["measure_number"],
                    "note_in_measure": location["note_in_measure"],
                    "pitch_name": location["pitch_name"] + " 到 " + next_name,
                    "reason": reason,
                }
            )
        ioi_index = ioi_index + 1

    extra_index = 0
    while extra_index < len(extra_student_indexes):
        student_index = extra_student_indexes[extra_index]
        nearest_standard_index = find_nearest_standard_index(
            student_notes[student_index]["start"],
            standard_notes,
        )
        location = get_standard_note_location(standard_midi, nearest_standard_index)
        error_notes.append(
            {
                "measure_number": location["measure_number"],
                "note_in_measure": None,
                "pitch_name": student_notes[student_index]["pitch_name"],
                "reason": "多彈（不扣分）",
            }
        )
        extra_index = extra_index + 1

    return error_notes


# ======================================================
# 把節奏誤差轉成「偏快／偏慢」文字
# ======================================================
def describe_rhythm_error(ioi_detail, tempo_ratio):
    """依正規化後的間隔，說明這一顆音後面的節奏哪裡不對。"""
    student_ioi = ioi_detail["student_ioi"]
    standard_ioi = ioi_detail["standard_ioi"]
    if student_ioi is None or tempo_ratio == 0:
        return "節奏錯誤"

    normalized_student_ioi = student_ioi / tempo_ratio
    if ioi_detail["weight"] == 0.5:
        if normalized_student_ioi > standard_ioi:
            return "節奏稍慢"
        return "節奏稍快"
    if normalized_student_ioi > standard_ioi:
        return "節奏偏慢"
    return "節奏偏快"


# ======================================================
# 步驟 12：把評分 dict 轉成 Pydantic 結構
# ======================================================
def build_score_report(midi_path, audio_path, standard_midi, student_midi, score_result):
    """檢查欄位後，產出之後可以轉成 JSON 的評分報告。"""
    report = ScoreReport(
        standard_midi=str(midi_path),
        student_audio=str(audio_path),
        time_signature=standard_midi["time_signature"],
        tempo_bpm=standard_midi["tempo_bpm"],
        pickup_supported=False,
        standard_note_count=standard_midi["note_count"],
        student_note_count=student_midi["note_count"],
        correct_pitch_count=score_result["correct_pitch_count"],
        missing_notes=score_result["missing_notes"],
        extra_notes=score_result["extra_notes"],
        pitch_score=score_result["pitch_score"],
        rhythm_score=score_result["rhythm_score"],
        tempo_ratio=score_result["tempo_ratio"],
        tempo_source=score_result["tempo_source"],
        metronome_bpm=score_result["metronome_bpm"],
        played_bpm=score_result["played_bpm"],
        tempo_changes=score_result["tempo_changes"],
        raw_total=score_result["raw_total"],
        final_score=score_result["final_score"],
        measures=score_result["measures"],
        error_notes=score_result["error_notes"],
    )
    report.problems = list_problems(report)
    return report


def join_measures(numbers):
    """[3, 6, 7] → 「第 3、6、7 小節」。"""
    return "第 " + "、".join(str(number) for number in numbers) + " 小節"


def list_problems(report):
    """把評分結果整理成幾句話，給 LLM 當成「只能講這些」的清單。"""
    problems = []
    missing = [item.measure_number for item in report.measures if item.missing_notes]
    if missing:
        problems.append(join_measures(missing[:5]) + "有漏掉或彈錯的音")
    if report.extra_notes:
        problems.append(f"有 {report.extra_notes} 個多彈的音（不扣分）")
    rhythm = [item.measure_number for item in report.measures if item.rhythm_issue]
    if rhythm:
        problems.append(join_measures(rhythm[:5]) + "節奏跟答案不一樣")
    for change in report.tempo_changes:
        speed = "變快" if change.direction == "faster" else "變慢"
        where = join_measures(range(change.start_measure, change.end_measure + 1)) if change.end_measure - change.start_measure < 4 else f"第 {change.start_measure}～{change.end_measure} 小節"
        problems.append(f"{where}突然{speed}約 {change.factor} 倍")
    return problems


# ======================================================
# 步驟 13：把結構化結果交給 LLM，產生給學生看的文字回饋
# 透過 backend/services/llm.py 呼叫：有等待上限、會重試一次、失敗會記下原因，
# 也可以在 .env 用 PRACTICE_FEEDBACK_LLM_PROVIDER 切換 Gemini 或 OpenAI
# ======================================================
FEEDBACK_SYSTEM_PROMPT = """你是一位溫柔、簡潔、清楚的鋼琴老師。請根據這次練習的評分，用繁體中文給學生 2～4 句回饋。

你會拿到：
- 音高分數、節奏分數：寫「（滿分）」的就是完全正確。音高滿分 70、節奏滿分 30，30 分是節奏滿分，不是低分。
- problems：程式整理好的「這次真正的問題」。
- 節拍器（可能沒有）：有開節拍器時，節奏是照節拍器的速度評分。

規則：
1. 第一句先具體肯定這次做得好的地方。
2. 問題只能從 problems 裡挑，最多挑 1～2 個最明顯的，用概括的方式說（例如「第 5、7 小節有幾個音要再確認」）。
3. problems 是空的，代表音高和節奏都對：只稱讚和鼓勵，不可以說任何地方要改進、不穩或得分低。
4. 有「突然變快／變慢」的問題時優先提醒，請學生那裡保持跟前後一樣的速度。
5. 有多彈的音時只要簡單提醒「有幾個地方多彈了，可以再注意一下」，不要猜原因。
6. 不要編造沒有給你的小節、音符、錯誤或進步，也不要提到「上次」。
7. 最後一句給一個簡單、實際的練習建議或鼓勵。
8. 像老師直接對學生說話，不要像系統報告；只輸出回饋本身，不要標題、條列或 JSON。
9. 分數只用來幫你判斷表現，回饋裡不可以提到分數、滿分或任何評分數字。

語氣示範（內容一定要照這次的 problems，不要照抄）：
有問題時：「這次整體彈得很不錯！第 5、7 小節還有幾個音需要再確認一下，可以看著樂譜慢慢練一次。繼續保持！」
problems 是空的時：「這次音準和節奏都很穩，整首彈得很完整，做得很好！下次可以試著加一點強弱變化。」"""


def load_llm_module():
    """在專案根目錄外直接執行這支檔案時，先把專案根目錄加進 sys.path 才找得到 backend 套件。"""
    try:
        from backend.services import llm
    except ImportError:
        sys.path.insert(0, str(BASE_DIR.parents[1]))
        from backend.services import llm
    return llm


def score_text(score, maximum):
    text = f"{score:g} / {maximum}"
    return text + "（滿分）" if score >= maximum else text


def feedback_input(score_report):
    """交給 LLM 的精簡內容。完整報告數字太多，小模型容易看錯（例如把節奏 30 分當成低分），只給它需要的。"""
    data = {
        "音高分數": score_text(score_report.pitch_score, score_report.pitch_score_max),
        "節奏分數": score_text(score_report.rhythm_score, score_report.rhythm_score_max),
        "彈對的音": f"{score_report.correct_pitch_count} / {score_report.standard_note_count}",
        "problems": score_report.problems,
    }
    if score_report.tempo_source == "metronome" and score_report.metronome_bpm:
        data["節拍器"] = f"有開，{score_report.metronome_bpm:g} BPM，節奏照節拍器速度評分"
    return json.dumps(data, ensure_ascii=False, indent=2)


def generate_feedback(score_report):
    """回傳 (回饋文字, 失敗原因)。成功時失敗原因是 None。"""
    llm = load_llm_module()
    return llm.generate_text_with_reason(
        FEEDBACK_SYSTEM_PROMPT,
        feedback_input(score_report),
        feature=llm.FEATURE_PRACTICE_FEEDBACK,
        temperature=0.4,
    )


# ======================================================
# 最後只印測試摘要：檔案、讀取是否成功、音符數、分數、回饋
# ======================================================
def print_test_summary(midi_path, audio_path, read_ok, score_report, feedback_text, feedback_error):
    """印出這次測試最需要看的結果。"""
    print("測試檔案")
    print("標準答案 MIDI：" + str(midi_path))
    print("學生演奏音檔：" + str(audio_path))
    if read_ok is False:
        print("讀取結果：失敗")
        return

    print("讀取結果：成功")
    print("標準答案音符數：" + str(score_report.standard_note_count))
    print("使用者音符數：" + str(score_report.student_note_count))
    print("音高分數：" + str(score_report.pitch_score) + " 分")
    print("節奏分數：" + str(score_report.rhythm_score) + " 分")
    print("最後分數：" + str(score_report.final_score) + " 分")
    print_error_notes(score_report.error_notes)

    print("AI 回饋：")
    if feedback_text:
        print(feedback_text)
    else:
        print(feedback_error)


# ======================================================
# 把錯音一行一行印出來
# ======================================================
def print_error_notes(error_notes):
    """印出第幾小節的哪個音出了什麼問題。"""
    print("錯音：")
    if len(error_notes) == 0:
        print("沒有")
        return

    error_index = 0
    while error_index < len(error_notes):
        item = error_notes[error_index]
        if item.note_in_measure is None:
            place = "第 " + str(item.measure_number) + " 小節 " + item.pitch_name
        else:
            place = (
                "第 "
                + str(item.measure_number)
                + " 小節第 "
                + str(item.note_in_measure)
                + " 顆 "
                + item.pitch_name
            )
        print(place + "：" + item.reason)
        error_index = error_index + 1


# ======================================================
# 測試入口：檢查檔案 → 前處理 → 轉 MIDI → 對齊 → 評分 → 回饋
# ======================================================
def main():
    """依序執行步驟 1 到 13，最後只印測試摘要。"""
    start_time = time.time()
    args = parse_args()

    midi_ok = check_input_file(args.midi, MIDI_SUFFIXES, "標準答案 MIDI")
    audio_ok = check_input_file(args.audio, AUDIO_SUFFIXES, "測試音檔")
    if midi_ok is False or audio_ok is False:
        print_test_summary(args.midi, args.audio, False, None, None, None)
        print_elapsed_seconds(start_time)
        return 1

    processed_audio_path = PROCESSED_DIR / (args.audio.stem + "_processed.wav")
    preprocess_audio(args.audio, processed_audio_path)

    standard_midi = read_midi_notes(args.midi, "標準答案")
    converted_midi_path = CONVERTED_DIR / (args.audio.stem + "_converted.mid")
    convert_audio_to_midi(processed_audio_path, converted_midi_path, pitch_range_of(standard_midi["notes"]))

    student_midi = read_midi_notes(converted_midi_path, "學生演奏（由音檔轉出）")

    alignment = align_notes_with_dtw(standard_midi["notes"], student_midi["notes"])
    score_result = score_performance(standard_midi, student_midi, alignment)
    score_report = build_score_report(
        args.midi,
        args.audio,
        standard_midi,
        student_midi,
        score_result,
    )
    feedback_text, feedback_error = generate_feedback(score_report)
    print_test_summary(
        args.midi,
        args.audio,
        True,
        score_report,
        feedback_text,
        feedback_error,
    )
    print_elapsed_seconds(start_time)
    return 0


# ======================================================
# 算出從開始執行到現在過了幾秒
# ======================================================
def print_elapsed_seconds(start_time):
    """印出這次測試總共花了多少秒。"""
    elapsed = time.time() - start_time
    print("執行時間：" + str(round(elapsed, 2)) + " 秒")


if __name__ == "__main__":
    sys.exit(main())
