# AI 找課每日啟動與排錯

適用：Render 網站搭配 Mac 上的 Ollama、受金鑰保護的閘道與 Cloudflare 臨時通道。Docker 包裝的是網站環境，並未把 Mac 的模型服務一起搬到 Render。

連線順序：瀏覽器 → Render → HTTPS 通道 → 本機閘道（18763）→ Ollama（11434）。

## 這台 Mac 的背景服務（2026-11-01）

本次切換已完成 Render 環境變數更新與重新部署。驗收：固定 ngrok 通道未帶金鑰回傳 401、帶金鑰 Qwen 回傳 200、BGE-M3 回傳 200 與 1024 維向量；ngrok 背景服務重啟後網址不變；公開站輸入「我想學電影配樂」回傳 200 與 3 門課程，無排序降級提示。舊 cloudflared 通道已停止。這是基本連線驗收，不代表複合條件解析與長期可用性已全面通過。

已將閘道與 ngrok 安裝為目前使用者的 macOS LaunchAgent，登入後自動啟動，異常退出時自動重啟。這些設定在本機使用者目錄，不會隨 Git 自動部署到其他電腦。ngrok 使用目前帳號的固定開發網址；Render 使用相同網址。Ollama 仍由 Ollama 應用程式提供，請確認應用程式已開啟；本次未變更其登入啟動設定。Mac 關機、登出、休眠或斷網仍會中斷服務。

正常情況下，不必再手動啟動另一份 uvicorn 或 ngrok，也不必重部署 Render。檢查服務：

```sh
launchctl print "gui/$(id -u)/tw.aipe04.shared-ai-gateway"
launchctl print "gui/$(id -u)/tw.aipe04.shared-ai-ngrok"
```

輸出應包含 `state = running`。需要重啟時：

```sh
launchctl kickstart -k "gui/$(id -u)/tw.aipe04.shared-ai-gateway"
launchctl kickstart -k "gui/$(id -u)/tw.aipe04.shared-ai-ngrok"
```

只重啟服務即可，不更換網址或金鑰。ngrok 設定檔為 `~/Library/Application Support/ngrok/ngrok.yml`；閘道啟動腳本及兩個服務的日誌在 `~/Library/Application Support/AIPE04SharedAI/`。LaunchAgent 的 plist 在 `~/Library/LaunchAgents/tw.aipe04.shared-ai-*.plist`。請勿分享含憑證的 ngrok 設定檔。

要暫停背景服務，使用下列命令；單純 kill 會被自動重啟：

```sh
launchctl bootout "gui/$(id -u)/tw.aipe04.shared-ai-ngrok"
launchctl bootout "gui/$(id -u)/tw.aipe04.shared-ai-gateway"
```

同一次登入期間，暫停後要恢復：

```sh
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/tw.aipe04.shared-ai-gateway.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/tw.aipe04.shared-ai-ngrok.plist"
```

以下手動流程適合尚未配置背景服務的電腦，或排錯參考；不要與現有背景服務重複啟動。

## 每次測試前的啟動順序

### 1. 開啟 Ollama，確認模型存在

開啟 Mac 的 Ollama 應用程式，或在獨立終端機執行 `ollama serve`（二擇一，已運行時不必重複啟動）。

```sh
curl --fail --max-time 5 http://127.0.0.1:11434/api/tags
ollama list
```

清單應包含 `qwen3:4b-instruct-2507-q4_K_M` 與 `bge-m3:567m`。若尚未下載，首次執行：

```sh
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama pull bge-m3:567m
```

### 2. 啟動閘道（終端機 A）

```sh
cd /Users/olliehu/iSpan/AIPE04_group3
source .venv/bin/activate
lsof -nP -iTCP:18763 -sTCP:LISTEN
```

如果已有程序監聽，先用下方驗證步驟檢查，正常就沿用。沒有程序時才執行：

```sh
export AI_GATEWAY_TOKEN="$(cat .scratch/shared-ai/gateway-token)"
python -m uvicorn scripts.local_ai_gateway:app \
  --host 127.0.0.1 --port 18763 --no-access-log
```

