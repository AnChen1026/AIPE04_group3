# 鋼琴課程目錄重編：研究依據與驗收

查找與編輯日期：2026-11-02。

## 研究方式與資料性質

搜尋台灣鋼琴教室、到府家教、樂齡與親子課程，以及音樂院校、考試機構的公開課程。參考的是教學領域、學習情境、先備能力與練習方向；課名、課綱、教師姓名與專長組合由本專案重新撰寫，沒有搬入真實老師名單、學歷、認證、得獎紀錄、聯絡資料或機構的招生承諾。

此目錄仍是 local/staging 使用的虛構產品資料，不是下列機構實際開設或背書的 426 門課。公開課程文字不放入研究或維運資訊；內部保留 `is_demo`、原始識別碼與舊版內容指紋，以便安全重做匯入。課程搜尋與首頁推薦使用正式 `courses` 資料；不把這份研究筆記當成已核准的 RAG 知識文件。

## 查閱的公開來源

| 第一手來源 | 本次參考的方向 |
| --- | --- |
| [Yamaha 鋼琴個別課](https://www.yamahamusic.tw/yms/music-lesson/pianoforte) | 聽、唱、彈、讀、樂理及聯彈並行，個別課不只彈奏指定曲。 |
| [Yamaha 流行鍵盤](https://www.yamahamusic.tw/yms/music-lesson/piano) | 節奏、和弦與編曲的鍵盤學習路線。 |
| [Yamaha 兒童音樂教育](https://www.yamahamusic.tw/yms/jmc) | 依年齡與學習起點安排活動，而不是以同一教法處理所有兒童。 |
| [拯救音樂鋼琴課程](https://savingmusic.com.tw/index.php?information_id=77&route=information/information) | 啟蒙、兒童、青少年、成人與教材選擇的差別。 |
| [小作曲家成人鋼琴課](https://www.composer.com.tw/adult-piano.html) | 成人目標曲、到府／線上、分散練習與復學需求。未採用其速成時程或價格承諾。 |
| [鴻韻音樂教育](https://www.hymusic.com.tw/hymusicclassroom/) | 個別課與團體課、聽唱讀及節奏活動等市場常見情境。此次仍以一對一為主。 |
| [楷思室內樂培訓](https://ksmusic.com.tw/training/) | 親子四手、器樂重奏與成人合作演奏的課程方向。 |
| [Sandy 樂齡到府鋼琴](https://www.sandymusicedu.com/news/details.php?id=44196) | 搜尋摘要提供樂齡／到府學琴情境；全文抓取失敗，未引述個案內容。 |
| [ABRSM Piano](https://www.abrsm.org/en-gb/piano) | 演奏曲目、音階、視奏、聽力及演奏文憑是不同準備面向。本文不固定當期考試規則。 |
| [Trinity Piano](https://www.trinitycollege.com/qualifications/music/grade-exams/piano) | 鋼琴考級與個人化演奏選擇；備考時需依選定考試核對當期項目。 |
| [RCM Syllabi](https://www.rcmusic.com/learning/examinations/academic-resources-and-policies/syllabi-and-syllabi-errata) | 分級演奏、曲目與教學法可有不同進階路線。 |
| [RCM 鋼琴教學法附錄](https://teacherportal.rcmusic.com/getattachment/70639f15-3777-492e-9366-1a15d4bc322d/rcm_pianopedagogy_2023_online_f.pdf) | 進階教學與跨時期曲目應有實質內容，不能只更換程度標籤。 |
| [Berklee Piano Courses](https://college.berklee.edu/piano/piano-courses) | 爵士三重奏、合奏互動、和聲與進階節奏可各成不同教學主題。 |
| [Berklee Pop/Rock Keyboard](https://online.berklee.edu/courses/pop-rock-keyboard) | 樂團鍵盤需要處理和弦配置、律動與聲部角色，與獨奏旋律譜不同。 |
| [Berklee Jazz Improvisational Techniques](https://college.berklee.edu/courses/psij-211) | 爵士即興可透過採譜、聽辨與練習策略建立語彙。 |
| [Berklee Gary Burton: Jazz Improvisation](https://online.berklee.edu/courses/gary-burton-jazz-improvisation) | 即興發展與曲式、和聲、合奏脈絡的關係。 |
| [Berklee Gospel Keyboard](https://online.berklee.edu/courses/gospel-music-for-keyboard) | 司琴的現場回應與進階福音鍵盤可分開設計先備要求。 |
| [UCLA Collaborative Piano audition requirements](https://schoolofmusic.ucla.edu/app/uploads/2024/07/2025-Audition-Reqs_Collaborative_Piano.pdf) | 進階合作鋼琴包含器樂、聲樂與協奏曲等不同準備方向。 |

以上來源只支撐主題規劃；各門課的任務、練習量與成果檢核是本專案的編輯設計，不宣稱等同官方課綱。Trinity 等考試名稱僅用於備考情境，不宣稱取得其認證，也不自訂考試資格與曲目規則；實際報考需查當期官方資料。

## 編輯規則

- 保留原來 426 個課程 ID、226 個老師 ID 及原有關聯；不刪掉課程重建。
- 80 個核心主題，每主題最多出現 6 門；每門都有獨立課名與具體任務。
- 同一老師的至多兩門課屬於同一核心主題，專長、教法及介紹同步更新。
- 先備能力與找課程度相符。進階不使用「零基礎」招生說明。
- 每門詳細介紹列出先備能力、課堂重點、練習安排、成果檢核與授課安排。
- 到府、工作室與線上情境使用現有地區／方式欄位；線上合作題材不承諾低延遲同步合奏。
- 公開介紹不杜撰師資學歷、保證考試結果、保證短期速成或既有未提供的錄影／陪練功能。
- 課程費用、時段、圖片、參考 MIDI、綁定與狀態保留既有值。這次更新課名、程度、風格及介紹，並補相符教師資料。

## 分布與品質驗收

| 程度 | 舊版 | 新版 |
| --- | ---: | ---: |
| 入門 | 291 | 107 |
| 初階 | 68 | 107 |
| 中階 | 67 | 106 |
| 進階 | 0 | 106 |
| 合計 | 426 | 426 |

舊版僅 26 個基礎主題，164 個不同課名；新版有 80 個核心主題、426 個唯一課名與 226 個唯一教師顯示名稱。主題庫共撰寫 480 個子課綱，依既有教師的單課／雙課配置選用其中 426 個，其餘為尚未發布的編輯候選，不增加課程筆數。

自動驗收包含：四級分布、主題集中度、教師與課綱一致、必備欄位、完整內容可納入 1000 字的語意索引、跨程度搜尋情境，以及全文三字片語集合 Jaccard 重疊率須小於 0.8。此數字是字面重疊檢查，不是學習成效、語意多樣性或推薦品質的保證；同一領域仍會自然共享和弦、視譜、踏板等詞。

## 本次執行結果

- staging 核對：426 門課與 226 位教師的新版欄位全部一致，教師／課程 ID 與關聯保留。
- 授課情境：48 門到府家教、96 門工作室實體、147 門線上、135 門線上／實體可選；不變更既有費用與地區欄位。
- 索引：426 筆皆符合最新 `course_hash` 與本機 BGE-M3 模型版本。
- 自動測試：8 項匯入／更新保護測試（隔離 SQLite）與 7 項內容品質測試通過；另於 staging PostgreSQL 逐筆核對正式資料。
- 自然語句：16 個指定程度的語句，在同程度已發布課程的 BGE-M3 cosine 排序中，前三名全部包含預期核心主題。初次為 15/16；釐清聽奏課的敘述後為 16/16。
- [完整語句與前三名結果](piano-catalog-retrieval-check.json) 保留實際課名、主題與分數。這是已知課程主題的編輯回歸驗收，並非盲測，也不是完整搜尋 API、條件解析或多輪對話的端對端驗收。

## 代表性差異

- 入門：黑鍵五聲音樂、樂齡大字譜、親子陪練、成人復學與電子琴轉鋼琴，起點與任務不同。
- 初階：自彈自唱換和弦、台語三拍伴奏、爵士藍調、教會司琴與吉他手轉鍵盤，各自有不同手部與節拍分工。
- 中階：巴洛克複音、古典曲式、R&B 後靠拍、Bossa Nova、藝術歌曲伴奏與配樂縮編，不以兩個課名套滿所有資料。
- 進階：賦格聲部、貝多芬全曲、蕭邦敘事、法國音色、協奏曲、專業合作、爵士三重奏、婚宴現場移調與教學法，要求既有能力並列出實作。

## 重做與更新

```sh
python -m scripts.build_demo_catalog
python -m pytest tests/catalog --confcutdir=tests/catalog -q
python -m scripts.cloud_command seed --refresh-existing
python -m scripts.cloud_command seed --refresh-existing --apply --confirm-database postgres
```

前兩行只處理本機內容。後兩行使用已設定的 staging 環境；預設 dry-run。只有老師身分與課程／教師介紹符合已知舊版或新版指紋時才更新，所有碰撞檢查在寫入前完成。遇到人工修改應先盤點差異，不放寬為只憑假資料字首即可覆寫。完成更新後另依 [共用本機 AI 手冊](shared-local-ai.md) 重建索引，舊 content hash 不視為有效索引。
