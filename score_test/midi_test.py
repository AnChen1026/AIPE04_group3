# 演奏評分測試：目前只做步驟 1、2
# 1. 準備標準答案 MIDI
# 2. 準備測試音檔（先用現成檔，不用瀏覽器錄音）
#
# 使用方式：
#   1. 把標準答案 MIDI 放到 score_test/midi_test_data/
#   2. 把測試音檔放到 score_test/audio_test_data/
#   3. 在專案根目錄執行：python score_test/midi_test.py
#
# 或直接在指令帶路徑：
#   python score_test/midi_test.py --midi 標準答案.mid --audio 測試音檔.wav

from pathlib import Path  # 處理檔案路徑，避免自己拼字串
import argparse  # 讀取指令列參數，例如 --midi、--audio
import sys  # 結束程式時回傳成功或失敗代碼

# 這個 .py 所在的資料夾（score_test/），用來組相對路徑
BASE_DIR = Path(__file__).resolve().parent
MIDI_DIR = BASE_DIR / "midi_test_data"
AUDIO_DIR = BASE_DIR / "audio_test_data"

# ======================================================
# 步驟 1：標準答案 MIDI（請把檔案放到這個相對路徑）
# ======================================================
MIDI_PATH = MIDI_DIR / "test1.mid"

# ======================================================
# 步驟 2：測試音檔（請把檔案放到這個相對路徑）
# ======================================================
AUDIO_PATH = AUDIO_DIR / "test1.wav"

MIDI_SUFFIXES = {".mid", ".midi"}
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}


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

    size_kb = file_path.stat().st_size / 1024
    print(f"[成功] {label}")
    print(f"       路徑：{file_path.resolve()}")
    print(f"       大小：{size_kb:.1f} KB")
    return True


# ======================================================
# 讀取指令列參數：可用 --midi、--audio 覆蓋檔案上方的預設路徑
# ======================================================
def parse_args():
    """解析指令列，讓測試時不必改程式裡的預設路徑。"""
    parser = argparse.ArgumentParser(description="載入標準 MIDI 與測試音檔")
    parser.add_argument("--midi", type=Path, default=MIDI_PATH, help="標準答案 MIDI 檔")
    parser.add_argument("--audio", type=Path, default=AUDIO_PATH, help="測試用音檔")
    return parser.parse_args()


# ======================================================
# 測試入口：依序檢查標準答案 MIDI 與測試音檔是否就緒
# ======================================================
def main():
    """執行步驟 1、2，確認兩個輸入檔都準備好。"""
    args = parse_args()

    print("=== 演奏評分測試：步驟 1、2 ===")
    midi_ok = check_input_file(args.midi, MIDI_SUFFIXES, "標準答案 MIDI")
    audio_ok = check_input_file(args.audio, AUDIO_SUFFIXES, "測試音檔")

    if midi_ok and audio_ok:
        print("兩個檔案都準備好了。下一步才會讀取 MIDI 內容與處理音訊。")
        return 0

    print("請先修正上面的檔案路徑後再執行一次。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
