# 共用本機 AI 找課：測試環境操作

本功能供小規模測試：瀏覽器 → Render 後端 → 臨時 HTTPS 通道 → Mac 上的受限閘道 → Ollama。模型不在組員的電腦執行。Mac 必須開機、保持網路及服務運作；休眠或網路中斷會使 AI 找課失敗。未設定模型時保留原本的找課方式；已設定但模型無法連線時，介面顯示錯誤並保留輸入，其他一般課程頁面仍可使用。

## 啟動本機模型與閘道

以下在取得此功能分支、安裝後端依賴及 Ollama 後操作。首次執行需下載模型，磁碟與記憶體空間依 Ollama 模型版本而定。

```sh
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama pull bge-m3:567m
mkdir -p .scratch/shared-ai
chmod 700 .scratch/shared-ai
python -c 'import os,secrets; p=".scratch/shared-ai/gateway-token"; f=os.open(p, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600); os.write(f,secrets.token_urlsafe(48).encode()); os.close(f)'
```

最後一行只在首次建立金鑰時執行；檔案已存在會安全地報錯，不會覆蓋舊金鑰。妥善保管此檔案，不要放進 Git 或提供給組員。請確認 Ollama 正在執行，接著在專案根目錄開啟一個終端機：

```sh
export AI_GATEWAY_TOKEN="$(cat .scratch/shared-ai/gateway-token)"
python -m uvicorn scripts.local_ai_gateway:app --host 127.0.0.1 --port 18763 --no-access-log
```

閘道只接受指定模型與有限大小的請求，且同時只處理一個；忙碌時會拒絕其他請求。不要直接把 Ollama 的 11434 埠公開。保持終端機開啟，Ctrl-C 可停止閘道。

## 啟動免費臨時通道

另開終端機，使用已安裝的 Cloudflare `cloudflared`：

```sh
cloudflared tunnel --url http://127.0.0.1:18763
```

終端機顯示的 HTTPS 網址是臨時網址，重啟後可能改變，且沒有可用性保證。通道網址不能取代金鑰；閘道的 Bearer 驗證仍必須啟用。只將網址與金鑰交給管理 Render 服務設定的人，不要放在前端、文件、Git 或聊天群組。這是臨時測試方案，不是持續上線的正式服務。

在 Render 後端服務的環境變數中設定：

- `AI_COURSE_GATEWAY_URL`：剛取得的臨時 HTTPS 網址，沒有結尾 `/`。
- `AI_COURSE_GATEWAY_TOKEN`：本機 `.scratch/shared-ai/gateway-token` 的完整內容。
- `AI_COURSE_EMBEDDING_VERSION`：本機 Ollama 的 `bge-m3:567m` 模型完整 digest（64 個十六進位字元）；本機可用 `curl -s http://127.0.0.1:11434/api/tags` 取得對應 `digest`。

這些是後端設定，不是 `VITE_` 前端變數；網址改變後必須更新 Render 並重新部署服務。不要在未先部署本分支程式與完成遷移前啟用。若金鑰疑似外洩，停止通道與閘道、刪除舊金鑰後重新建立，並同步更新 Render。

## 資料庫與索引

先完成可還原備份，更新備份排程執行環境使其支援新 migration，再執行 `020_course_embeddings` 遷移；應由管理員確認目標測試資料庫及部署順序。索引只處理已發布課程的標題、曲風及介紹；原始課程資料仍以 `courses` 表為準。編輯課程後舊向量會失效，但目前不會自動重建；需重新執行索引工具。無索引或模型不通時會顯示排序降級資訊。最多考慮最新的 1000 門符合條件課程，超過時會在結果中提示，未針對大量課程最佳化。

在有雲端設定檔的管理員 Mac，於專案根目錄執行；以下不輸出金鑰。先將模型 digest 填入本機 shell 的 `AI_COURSE_EMBEDDING_VERSION`，並確保其與 Render 相同：

```sh
export AI_COURSE_GATEWAY_URL=http://127.0.0.1:18763
export AI_COURSE_GATEWAY_TOKEN="$(cat .scratch/shared-ai/gateway-token)"
export AI_COURSE_EMBEDDING_VERSION="$(curl -s http://127.0.0.1:11434/api/tags | python -c 'import json,sys; print(next(m["digest"] for m in json.load(sys.stdin)["models"] if m["name"] == "bge-m3:567m"))')"
python -m scripts.cloud_command --config /path/to/.env.cloud.json index-courses
```

預設為 dry-run，只顯示課程與待索引數量。確認資料庫名稱與結果後，再執行下列命令並將 `DATABASE_NAME` 換成實際資料庫名稱：

```sh
python -m scripts.cloud_command --config /path/to/.env.cloud.json index-courses --apply --confirm-database DATABASE_NAME
```

請在課程異動後重跑，並於更換 BGE 模型 digest 時重建全部索引。工具分批寫入，中斷後可重跑，已完成的部分會保留。此命令是人工操作，尚未建立自動排程。

## 已知限制

- 使用者的文字會送至 Render，經加密通道傳到這台 Mac 的模型；不要輸入密碼或敏感個資。對話過期後不能讀取，實體刪除在後續新搜尋時觸發；備份可能保留較舊資料。
- 硬條件採保守驗證，複雜的否定或修正可能要求換句話說；語意搜尋不保證理解每種說法，請檢查課程原文及費用。
- Refine 與直接整理目前是離線比較工具，不是線上推薦回答。少量測試不足以證明它比直接整理更好；正式啟用前仍需擴大評估、量測延遲並檢查引用。
- 閘道及後端限流是單程序記憶體內計數，重新啟動後重設；未支援多副本的集中限流。暫不適合高流量或高可用正式部署。