看到 `Uvicorn running on http://127.0.0.1:18763` 後保持終端機開啟。金鑰不存在時，依 [首次設定手冊](shared-local-ai.md) 建立；日常啟動不要重新產生金鑰。

### 3. 啟動 HTTPS 通道（終端機 B）

建議優先使用 ngrok 帳號的固定開發網址，避免重啟後反覆更新 Render。以下為 ngrok 模式；Cloudflare 臨時通道保留為備用，兩種方式擇一。

首次安裝並依 ngrok Dashboard 指示設定帳號 authtoken（這是 ngrok 的憑證，與閘道 Bearer 金鑰不同；不要提交到 Git）：

```sh
brew install --cask ngrok
```

完成帳號憑證設定後執行：

```sh
ngrok http http://127.0.0.1:18763 --inspect=false
```

`--inspect=false` 關閉本機 HTTP 請求檢視，減少對話內容及驗證標頭被本機檢視工具記錄的機會。免費帳號的 `ngrok http` 預設使用帳號分配的固定開發網址，程序重啟時網址不變；以實際輸出的 Forwarding 網址為準。Render 的 `AI_COURSE_GATEWAY_URL` 首次換成此 HTTPS 網址，保留原有閘道金鑰與 BGE-M3 digest，再部署。之後網址和金鑰未變就不必重部署。切換前先依下方逐段驗證測試 ngrok，確認公開站成功後再停止舊 cloudflared。

固定網址不等於服務自動啟動；仍須保持 Ollama、閘道及 ngrok 運作。背景服務可另外配置，尚未配置前請保持終端機開啟。免費方案有流量／請求額度，請在 Dashboard Usage 查看；它不會讓休眠或關機的 Mac 繼續提供模型。

