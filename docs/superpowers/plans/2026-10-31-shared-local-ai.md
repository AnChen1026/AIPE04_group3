# Shared Local AI Implementation Plan

**Goal:** 以本機 Qwen、BGE-M3 為共享測試站提供有根據的多輪找課。
**Architecture:** Vue → FastAPI → 安全通道 → localhost 受限模型閘道 → Ollama；正式課程以 PostgreSQL 為準。Refine 和直接生成使用相同候選進行比較。
**Tech Stack:** FastAPI、Vue、PostgreSQL、Ollama、Qwen3 4B、BGE-M3、Pydantic、pytest。
**Spec:** docs/superpowers/specs/2026-10-31-shared-local-ai-design.md

## Constraints
- 本機模型，最高兩次系統追問，公開已發布鋼琴課，保持既有 session ownership；不可根據練習分數推測程度。
- 不向網際網路暴露未驗證的 Ollama；限速、序列化、超時、拒絕未授權。
- 雲端 migration 前確認可還原備份；保護現有使用者資料和私有設定。

## Review focus
- 否定／撤銷／更正不能默默放寬硬條件；未知不視為符合。
- 模型輸出不得選擇未發布課、越權來源或編造價格與證據。
- 未持密鑰請求不得呼叫模型；不要記錄 prompt 或憑證。
- 索引與課程更新、取消發布保持一致；模型失敗後一般搜尋可用。
- Refine、直接整理以同一候選比較；可靠性、延遲與容量實測。

## Tasks
- [x] 盤點與固定基準，保留並驗證可用還原點（備份／還原曾有一次暫時失敗，根因尚未確認）。
- [x] 整合結構化需求理解、增量狀態、動態追問與後續修正；測試 owner 與硬限制。
- [ ] 移植 BGE 語意搜尋並核對來源與索引生命週期；僅查已發布正式課程（已實作及索引，更新後目前需人工重建）。
- [ ] 以相同候選比較 Refine／直接整理及真人可審核的測試報告。
- [ ] 實作並驗證安全本機模型閘道、限流與受保護的遠端連線（臨時通道曾完成測試，尚未接上 Render）。
- [x] 更新 Vue、執行整合及真實模型測試，撰寫運行手冊。
- [ ] 驗證備份、共享環境、部署與真實組員流程；未獲得必要基礎設施時明確報告。
