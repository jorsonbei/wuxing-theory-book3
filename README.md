# 宇宙是光之流體：物性論作為新的科學範式

這個倉庫公開《宇宙是光之流體：物性論作為新的科學範式》的繁體中文閱讀版。

網站入口：

https://jorsonbei.github.io/wuxing-theory-book3/

## 內容

- `index.html`：公開閱讀網站首頁
- `chapters/`：逐章 HTML 閱讀頁
- `resources/formula-canon.html`：104條公式正典網頁版
- `resources/reproduction.html`：公開復演入口
- `resources/FormulaOperatorCanon.json`：104條公式正典 JSON
- `book/README.md`：私有下載文件說明
- `assets/`：封面、樣式與搜尋索引
- `supabase/schema.sql`：登入、收藏、評論、下載記錄的資料表與 RLS
- `supabase/functions/download/`：登入後生成私有文件短期下載連結
- `docs/supabase-setup.md`：Supabase 後端啟用步驟

## 平台功能

- 公開閱讀：不需要登入
- 閱讀器設定：字體、背景、字號、行距、版心寬度
- 閱讀進度：本機保存
- 收藏：後端啟用後需要登入並保存到雲端
- 評論：可匿名提交，進入待審狀態，審核後公開
- 會員下載：後端啟用後需要登入，由私有 Storage 生成短期下載連結

> 注意：DOCX / Markdown 原稿不應提交到公開 GitHub Pages 倉庫，否則任何人都能繞過前端登入按鈕直接下載。下載文件應放入 Supabase private Storage。

## 後端啟用

見：

```text
docs/supabase-setup.md
```

## 復演材料

與書中相關的 V32 / V33 / V34 復演包、公式正典與在線復演室位於：

https://github.com/jorsonbei/wuxing-v32-v33-v34-reproduction

公式正典：

https://github.com/jorsonbei/wuxing-v32-v33-v34-reproduction/blob/main/release/FormulaOperatorCanon.json

在線復演室：

https://jorsonbei.github.io/wuxing-v32-v33-v34-reproduction/

## 版權

Copyright © 景龍鎖・貝記勝. All rights reserved.

本倉庫用於公開閱讀、引用與檢查，不代表放棄著作權。未經授權，不得將全文或改編版本用於商業出版、訓練資料集打包、付費分發或其他侵害作者權益的用途。
