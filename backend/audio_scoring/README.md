# backend/audio_scoring：演奏評分測試說明

這個資料夾用來測試 `midi_test.py`：把「標準答案 MIDI」和「學生演奏音檔」比對，算出音高／節奏分數，再請 Gemini 寫文字回饋。

## 2026-10-27 更新重點

- **步驟 5 濾掉假音**：音域外的音、泛音（大聲的音上方八度、十二度…的小聲音）、很小聲又很短的殘響。多彈的真音音量夠大，會留下來。
- **節拍器**：學生錄音時有開節拍器，`score_performance(..., metronome_bpm)` 的節奏照節拍器速度比（`tempo_source = "metronome"`）；沒開或上傳音檔，照學生自己的整體速度（中位數）按比例比。評分標準不變：音高 70、節奏 30，多彈不扣分。
- **突然變快／變慢**：`find_tempo_changes()` 找出連續 3 個以上間隔都比整體速度快或慢 1.35 倍以上的段落，放進 `ScoreReport.tempo_changes`，回饋會提到「第幾小節突然變快約幾倍」。這些間隔本來就拿不到節奏分。
- **上下對照樂譜**：`score_sheet.py` 把答案和學生演奏做成同一份 MusicXML 的兩行，每個小節上下對齊。學生的音照評分用的速度換成拍子，對齊到跟答案一樣細的格子（最細 16 分音符）。顏色：紅＝彈錯音高（答案行：沒彈對的音）、橘＝多彈、藍＝音對但時間不對。網站的作業頁用 OpenSheetMusicDisplay 顯示。
- **讀音檔**：`load_audio()` 讀不了 webm／m4a 時，先用 ffmpeg 轉成 wav。

## 使用的工具與預訓練模型

| 名稱 | 用在哪裡 | 做什麼 |
| --- | --- | --- |
| librosa | 步驟 4、7 | 讀取音檔、轉成單聲道、去掉頭尾靜音；再用 DTW 把學生的音對到標準答案 |
| soundfile | 步驟 4 | 把處理好的聲音存成 `.wav` |
| Basic Pitch | 步驟 5 | 把音檔裡聽到的音轉成音符 |
| ICASSP 2022 ONNX 模型 | 步驟 5 | Basic Pitch 附帶的預訓練模型，負責從聲音判斷音高和時間。程式用 ONNX 版本，不必另外安裝 TensorFlow |
| pretty_midi | 步驟 3、5、6 | 讀取 MIDI，取出每顆音的音高、開始時間和結束時間 |
| NumPy | 步驟 7 | 建立 DTW 比對時使用的成本表 |
| Pydantic | 步驟 12 | 把分數、小節摘要和錯音整理成固定格式 |
| music21 | 對照樂譜 | 把答案與學生的音符排成兩行樂譜，輸出 MusicXML |
| ffmpeg | 步驟 4 | 把瀏覽器錄的 webm、手機的 m4a 轉成 wav |
| Google Gemini | 步驟 13 | 依照評分結果寫給學生看的文字回饋。測試使用 `gemini-3.8-flash` |

目前做到步驟 1～13。中間結果大多是程式裡的 **Python dict**，**不會自動存成 JSON 檔**。只有兩個步驟會寫出檔案：

- 步驟 4：寫出前處理後的 `.wav`
- 步驟 5：寫出轉好的 `.mid`

步驟 12 的評分報告是 **Pydantic 物件**。呼叫 Gemini 時會用 `model_dump_json()` 轉成 **JSON 字串** 傳出去，但仍不會存到磁碟。

最後終端機印出的是 **純文字摘要**，不是 JSON。

---

## 怎麼執行

在專案根目錄：

```bash
pip install -r requirements.txt
python backend/audio_scoring/midi_test.py
```

可改用其他檔案：

```bash
python backend/audio_scoring/midi_test.py --midi backend/audio_scoring/midi_test_data/test1.mid --audio backend/audio_scoring/audio_test_data/test3.mp3
```

若要產生 AI 回饋，在專案根目錄 `.env` 寫入 `GEMINI_API_KEY=你的key`。`.env` 不要提交到 Git。

---

## 資料夾

| 路徑 | 用途 |
| --- | --- |
| `midi_test_data/` | 步驟 1：放標準答案 MIDI |
| `audio_test_data/` | 步驟 2：放測試音檔（`.wav` / `.mp3` / `.m4a` / `.flac` / `.ogg`） |
| `processed_audio/` | 步驟 4 產出：前處理後的 wav（執行後才會出現） |
| `converted_midi/` | 步驟 5 產出：音檔轉出的 MIDI（執行後才會出現） |

