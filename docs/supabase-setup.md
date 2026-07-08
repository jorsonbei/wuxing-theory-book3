# Supabase 上線協作說明

這份文件不是讓作者自己研究技術部署，而是給項目留檔。實際開發、配置、部署、檢查由 Codex 負責；作者只處理必須本人完成的帳號與授權動作。

## 目前狀態

網站已經具備以下前端入口：

- 公開閱讀：所有章節不需要登入
- 登入 / 註冊入口
- 我的收藏
- 會員下載
- 讀者評論

真正的雲端功能需要接上 Supabase：

- 收藏寫入雲端帳號
- 評論寫入資料庫，先待審，審核後公開
- DOCX / Markdown 放入私有 Storage
- 登入後由 Edge Function 生成短期下載連結

## 作者只需要做的事

### 1. 登入或註冊 Supabase

打開：

```text
https://supabase.com/
```

用你的 Email / GitHub / Google 登入。需要驗證郵箱或手機時，由你本人完成。

### 2. 建立 Supabase access token

登入後打開：

```text
https://supabase.com/dashboard/account/tokens
```

建立一個 access token。這個 token 只用來讓本機 Supabase CLI 連上你的帳號。

你可以選擇兩種方式之一：

- 把 token 給 Codex，Codex 執行 `supabase login --token ...`
- 或你自己在終端執行 `supabase login`，完成瀏覽器登入

### 3. 確認是否允許建立 Supabase 專案

登入後，Codex 可以列出你的 organization，並幫你建立專案。若 Supabase 要求選擇免費 / 付費方案、綁卡、付款，這一步需要你本人確認。

建議專案設定：

```text
Project name: wuxing-theory-book3
Region: ap-southeast-1
Size: nano
```

## Codex 負責做的事

作者完成登入後，Codex 會接手：

1. 建立或連接 Supabase project
2. 取得 Project URL、anon key、service role key
3. 執行資料庫 migration
4. 建立資料表、RLS 權限與私有 Storage bucket
5. 部署 `download` Edge Function
6. 上傳私有下載文件
7. 更新網站 `assets/platform-config.js`
8. 重建網站
9. 提交並推送 GitHub Pages
10. 線上測試登入、收藏、評論與會員下載

## 本地自動部署腳本

Codex 準備好的腳本是：

```text
tools/launch_supabase_backend.sh
```

它會一次完成：

- link Supabase project
- push database migrations
- set Edge Function secrets
- deploy download function
- upload private DOCX / Markdown
- enable frontend config
- rebuild site
- run basic checks
- commit and push

敏感資料不會提交到 GitHub。實際部署時會使用本機文件：

```text
.env.deploy.local
```

這個文件已被 `.gitignore` 忽略。

## 私有下載文件

目前本機書稿文件位置：

```text
/Users/beijisheng/Downloads/物性論3_投稿前總審版.docx
/Users/beijisheng/Downloads/物性論3_投稿前總審版.md
```

上線後，它們會被上傳到 Supabase private Storage：

```text
private-downloads/
  wuxing-theory-book3/
    wuxing-theory-book3.docx
    wuxing-theory-book3.md
```

GitHub Pages 公開倉庫不再保存這兩個文件，否則讀者可以繞過登入直接下載。

## 評論審核

讀者送出評論後，資料庫狀態是：

```text
pending
```

審核通過後改成：

```text
approved
```

之後可以再做一個管理後台，讓作者不用進 Supabase 後台也能審核評論。
