"""AI出題系統

目前只有兩個 view 函數：
    POST /api/upload     上傳教材（pdf / txt），回傳 doc_id
    GET  /api/questions  依 doc_id 取得 AI 出的題目

使用 openai api 呼叫模型
"""

import io
import json
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

import fitz  # PyMuPDF：讀取 PDF 文字、把頁面轉成圖片給 OCR
import pytesseract
from fastapi import FastAPI, File, HTTPException, UploadFile, APIRouter
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
#from PIL import Image

load_dotenv()

# ----------------------------------------------------------------------------
# 設定
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
#OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
#OCR_LANG = os.getenv("OCR_LANG", "chi_tra+eng")  # 需安裝對應 tesseract 語言包
#OCR_LANG = "chi_tra"  # 需安裝對應 tesseract 語言包

MIN_TEXT_CHARS_PER_PAGE = 20  # 頁面文字少於此數量，視為掃描頁，改用 OCR
MAX_MATERIAL_CHARS = 30000  # 送進模型的教材長度上限
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
#OCR_ZOOM = 2.0  # 頁面轉圖放大倍率，越大 OCR 越準但越慢


def get_openai_client():
    """
    根據 .env 設定，動態初始化並回傳 OpenAI Client 與對應的模型名稱
    """
    # 將字串轉為布林值
    use_local = os.getenv("USE_LOCAL_MODEL", "False").lower() == "true"
    
    if use_local:
        # 使用本地模型
        client = OpenAI(
            base_url=os.getenv("LOCAL_API_URL", "http://localhost:11434/v1"),
            api_key="ollama"  # 本地 Ollama 不需要 key，但 SDK 要求必填，隨便給個字串即可
        )
        model_name = os.getenv("LOCAL_MODEL_NAME", "llama3")
    else:
        # 使用雲端模型
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        
    return client, model_name

client, MODEL_NAME = get_openai_client()

# 教材暫存在記憶體，重啟後消失
DOCS: dict[str, dict] = {}

# 出題邏輯全部寫在 system prompt
SYSTEM_PROMPT = """你是一位專業的出題老師，負責根據使用者提供的教材內容出題。

# 出題原則
1. 題目必須完全根據教材內容，不可使用教材以外的知識，也不可捏造教材沒有的資訊。
2. 題型為四選一的單選題，每題有且只有一個正確答案。
3. 題目要涵蓋教材中不同的重要概念，避免重複或過度集中在同一段落。
4. 難度由淺入深：先考記憶與理解，再考應用與比較。
5. 干擾選項要合理、有迷惑性，但不可有爭議或同時正確的情況。
6. 題目與選項使用與教材相同的語言（教材為中文則用繁體中文）。
7. 每題附上簡短解析，說明為什麼答案正確，必要時指出教材依據。
8. 若教材內容不足以出到要求的題數，就只出能出的題數，不要硬湊。

# 輸出格式
只輸出一個 JSON 物件，不要有任何其他文字，格式如下：
{
  "questions": [
    {
      "question": "題目文字",
      "options": ["選項A內容", "選項B內容", "選項C內容", "選項D內容"],
      "answer": 0,
      "explanation": "解析文字"
    }
  ]
}
其中 answer 是正確選項在 options 中的索引（0~3）。options 內容不要包含 A/B/C/D 前綴。"""


# ----------------------------------------------------------------------------
# 教材文字萃取
# ----------------------------------------------------------------------------
def decode_text_bytes(data: bytes) -> str:
    """TXT 解碼：依序嘗試常見編碼。"""
    
    for enc in ("utf-8-sig", "utf-8", "big5", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    
    return data.decode("utf-8", errors="ignore")


def extract_pdf_text(data: bytes) -> str:
    """逐頁取文字；若該頁幾乎沒有文字（掃描檔）就改用 OCR。"""
    
    pages_text = []
    with fitz.open(stream=data, filetype="pdf") as pdf:
        for page in pdf:
            text = page.get_text().strip()
            
            #if len(text) < MIN_TEXT_CHARS_PER_PAGE:
            #    pix = page.get_pixmap(matrix=fitz.Matrix(OCR_ZOOM, OCR_ZOOM))
            #    image = Image.open(io.BytesIO(pix.tobytes("png")))
            #    text = pytesseract.image_to_string(image, lang=OCR_LANG).strip()
            
            pages_text.append(text)
    
    return "\n\n".join(t for t in pages_text if t)


def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".txt":
        return decode_text_bytes(data).strip()
    if ext == ".pdf":
        return extract_pdf_text(data)
    raise ValueError("目前只支援 .pdf 與 .txt 檔案")


# ----------------------------------------------------------------------------
# AI 出題
# ----------------------------------------------------------------------------
def validate_questions(raw: dict) -> list[dict]:
    """檢查並整理模型回傳的題目，剔除格式不正確的題目。"""
    cleaned = []
    for q in raw.get("questions", []):
        options = q.get("options")
        answer = q.get("answer")
        if (
            isinstance(q.get("question"), str)
            and isinstance(options, list)
            and len(options) == 4
            and isinstance(answer, int)
            and 0 <= answer < 4
        ):
            cleaned.append(
                {
                    "question": q["question"],
                    "options": [str(o) for o in options],
                    "answer": answer,
                    "explanation": str(q.get("explanation", "")),
                }
            )
    return cleaned


def generate_questions(material: str, num: int) -> list[dict]:
    """system prompt（出題邏輯）→ 教材 → 出題指令。"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"以下是教材內容：\n\n{material[:MAX_MATERIAL_CHARS]}"},
        {"role": "user", "content": f"請根據以上教材出 {num} 題單選題，並依照指定的 JSON 格式輸出。"},
    ]
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    print(response)
    raw = json.loads(response.choices[0].message.content)
    return validate_questions(raw)


# ----------------------------------------------------------------------------
# FastAPI：兩個 view 函數
# ----------------------------------------------------------------------------
router = APIRouter()

@router.post("/teacher/upload")
def upload_material(file: UploadFile = File(...)):
    """上傳教材（pdf / txt），萃取純文字後暫存，回傳 doc_id。"""
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="檔案是空的")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="檔案過大（上限 20MB）")

    try:
        text = extract_text(file.filename or "", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(status_code=500, detail="伺服器未安裝 Tesseract，無法 OCR 掃描檔")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"檔案解析失敗：{e}")

    if not text:
        raise HTTPException(status_code=400, detail="沒有從檔案中讀到任何文字")

    doc_id = uuid.uuid4().hex
    DOCS[doc_id] = {"filename": file.filename, "text": text}
    return {"doc_id": doc_id, "filename": file.filename, "chars": len(text)}

@router.get("/teacher/questions")
def get_questions(doc_id: str, num: int = 5):
    """依 doc_id 取得教材並請 AI 出題。"""
    doc = DOCS.get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="找不到該教材，請重新上傳")
    num = max(1, min(num, 20))

    try:
        questions = generate_questions(doc["text"], num)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 出題失敗：{e}")

    if not questions:
        raise HTTPException(status_code=502, detail="AI 沒有產生有效題目，請再試一次")
    return {"filename": doc["filename"], "questions": questions}
