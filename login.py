# -*- coding: utf-8 -*-
"""
會員系統 — 純終端機 CLI 版
─────────────────────────────────────────────
功能：
  1. 老師登入 / 學生登入（分開）
  2. 註冊（學生 / 老師）
  3. 修改資料（名字 / 性別 / Email / 手機）
  4. 修改密碼
  5. 忘記密碼（名字 + Email 或手機驗證）
  6. 登出

規則：
  · 名字、Email、手機皆允許重複
  · 但「名字 + Email」或「名字 + 手機」不可同時重複
  · 密碼長度 6～8 位
  · 資料存於程式所在目錄的 users_data.json
"""

import json
import os
import re
import shutil
import sys
import tempfile
import time
import unicodedata
import uuid

from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users_data.json")

GENDER_MAP = {
    "1": "男",
    "2": "女",
    "3": "其他",
    "4": "不透露",
}


class DatabaseError(Exception):
    """資料檔無法讀取或已損毀"""


# ══════════════════════════════════════════════════════════════
# 資料存取
# ══════════════════════════════════════════════════════════════
def _empty_db():
    return {"teachers": {}, "students": {}}


def _backup_corrupt_file():
    """把損毀的資料檔另存一份，回傳備份路徑（失敗回傳 None）"""
    ts = time.strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:6]           # ★ 修正 2：加 UUID，同秒也不覆蓋
    dst = f"{DB_FILE}.corrupt-{ts}-{suffix}.bak"
    try:
        shutil.copy2(DB_FILE, dst)
        return dst
    except OSError:
        return None


def load_db():
    if not os.path.exists(DB_FILE):
        return _empty_db()
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("最外層不是物件")
        for key in ("teachers", "students"):
            data.setdefault(key, {})
            if not isinstance(data[key], dict):
                raise ValueError(f"「{key}」格式錯誤")
        return data
    except OSError as e:
        raise DatabaseError(f"無法讀取資料檔 {DB_FILE}：{e}") from e
    except ValueError as e:
        backup = _backup_corrupt_file()
        hint = f"已備份到 {backup}" if backup else "備份失敗，請手動保留原檔"
        raise DatabaseError(
            f"資料檔已損毀（{e}）。原檔未被修改，{hint}。"
            f"請修復或移除 {DB_FILE} 後再執行。"
        ) from e


def save_db(data):
    """原子寫入：暫存檔 → fsync → os.replace 覆蓋正式檔"""
    directory = os.path.dirname(DB_FILE) or "."
    fd, tmp_path = tempfile.mkstemp(
        dir=directory, prefix=".users_data-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, DB_FILE)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


# ══════════════════════════════════════════════════════════════
# 終端機工具
# ══════════════════════════════════════════════════════════════
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.ASCII)
PHONE_RE = re.compile(r"\+?[0-9]{8,15}", re.ASCII)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="─", n=48):
    print(char * n)


def title(text):
    clear()
    line("═")
    print(f"  {text}")
    line("═")


def bye():
    print("\n\n👋 再見！")
    sys.exit(0)


