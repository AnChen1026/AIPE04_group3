# 移除 Jinja 測試頁，後端只提供 API

Vue 已涵蓋登入註冊、老師後台、學生專區與管理員後台，Jinja 測試頁和它們專用的 HTML／表單路由一併刪除，後端只留 JSON API 與 WebSocket。新的 API 不再附測試頁，改用 FastAPI 自動產生的 `/docs` 試打，並在 `tests/` 寫自動測試。Google 驗證回來後由後端導回 Vue 的頁面，用 Google 註冊的老師在 Vue 老師後台補填申請資料。這份決定取代 0005 裡「保留 Jinja 測試頁、新 API 附測試頁」的部分，0005 其餘內容不變。
