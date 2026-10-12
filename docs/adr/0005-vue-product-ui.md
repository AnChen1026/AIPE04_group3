# 正式網頁使用 Vue

使用者看到的正式畫面用 Vue 製作，這一輪不改成 Next.js。現有 Jinja 測試頁保留，讓後端寫程式時可以測試。新的後端 API 也附一個簡單測試頁；正式使用者只走 Vue。後端維持現有 FastAPI，已完成的註冊、登入、角色與老師審核不重做。Vue 呼叫 JSON API，並沿用 Session Cookie，不改成 JWT。
