# GitHub 團隊協作超簡版

## 1. 每個人的分支

| 負責人 | 分支 |
|---|---|
| 永富 | `feature/login` |
| 姿彣 | `feature/course-management` |
| Ken | `feature/student-management` |
| Ollie | `feature/messaging` |
| 宇鈞 | `feature/admin` |
| 禹銨、雄哥 | `feature/database` |

---

## 2. 第一次加入專案

### Step 1：Clone 專案

```bash
git clone <GitHub 專案網址>
```

### Step 2：進入專案資料夾

```bash
cd AIPE04_group3
```

### Step 3：切到自己功能的分支



```bash
git switch feature/功能名稱
```


切完就可以開始寫自己的功能。

---

## 3. 每天開始開發

先確認自己在哪個分支：

```bash
git branch
```

看到自己的分支前面有 `*` 就可以開始。

例如：

```text
* feature/login
  main
```

不要在 `main` 裡面直接寫程式。

---

## 4. 寫完功能後

### Step 1：加入修改

```bash
git add .
```

### Step 2：Commit

```bash
git commit -m "這次開發做了什麼"
```

### Step 3：Push

```bash
git push
```

---

## 5. 完成後告訴組長

Push 完後，在群組告訴組長：

```text
我的功能已完成並 push 到 feature/功能名稱
```

由組長負責檢查並合併到 `main`。

---

## 6. 最簡單流程

```text
第一次：
git clone
↓
git switch 自己的分支
↓
開始寫程式


寫完：
git add .
↓
git commit -m "修改內容"
↓
git push
↓
告訴組長
```

---

## 7. 注意

1. 不要直接修改 `main`
2. 一定要確認自己在自己的 `feature/...` 分支
3. 不要上傳 `.env`
4. 不要把 API Key、Password、Token 放進 GitHub
5. 有問題先問，不要亂刪別人的程式
6. 千萬不要動到別人的程式碼！！！
7. 千萬不要動到別人的程式碼！！！
8. 千萬不要動到別人的程式碼！！！