預設檔案：

- 標準答案：`midi_test_data/test1.mid`
- 測試音檔：`audio_test_data/test3.mp3`

---

## 整體流程

```text
標準 MIDI + 學生音檔
        ↓
[4] 音訊前處理 → .wav + dict
        ↓
[5] 音檔轉 MIDI → .mid + dict（含音符列表）
        ↓
[3][6] 讀兩個 MIDI → dict（含音符列表）
        ↓
[7] DTW 對齊 → dict（配對結果）
        ↓
[8][9][10][11] 評分與小節摘要 → dict
        ↓
[12] Pydantic ScoreReport（可轉 JSON）
        ↓
[13] Gemini 文字回饋 → 字串
        ↓
終端機純文字摘要
```

---

## 各步驟產出

### 步驟 1. 準備標準答案 MIDI

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 把標準答案 MIDI 放到 `midi_test_data/` |
| 寫出檔案 | 無（只使用現成 `.mid` / `.midi`） |
| 程式回傳 | 無（這步是準備檔案） |
| 資料格式 | MIDI 二進位檔 |

---

### 步驟 2. 準備測試音檔

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 把學生演奏音檔放到 `audio_test_data/`，目前不用瀏覽器錄音 |
| 寫出檔案 | 無 |
| 程式回傳 | 無 |
| 資料格式 | 音訊檔（wav / mp3 等） |

開始評分前會先檢查兩個路徑是否存在、是否為檔案、副檔名是否正確。失敗時終端機印 `[失敗] ...`，並結束。

---

### 步驟 3. 讀取標準答案 MIDI

函式：`read_midi_notes(midi_path, "標準答案")`

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 用 pretty_midi 讀標準 MIDI，抽出音符、拍號、Tempo |
| 寫出檔案 | 無 |
| 程式回傳 | **Python dict** |
| 資料格式 | dict，不是 JSON 檔 |

回傳欄位：

```text
{
  "label": "標準答案",
  "file": "路徑",
  "duration_seconds": 12.3456,
  "instrument_count": 1,
  "note_count": 16,
  "time_signature": "4/4",
  "beats_per_bar": 4,
  "beat_unit": 4,
  "tempo_bpm": 120.0,
  "notes": [ 音符dict, ... ]
}
```

每顆音符：

```text
{
  "instrument": "鋼琴或 program_0",
  "pitch": 60,              # MIDI number
  "pitch_name": "C4",
  "start": 0.0,             # 秒
  "end": 0.5,
  "duration": 0.5,
  "velocity": 80
}
```

沒有拍號時預設 `4/4`，沒有 Tempo 時預設 `120`。

---

### 步驟 4. 音訊前處理

函式：`preprocess_audio(audio_path, output_path)`

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 轉單聲道、取樣率改成 22050、去掉頭尾靜音、把最大音量拉到約 0.9 |
| 寫出檔案 | `processed_audio/<音檔名>_processed.wav` |
| 程式回傳 | **Python dict**（處理摘要） |
| 資料格式 | 檔案是 **WAV**；回傳是 **dict**，不是 JSON |

回傳欄位：

```text
{
  "source_audio": "原始音檔路徑",
  "processed_audio": "processed_audio/test3_processed.wav",
  "sample_rate": 22050,
  "original_seconds": 8.1234,
  "trimmed_seconds": 7.5600
}
```

後面步驟 5 用的是寫出來的 `.wav`，不是這個 dict。

---

### 步驟 5. 把處理後的音檔轉成 MIDI

函式：`convert_audio_to_midi(processed_wav, output_midi)`

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 用 Basic Pitch（ONNX）辨識音符，並存成 MIDI |
| 寫出檔案 | `converted_midi/<音檔名>_converted.mid` |
| 程式回傳 | **Python dict**（含模型辨識到的音符） |
| 資料格式 | 檔案是 **MIDI**；回傳是 **dict** |

回傳欄位：

```text
{
  "source_audio": "前處理後 wav 路徑",
  "output_midi": "converted_midi/test3_converted.mid",
  "model_output_keys": ["note", "onset", ...],
  "note_count": 18,
  "notes": [ 音符dict, ... ]
}
```

模型音符（與步驟 3 略有不同，多了 `amplitude`，沒有 `velocity`）：