參考：[ngrok 免費方案與固定網址](https://ngrok.com/docs/pricing-limits/free-plan-limits)。

Cloudflare 臨時通道備用方式：

```sh
cloudflared tunnel --url http://127.0.0.1:18763
```

若已有 cloudflared 正常運行，不必重開。記下畫面提供的 `https://….trycloudflare.com`，保持終端機開啟。每次重啟通道，網址可能不同。不要把 Ollama 的 11434 埠直接公開。

### 4. 核對 Render Environment

| 變數 | 設定來源 |
| --- | --- |
| `AI_COURSE_GATEWAY_URL` | 本次通道的 HTTPS 網址，不加結尾 `/` |
| `AI_COURSE_GATEWAY_TOKEN` | 與 `.scratch/shared-ai/gateway-token` 相同 |
| `AI_COURSE_EMBEDDING_VERSION` | 目前 BGE-M3 的完整 digest |

網址、金鑰或 digest 有改變時，更新 Render 並重新部署；沒有改變時，不必每天重新部署。這些都是後端變數，不使用 `VITE_` 前綴。不要將金鑰放進 Git、截圖或聊天。

查詢 BGE-M3 digest（在已啟用 `.venv` 的終端機）：

```sh
python - <<'PY'
import httpx
models = httpx.get('http://127.0.0.1:11434/api/tags', timeout=5).json()['models']
print(next(m['digest'] for m in models if m['name'] == 'bge-m3:567m'))
PY
```

更換 embedding 模型 digest 或修改課程後，依首次設定手冊核對／重建課程索引；不要每次啟動都跑 migration 或重建索引。

### 5. 避免測試期間休眠

接上電源、保持上蓋開啟，在另一個終端機執行：

```sh
caffeinate -i
```

Mac 關機、休眠、斷網或關閉服務後，Render 網站仍可能正常，但 AI 找課會失效。

## 逐段驗證

在專案根目錄、已啟用 `.venv` 的終端機執行。先測本機閘道：

```sh
export AI_TEST_BASE_URL=http://127.0.0.1:18763
```

再執行以下測試，金鑰不會被印出：

```sh
python - <<'PY'
import os
from pathlib import Path
import httpx

url = os.environ['AI_TEST_BASE_URL'].rstrip('/') + '/v1/chat/completions'
token = Path('.scratch/shared-ai/gateway-token').read_text().strip()
try:
    r = httpx.post(url, json={}, timeout=15)
    print('未帶金鑰（預期 401）：', r.status_code)
    r = httpx.post(
        url,
        headers={'Authorization': 'Bearer ' + token},
        json={
            'model': 'qwen3:4b-instruct-2507-q4_K_M',
            'messages': [{'role': 'user', 'content': '只回答：測試成功'}],
            'max_tokens': 40, 'temperature': 0, 'stream': False,
        },
        timeout=80,
    )
    print('帶金鑰（預期 200）：', r.status_code)
    if r.status_code == 200:
        print(r.json()['choices'][0]['message']['content'])
    else:
        print(r.text[:300])
except httpx.HTTPError as error:
    print('連線失敗：', type(error).__name__)
PY
```

本機通過後，把 `AI_TEST_BASE_URL` 改為本次通道網址，再執行同一段 Python：

```sh
export AI_TEST_BASE_URL="https://請替換為本次網址.trycloudflare.com"
```

公開通道也通過後，到公開站重新開始一段找課對話，輸入「我想學電影配樂」。確認有課程結果或合理追問，且無語意排序降級提示。這個簡單測試不能取代複合條件、多輪修正與 BGE-M3／索引的完整驗收。

模型首次載入可能較慢；上述直接測試容許較長等待，但 Render 的需求解析呼叫目前只有 30 秒逾時。直接測試成功但公開站失敗時，也要檢查是否超過這個時限。

## 常見錯誤

| 現象 | 意義與處理 |
| --- | --- |
| `address already in use` | 18763 已有程序。用 `lsof` 查 PID，再以 `ps -p PID -o command=` 確認。不要重開第二份。 |
| 本機 `Connection refused` | 閘道未監聽或已停止；確認 Ollama 與閘道啟動順序。 |
| 不帶金鑰得到 `401` | 正常，表示驗證保護生效。 |
| 帶金鑰仍得到 `401` | 閘道載入的金鑰與檔案不同。停止舊閘道，重新 export 金鑰並啟動；Render 金鑰也須一致。 |
| 閘道 `503 Model unavailable` | Ollama 未啟動、指定模型不存在、模型回應逾時或上游錯誤。 |
| 閘道 `503 Model busy` | 目前僅容許一個模型請求，待上一個完成再試。 |
| 本機成功、HTTPS 失敗 | 通道未連線、網址已改變或外部網路問題。查看 cloudflared 終端機。 |
| HTTPS 成功、Render 顯示 AI 暫時無法使用 | 核對 Render URL／token、是否已部署新設定，並查 Render Logs；也可能是 30 秒逾時或模型輸出不符合 JSON 格式，不能只判定服務沒開。 |
| `422 我還無法確認你的條件` | 條件解析／驗證未通過，與服務未啟動不同。可先用簡單描述驗證連線，再針對原句排查。 |
| 語意排序降級、索引不完整 | 檢查 BGE-M3、digest 與課程索引；Qwen 可回答不等於語意排序正常。 |
| Render `/health` 正常、AI 失敗 | `/health` 不代表模型或通道正常。PR #41 版本只回報程序能回應；後續部署可能新增資料庫檢查，須以實際部署版本為準。 |

需要停止舊閘道時，優先在原終端機按 Ctrl+C。若找不到原視窗，確認 PID 確實是 `scripts.local_ai_gateway:app` 後才執行 `kill PID`，再依步驟 2 重啟。不要使用先前紀錄的固定 PID，也不要終止所有 Python 程序。

## 結束測試

在閘道、cloudflared、caffeinate 各自的終端機按 Ctrl+C。背景啟動的程序需確認 PID 後停止。停止本機 AI 服務後，公開網站的一般功能可以繼續使用，但 AI 找課會暫時無法使用；臨時通道不是持續上線的託管服務。