def ask(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        bye()


def ask_password(prompt="密碼: "):
    try:
        import getpass
        return getpass.getpass(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        bye()
    except Exception:
        print("⚠️  此環境無法隱藏密碼輸入，輸入內容將會顯示")
        return ask(prompt)


def pause():
    try:
        input("\n按 Enter 繼續...")
    except (EOFError, KeyboardInterrupt):
        bye()


def print_gender_options():
    print("  1. 男")
    print("  2. 女")
    print("  3. 其他")
    print("  4. 不透露")


def choose_gender(prompt="請選擇 (1-4): ", allow_skip=False):
    """allow_skip=True 時，Enter 回傳 None（不修改）；選項無效回傳 "" """
    print_gender_options()
    if allow_skip:
        print("  （直接按 Enter 不修改）")
    choice = ask(prompt)
    if not choice and allow_skip:
        return None
    return GENDER_MAP.get(choice, "")


# ══════════════════════════════════════════════════════════════
# 驗證工具
# ══════════════════════════════════════════════════════════════
def validate_name(name):
    if not (1 <= len(name) <= 30):
        return "名字長度需為 1～30 字"
    if any(unicodedata.category(ch).startswith("C") for ch in name):
        return "名字不可包含控制字元或不可見字元"
    return None


def validate_password(pw):
    if not (6 <= len(pw) <= 8):
        return "密碼長度需為 6～8 位"
    return None


def normalize_email(email):
    return email.strip().lower()


def email_equal(stored, given):
    """Email 比對（不分大小寫；空字串永遠不相等）"""
    return bool(given) and (stored or "").lower() == given.lower()


def find_users_by_name(db, name, role_key=None):
    keys = [role_key] if role_key else ("teachers", "students")
    result = []
    for rk in keys:
        for uid, u in db[rk].items():
            if u.get("name") == name:
                result.append((rk, uid, u))
    return result


def find_conflict(db, name, email, phone, exclude_uid=None):
    """檢查「名字 + Email」或「名字 + 手機」是否已被使用（跨身分）"""
    for rk in ("teachers", "students"):
        for uid, u in db[rk].items():
            if uid == exclude_uid or u.get("name") != name:
                continue
            if email and email_equal(u.get("email"), email):
                return ("Email", email)
            if phone and u.get("phone") == phone:
                return ("手機", phone)
    return None


# ══════════════════════════════════════════════════════════════
# 註冊
# ══════════════════════════════════════════════════════════════
def register():
    title("📝 註冊")

    print("身分：")
    print("  1. 學生")
    print("  2. 老師")
    choice = ask("請選擇 (1/2): ")
    if choice not in ("1", "2"):
        print("❌ 無效選擇")
        pause()
        return
    role = "teacher" if choice == "2" else "student"
    role_key = "teachers" if role == "teacher" else "students"
    prefix = "T" if role == "teacher" else "S"

    name = ask("名字: ")
    err = validate_name(name)
    if err:
        print(f"❌ {err}")
        pause()
        return

    print("\n性別：")
    gender = choose_gender()
    if not gender:
        print("❌ 無效選擇")
        pause()
        return

    email = normalize_email(ask("Email（沒有可留空）: "))
    phone = ask("手機號（沒有可留空）: ")

    if not email and not phone:
        print("❌ Email 與手機號至少需填寫一項")
        pause()
        return
    if email and not EMAIL_RE.fullmatch(email):
        print("❌ Email 格式不正確")
        pause()
        return
    if phone and not PHONE_RE.fullmatch(phone):
        print("❌ 手機號格式不正確（僅數字，長度 8～15）")
        pause()
        return

    pw = ask_password("設定密碼（6～8 位）: ")
    err = validate_password(pw)
    if err:
        print(f"❌ {err}")
        pause()
        return

    pw2 = ask_password("再次輸入密碼: ")
    if pw != pw2:
        print("❌ 兩次輸入的密碼不一致")
        pause()
        return

    db = load_db()
    conflict = find_conflict(db, name, email, phone)
    if conflict:
        kind, value = conflict
        print(f"❌ 「{name}」+ {kind}「{value}」已註冊過")
        pause()
        return

    while True:
        new_id = f"{prefix}-{os.urandom(4).hex()}"
        if new_id not in db[role_key]:
            break

    db[role_key][new_id] = {
        "name": name,
        "gender": gender,
        "email": email,
        "phone": phone,
        "password_hash": generate_password_hash(pw),
    }
    save_db(db)

    print(f"\n✅ 註冊成功！")
    print(f"   你的 ID：{new_id}")
    print(f"   登入方式：選「{'老師' if role == 'teacher' else '學生'}登入」")
    print(f"             + 名字「{name}」+ 你設定的密碼")
    pause()


# ══════════════════════════════════════════════════════════════
# 登入（依身分分開）
# ══════════════════════════════════════════════════════════════
def login(role):
    """
    role: 'teacher' 或 'student'
    成功回傳 (role, uid)；失敗回傳 None
    ★ 不再回傳 name，讓 dashboard() 自己從 db 讀，避免雙重來源
    """
    role_key = "teachers" if role == "teacher" else "students"
    role_label = "老師" if role == "teacher" else "學生"

    title(f"🔑 {role_label}登入")

    name = ask("名字: ")
    pw = ask_password("密碼: ")

    db = load_db()
    candidates = find_users_by_name(db, name, role_key=role_key)

    matched_uid = None
    for _, uid, user in candidates:
        if check_password_hash(user.get("password_hash", ""), pw):
            matched_uid = uid
            break

    if not matched_uid:
        print("\n❌ 名字或密碼錯誤")
        pause()
        return None

    if len(candidates) > 1:
        print(f"\n⚠️  系統中有 {len(candidates)} 位名叫「{name}」的{role_label}，")
        print(f"   已依密碼為你配對到：{matched_uid}")

    print(f"\n✅ {role_label}登入成功！歡迎，{name}")
    pause()
    return (role, matched_uid)


# ══════════════════════════════════════════════════════════════
# 儀表板（自行從 db 讀資料，不依賴外部傳入的 name）
# ══════════════════════════════════════════════════════════════
def dashboard(role, uid):
    role_label = "老師" if role == "teacher" else "學生"
    role_key = "teachers" if role == "teacher" else "students"

    while True:
        db = load_db()
        user = db[role_key].get(uid)
        if not user:
            print("❌ 帳號不存在（可能已被刪除）")
            pause()
            return

        title(f"👋 {user.get('name', '')}（{role_label}）")

        print(f"  ID     : {uid}")
        print(f"  名字   : {user.get('name', '')}")
        print(f"  性別   : {user.get('gender') or '—'}")
        print(f"  Email  : {user.get('email') or '—'}")
        print(f"  手機   : {user.get('phone') or '—'}")
        line()
        print("  1. ✏️  修改資料（名字 / 性別 / Email / 手機）")
        print("  2. 🔒 修改密碼")
        print("  3. 🚪 登出")
        print("  0. ❌ 離開程式")
        line()

        choice = ask("請選擇: ")

        if choice == "1":
            edit_profile(role, uid)
        elif choice == "2":
            change_password(role, uid)
        elif choice == "3":
            print("\n👋 已登出")
            pause()
            return
        elif choice == "0":
            print("\n👋 再見！")
            sys.exit(0)
        else:
            print("❌ 無效選擇")
            pause()


# ══════════════════════════════════════════════════════════════
# 修改資料
# ══════════════════════════════════════════════════════════════
def edit_profile(role, uid):
    title("✏️  修改資料")

    db = load_db()
    role_key = "teachers" if role == "teacher" else "students"
    user = db[role_key].get(uid)
    if not user:
        print("❌ 找不到帳號")
        pause()
        return

    print("直接按 Enter 表示不修改該欄位\n")

    print(f"目前名字  ：{user.get('name', '')}")
    new_name = ask("新名字    : ") or user.get("name", "")
    err = validate_name(new_name)
    if err:
        print(f"❌ {err}")
        pause()
        return

    print(f"\n目前性別  ：{user.get('gender') or '—'}")
    print("新性別：")
    result = choose_gender("請選擇 (1-4): ", allow_skip=True)

    if result is None:
        new_gender = user.get("gender", "")
    elif result == "":
        print("❌ 無效性別選項")
        pause()
        return
    else:
        new_gender = result

    print(f"\n目前 Email：{user.get('email') or '—'}")
    new_email = normalize_email(ask("新 Email  : "))
    if not new_email:
        new_email = user.get("email", "")
    elif not EMAIL_RE.fullmatch(new_email):
        print("❌ Email 格式不正確")
        pause()
        return

    print(f"\n目前手機  ：{user.get('phone') or '—'}")
    new_phone = ask("新手機    : ")
    if not new_phone:
        new_phone = user.get("phone", "")
    elif not PHONE_RE.fullmatch(new_phone):
        print("❌ 手機號格式不正確（僅數字，長度 8～15）")
        pause()
        return

    if not new_email and not new_phone:
        print("❌ Email 與手機號至少需填寫一項")
        pause()
        return

    conflict = find_conflict(db, new_name, new_email, new_phone, exclude_uid=uid)
    if conflict:
        kind, value = conflict
        print(f"❌ 「{new_name}」+ {kind}「{value}」已被使用")
        pause()
        return

    user["name"] = new_name
    user["gender"] = new_gender
    user["email"] = new_email
    user["phone"] = new_phone
    save_db(db)

    print("\n✅ 資料已更新")
    pause()


# ══════════════════════════════════════════════════════════════
# 修改密碼
# ══════════════════════════════════════════════════════════════
def change_password(role, uid):
    title("🔒 修改密碼")

    old = ask_password("舊密碼: ")
    new = ask_password("新密碼（6～8 位）: ")

    err = validate_password(new)
    if err:
        print(f"❌ {err}")
        pause()
        return

    new2 = ask_password("再次輸入新密碼: ")
    if new != new2:
        print("❌ 兩次輸入的新密碼不一致")
        pause()
        return

    db = load_db()
    role_key = "teachers" if role == "teacher" else "students"
    user = db[role_key].get(uid)
    if not user:
        print("❌ 找不到帳號")
        pause()
        return

    if not check_password_hash(user.get("password_hash", ""), old):
        print("❌ 舊密碼錯誤")
        pause()
        return

    if new == old:
        print("❌ 新密碼不能與舊密碼相同")
        pause()
        return

    user["password_hash"] = generate_password_hash(new)
    save_db(db)

    print("\n✅ 密碼已更新")
    pause()


# ══════════════════════════════════════════════════════════════
# 忘記密碼
# ══════════════════════════════════════════════════════════════
def forgot_password():
    title("🆘 忘記密碼")

    print("請輸入名字，以及註冊時填的 Email 或手機號來驗證身分。\n")

    name = ask("名字: ")
    contact = ask("Email 或手機號: ")

    if not name or not contact:
        print("\n❌ 名字與 Email／手機號都必須填寫")
        pause()
        return

    new = ask_password("新密碼（6～8 位）: ")

    err = validate_password(new)
    if err:
        print(f"❌ {err}")
        pause()
        return

    new2 = ask_password("再次輸入新密碼: ")
    if new != new2:
        print("❌ 兩次輸入的新密碼不一致")
        pause()
        return

    db = load_db()
    matches = []
    for role_key in ("teachers", "students"):
        for uid, u in db[role_key].items():
            if u.get("name") != name:
                continue
            phone = u.get("phone")
            if email_equal(u.get("email"), contact) or (phone and phone == contact):
                matches.append((role_key, uid, u))

    if not matches:
        print("\n❌ 查無此帳號，請確認名字與聯絡方式是否正確")
        pause()
        return

    new_hash = generate_password_hash(new)
    for _, _, u in matches:
        u["password_hash"] = new_hash
    save_db(db)

    print(f"\n✅ 密碼已重設（共 {len(matches)} 筆帳號）")
    if len(matches) > 1:
        print("   因資料重複，符合條件的帳號皆已更新為同一組新密碼。")
    pause()


# ══════════════════════════════════════════════════════════════
# 主選單
# ══════════════════════════════════════════════════════════════
def main_menu():
    while True:
        title("🎯 會員系統（CLI 版）")

        print("  1. 🔑 老師登入")
        print("  2. 🔑 學生登入")
        print("  3. 📝 註冊")
        print("  4. 🆘 忘記密碼")
        print("  0. ❌ 離開")
        line()

        choice = ask("請選擇: ")

        if choice == "1":
            result = login("teacher")
            if result:
                dashboard(*result)          # (role, uid)
        elif choice == "2":
            result = login("student")
            if result:
                dashboard(*result)
        elif choice == "3":
            register()
        elif choice == "4":
            forgot_password()
        elif choice == "0":
            print("\n👋 再見！")
            break
        else:
            print("❌ 無效選擇")
            pause()


def main():
    try:
        main_menu()
    except (DatabaseError, OSError) as e:   # ★ 修正 1：也捕捉 OSError
        print(f"\n❌ {e}")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════
# 進入點
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if os.name == "nt":
        os.system("chcp 65001 > nul")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再見！")