```text
{
  "pitch": 60,
  "pitch_name": "C4",
  "start": 0.12,
  "end": 0.48,
  "duration": 0.36,
  "amplitude": 0.73
}
```

`main()` 之後會再讀一次寫出的 `.mid`（步驟 6），評分用的是讀檔結果，不是這個模型 notes 列表。

---

### 步驟 6. 讀取轉出來的學生 MIDI

函式：`read_midi_notes(converted_midi_path, "學生演奏（由音檔轉出）")`

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 跟步驟 3 一樣讀 MIDI，只是讀的是步驟 5 轉出的檔 |
| 寫出檔案 | 無 |
| 程式回傳 | **Python dict**（格式與步驟 3 相同） |
| 資料格式 | dict |

學生 MIDI 的拍號／Tempo **不會拿來切小節**。小節一律依標準答案切。

---

### 步驟 7. 用 DTW 把學生音符對到標準答案

函式：`align_notes_with_dtw(standard_notes, student_notes)`

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 建立成本矩陣（同音高成本 1、不同音高成本 100），用 DTW 找對應。只接受音高完全相同的配對 |
| 寫出檔案 | 無 |
| 程式回傳 | **Python dict** |
| 資料格式 | dict |

回傳欄位：

```text
{
  "pairs": [ 每一顆標準音的配對, ... ],
  "standard_to_student": [3, -1, 5, ...],   # 標準音 i 對到學生音編號；-1 代表沒對到
  "extra_student_indexes": [2, 9]           # 多彈、沒配到的學生音編號
}
```

每一組 pair：

```text
{
  "standard_index": 0,
  "student_index": 3,          # 沒對到是 -1
  "standard_pitch": 60,
  "standard_pitch_name": "C4",
  "standard_start": 0.0,
  "matched": true,
  "student_pitch": 60,         # 沒對到是 null
  "student_start": 0.15
}
```

---

### 步驟 8. 比對音高

在 `score_performance()` 裡一起算。

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 已配對且音高相同 → 算對。沒配到 → 漏音。多出來的學生音 → 多彈（不扣分） |
| 滿分 | 70 分 |
| 寫出檔案 | 無 |
| 產出 | 分數與計數，放進步驟 11 的 dict |

公式：`正確音高數 / 標準音符數 × 70`

---

### 步驟 9. 比對節奏

同樣在 `score_performance()` 裡。

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 先用相鄰已配對音符的 IOI（開始時間間隔）算整體速度比例 `tempo_ratio`，再逐段比節奏 |
| 滿分 | 30 分 |
| 寫出檔案 | 無 |
| 產出 | 每段 IOI 的 dict 列表（只存在函式內部，最後分數進步驟 11） |

單一間隔權重：誤差 ≤ 50ms 或比例誤差 ≤ 10% → `1`；比例誤差 ≤ 20% → `0.5`；否則 `0`。

內部 IOI 明細格式：

```text
{
  "from_standard_index": 0,
  "to_standard_index": 1,
  "standard_ioi": 0.5,
  "student_ioi": 0.62,
  "weight": 0.5
}
```

`tempo_ratio > 1` 代表學生整體偏慢，`< 1` 代表偏快。

---

### 步驟 10. 依標準答案切小節

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 用標準答案的拍號與 Tempo 算「一小節幾秒」，再依標準音符開始時間切小節 |
| 限制 | **不支援弱起**；第一顆標準音當第 1 小節開頭 |
| 寫出檔案 | 無 |
| 產出 | 每顆標準音的小節編號，供步驟 11 摘要使用 |

例如 4/4、120 BPM → 一拍 0.5 秒，一小節 2 秒。

---

### 步驟 11. 計算整首總分與每小節摘要

函式：`score_performance()` 回傳的 dict，再加上 `build_measure_summaries()`、`build_error_notes()`。

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 音高 70 + 節奏 30，四捨五入成整數總分；整理每小節與錯音 |
| 寫出檔案 | 無 |
| 程式回傳 | **Python dict** |

回傳欄位：

```text
{
  "standard_note_count": 16,
  "correct_pitch_count": 14,
  "missing_notes": 2,
  "wrong_notes": 0,
  "extra_notes": 1,
  "pitch_score": 61.25,
  "rhythm_score": 22.5,
  "tempo_ratio": 1.04,
  "ioi_count": 15,
  "raw_total": 83.75,
  "final_score": 84,
  "measures": [ 小節摘要, ... ],
  "error_notes": [ 錯音, ... ]
}
```

