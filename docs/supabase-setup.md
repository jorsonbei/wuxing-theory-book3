# Supabase 後端啟用指南

本網站目前是 GitHub Pages 靜態站。公開閱讀不需要後端；但「註冊登入、雲端收藏、會員下載、評論審核」需要 Supabase。

## 1. 建立 Supabase 專案

在 Supabase 建立新專案後，記下：

- Project URL
- anon public key
- service role key

前端只放 `anon public key`。`service role key` 只能放在 Edge Function secrets，不能放進 GitHub Pages。

## 2. 執行資料庫 SQL

在 Supabase SQL Editor 執行：

```sql
-- repo file:
-- supabase/schema.sql
```

這會建立：

- `books`
- `user_favorites`
- `book_comments`
- `download_requests`
- 私有 Storage bucket：`private-downloads`
- RLS policies

權限設計：

- 閱讀網站：不登入
- 評論：匿名可提交，但只進入 `pending`
- 公開評論：只讀 `approved`
- 收藏：登入後只讀寫自己的收藏
- 下載：登入後由 Edge Function 生成短期連結

## 3. 上傳會員下載文件

把下載文件放入 Supabase Storage 的 `private-downloads` bucket：

```text
private-downloads/
  wuxing-theory-book3/
    wuxing-theory-book3.docx
    wuxing-theory-book3.md
```

目前本地最終稿可使用：

```text
/Users/beijisheng/Downloads/物性論3_投稿前總審版.docx
/Users/beijisheng/Downloads/物性論3_投稿前總審版.md
```

上傳後不要把 DOCX / MD 放回公開 GitHub Pages 目錄，否則仍可被直鏈下載。

## 4. 部署下載 Edge Function

安裝並登入 Supabase CLI 後：

```bash
supabase login
supabase link --project-ref <PROJECT_REF>
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=<SERVICE_ROLE_KEY>
supabase secrets set PRIVATE_DOWNLOAD_BUCKET=private-downloads
supabase functions deploy download
```

Supabase 通常會自帶 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY`。如果你的環境沒有，補設：

```bash
supabase secrets set SUPABASE_URL=<PROJECT_URL>
supabase secrets set SUPABASE_ANON_KEY=<ANON_PUBLIC_KEY>
```

## 5. 啟用前端配置

編輯：

```text
assets/platform-config.js
```

改成：

```js
window.WUXING_PLATFORM_CONFIG = {
  enabled: true,
  supabaseUrl: "https://YOUR_PROJECT.supabase.co",
  supabaseAnonKey: "YOUR_ANON_PUBLIC_KEY",
  downloadFunctionUrl: "https://YOUR_PROJECT.supabase.co/functions/v1/download",
  bookId: "wuxing-theory-book3"
};
```

然後重建並推送：

```bash
python3 tools/build_site.py
git add assets/platform-config.js index.html chapters resources assets tools
git commit -m "Enable Supabase backend"
git push origin main
```

## 6. 設定登入回跳網址

在 Supabase Auth URL Configuration 中加入：

```text
https://jorsonbei.github.io/wuxing-theory-book3/
https://jorsonbei.github.io/wuxing-theory-book3/**
```

本地測試可加入：

```text
http://127.0.0.1:8123/**
```

## 7. 評論審核

讀者提交後，評論狀態是 `pending`。審核通過時，在 Supabase Table Editor 或 SQL 裡改：

```sql
update public.book_comments
set status = 'approved',
    approved_at = now()
where id = '<COMMENT_ID>';
```

拒絕則改成：

```sql
update public.book_comments
set status = 'rejected'
where id = '<COMMENT_ID>';
```

## 8. 後續建議

匿名評論正式開放後，建議再加：

- Cloudflare Turnstile 防垃圾評論
- 管理員審核後台
- 下載頻率限制
- 多書籍 `books` 管理界面
- 郵件訂閱與新書通知