小節摘要：

```text
{
  "measure_number": 1,
  "standard_note_count": 4,
  "correct_pitch_count": 3,
  "missing_notes": 1,
  "wrong_notes": 0,
  "extra_notes": 0,
  "pitch_text": "3 / 4",
  "rhythm_text": "2.5 / 3"
}
```

錯音：

```text
{
  "measure_number": 2,
  "note_in_measure": 3,          # 多彈時是 null
  "pitch_name": "E4",
  "reason": "漏音"               # 或節奏稍快／稍慢／偏快／偏慢／多彈（不扣分）
}
```

`wrong_notes` 目前固定是 `0`，因為不同音高不會被配成一對，只會變成漏音或多彈。

---

### 步驟 12. 用 Pydantic 整理成結構化結果

函式：`build_score_report()` → `ScoreReport`

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 把步驟 11 的 dict 加上檔名、拍號、Tempo，收成固定欄位 |
| 寫出檔案 | **無** |
| 程式回傳 | **Pydantic 物件 `ScoreReport`** |
| 可轉成 | **JSON 字串**（`score_report.model_dump_json()`），給步驟 13 使用 |

JSON 長這樣（精簡示例）：

```json
{
  "standard_midi": "backend/audio_scoring/midi_test_data/test1.mid",
  "student_audio": "backend/audio_scoring/audio_test_data/test3.mp3",
  "time_signature": "4/4",
  "tempo_bpm": 120.0,
  "pickup_supported": false,
  "standard_note_count": 16,
  "student_note_count": 18,
  "correct_pitch_count": 14,
  "missing_notes": 2,
  "extra_notes": 1,
  "pitch_score": 61.25,
  "rhythm_score": 22.5,
  "tempo_ratio": 1.04,
  "raw_total": 83.75,
  "final_score": 84,
  "measures": [
    {
      "measure_number": 1,
      "standard_note_count": 4,
      "correct_pitch_count": 4,
      "missing_notes": 0,
      "wrong_notes": 0,
      "extra_notes": 0,
      "pitch_text": "4 / 4",
      "rhythm_text": "3.0 / 3"
    }
  ],
  "error_notes": [
    {
      "measure_number": 2,
      "note_in_measure": 1,
      "pitch_name": "G4",
      "reason": "漏音"
    }
  ]
}
```

---

### 步驟 13. 把結構化結果交給 LLM，產生文字回饋

函式：`generate_feedback(score_report)`

| 項目 | 內容 |
| --- | --- |
| 做什麼 | 把步驟 12 的 JSON 字串傳給 Gemini（`gemini-3.8-flash`） |
| 寫出檔案 | 無 |
| 程式回傳 | `(回饋文字, 錯誤訊息)`，兩個都是字串或 `None` |
| 資料格式 | **純文字**，不是 JSON |

成功：`("這次整體彈得很不錯！...", None)`  
失敗：`(None, "沒有設定 GEMINI_API_KEY...")`

---

## 終端機最後印出什麼

函式：`print_test_summary()`，格式是 **純文字**：

```text
測試檔案
標準答案 MIDI：...
學生演奏音檔：...
讀取結果：成功
標準答案音符數：16
使用者音符數：18
音高分數：61.25 分
節奏分數：22.5 分
最後分數：84 分
錯音：
第 2 小節第 1 顆 G4：漏音
AI 回饋：
（Gemini 文字，或錯誤原因）
執行時間：12.34 秒
```

---

## 一句話對照：每步是檔案還是 JSON？

| 步驟 | 主要產出 | 格式 |
| --- | --- | --- |
| 1 | 標準 MIDI | `.mid` 檔 |
| 2 | 學生音檔 | `.wav` / `.mp3` 等 |
| 3 | 標準音符 | Python dict |
| 4 | 前處理音訊 | `.wav` 檔 + Python dict |
| 5 | 學生 MIDI | `.mid` 檔 + Python dict |
| 6 | 學生音符 | Python dict |
| 7 | 對齊結果 | Python dict |
| 8 | 音高分數 | 數字，放在 dict 裡 |
| 9 | 節奏分數 | 數字，放在 dict 裡 |
| 10 | 小節切分 | 數字編號，放在 dict 裡 |
| 11 | 總分與摘要 | Python dict |
| 12 | 評分報告 | Pydantic，**可轉 JSON**（不存檔） |
| 13 | AI 回饋 | 純文字字串 |
| 畫面輸出 | 測試摘要 | 純文字 |
