#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("WUXING_SOURCE_MD", ROOT / "book" / "wuxing-theory-book3.md"))
CHAPTERS = ROOT / "chapters"
ASSETS = ROOT / "assets"
RESOURCES = ROOT / "resources"
SITE_URL = "https://jorsonbei.github.io/wuxing-theory-book3/"
FORMULA_CANON = RESOURCES / "FormulaOperatorCanon.json"
ASSET_VERSION = "20260708-platform-backend-v1"


CN_NUM = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def cn_to_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    if value == "十":
        return 10
    if "十" in value:
        left, right = value.split("十", 1)
        tens = CN_NUM.get(left, 1) if left else 1
        ones = CN_NUM.get(right, 0) if right else 0
        return tens * 10 + ones
    return CN_NUM.get(value)


def plain_text(markdown: str) -> str:
    text = re.sub(r"```.*?```", " ", markdown, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[$*_>#~\\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def pandoc_fragment(markdown: str) -> str:
    result = subprocess.run(
        [
            "pandoc",
            "--from",
            "markdown+tex_math_dollars+raw_tex",
            "--to",
            "html5",
            "--mathjax",
        ],
        input=markdown,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return mark_formula_paragraphs(result.stdout)


def mark_formula_paragraphs(html_text: str) -> str:
    def repl(match: re.Match) -> str:
        inner = match.group(1)
        stripped = re.sub(r"<[^>]+>", "", inner)
        stripped = html.unescape(stripped).strip()
        has_chinese = re.search(r"[\u4e00-\u9fff]", stripped) is not None
        looks_like_formula = (
            "=" in stripped
            and not has_chinese
            and len(stripped) <= 260
            and re.search(r"[A-Za-zα-ωΑ-ΩΣΔΩΠησχ²ℏ_{}()[\]^+\-*/|≤≥]", stripped)
        )
        if looks_like_formula:
            return f'<p class="formula-line">{inner}</p>'
        return match.group(0)

    return re.sub(r"<p>(.*?)</p>", repl, html_text, flags=re.S)


def split_sections(markdown: str) -> tuple[str, list[dict]]:
    matches = list(re.finditer(r"^# (.+)$", markdown, flags=re.M))
    if not matches:
        raise RuntimeError("No H1 headings found")

    book_title = matches[0].group(1).strip()
    sections: list[dict] = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        block = markdown[start:end].strip()
        if title in {book_title, "目錄"}:
            continue
        if title.startswith("附錄與後記"):
            h2_matches = list(re.finditer(r"^## (.+)$", block, flags=re.M))
            if h2_matches:
                prefix = block[: h2_matches[0].start()].strip()
                if prefix:
                    sections.append({"title": title, "markdown": prefix})
                for j, h2 in enumerate(h2_matches):
                    h2_title = h2.group(1).strip()
                    h2_start = h2.start()
                    h2_end = h2_matches[j + 1].start() if j + 1 < len(h2_matches) else len(block)
                    h2_block = block[h2_start:h2_end].strip()
                    h2_block = re.sub(r"^## ", "# ", h2_block, count=1, flags=re.M)
                    sections.append({"title": h2_title, "markdown": h2_block})
                continue
        sections.append({"title": title, "markdown": block})
    return book_title, sections


def filename_for(title: str, index: int) -> str:
    if title.startswith("序章"):
        return "preface.html"
    if title.startswith("附錄與後記"):
        return "appendix-index.html"
    if title.startswith("後記"):
        return "afterword.html"
    chapter = re.search(r"第(.+?)章", title)
    if chapter:
        n = cn_to_int(chapter.group(1)) or index
        return f"chapter-{n:02d}.html"
    part = re.search(r"第(.+?)部", title)
    if part:
        n = cn_to_int(part.group(1)) or index
        return f"part-{n:02d}.html"
    appendix = re.search(r"附錄([一二三四五六七八九十]+)", title)
    if appendix:
        n = cn_to_int(appendix.group(1)) or index
        return f"appendix-{n:02d}.html"
    return f"section-{index:02d}.html"


def category(title: str) -> str:
    if title.startswith("第") and "部" in title and "章" not in title:
        return "part"
    if title.startswith("附錄"):
        return "appendix"
    if title.startswith("後記"):
        return "afterword"
    if title.startswith("序章"):
        return "preface"
    return "chapter"


def nav_html(sections: list[dict], current: str | None = None, base: str = "") -> str:
    items = []
    for s in sections:
        cls = [category(s["title"])]
        if s["filename"] == current:
            cls.append("active")
        label = html.escape(s["title"])
        href = html.escape(base + "chapters/" + s["filename"])
        items.append(f'<a class="nav-item {" ".join(cls)}" href="{href}">{label}</a>')
    return "\n".join(items)


def page_shell(
    *,
    title: str,
    body: str,
    base: str = "",
    description: str = "《宇宙是光之流體：物性論作為新的科學範式》公開閱讀網站。",
) -> str:
    safe_title = html.escape(title)
    safe_desc = html.escape(description)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <meta name="description" content="{safe_desc}">
  <meta property="og:title" content="{safe_title}">
  <meta property="og:description" content="{safe_desc}">
  <meta property="og:type" content="book">
  <meta property="og:image" content="{base}assets/cover.jpg">
  <link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{base}assets/styles.css?v={ASSET_VERSION}">
  <script>
    window.MathJax = {{
      tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']] }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src="{base}assets/platform-config.js?v={ASSET_VERSION}"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <script defer src="{base}assets/site.js?v={ASSET_VERSION}"></script>
</head>
<body data-base="{base}">
{body}
<div class="auth-modal" id="auth-modal" hidden>
  <div class="auth-modal-panel" role="dialog" aria-modal="true" aria-labelledby="auth-title">
    <button class="auth-close" type="button" aria-label="關閉登入視窗">×</button>
    <p class="edition">會員系統</p>
    <h2 id="auth-title">登入或註冊</h2>
    <p>輸入 Email 後，系統會寄出登入連結。登入後可以雲端收藏與下載會員文件。</p>
    <form class="auth-form">
      <label><span>Email</span><input id="auth-email-input" name="email" type="email" autocomplete="email" required placeholder="you@example.com"></label>
      <button class="button primary" type="submit">寄出登入連結</button>
    </form>
    <p class="auth-status" aria-live="polite"></p>
  </div>
</div>
<div class="auth-modal" id="favorites-modal" hidden>
  <div class="auth-modal-panel favorites-panel" role="dialog" aria-modal="true" aria-labelledby="favorites-title">
    <button class="auth-close favorites-close" type="button" aria-label="關閉收藏視窗">×</button>
    <p class="edition">雲端收藏</p>
    <h2 id="favorites-title">我的收藏</h2>
    <p>登入後，收藏會保存到雲端帳號；後端尚未啟用時，這裡會顯示本機暫存收藏。</p>
    <p class="favorite-status" aria-live="polite"></p>
    <div class="favorite-list" data-favorite-list></div>
  </div>
</div>
</body>
</html>
"""


def header(base: str = "") -> str:
    return f"""<header class="site-header">
  <a class="brand" href="{base}index.html">物性論閱讀平台</a>
  <nav class="top-links">
    <a href="{base}index.html#library">書庫</a>
    <a href="{base}index.html#catalog">目錄</a>
    <a href="{base}resources/formula-canon.html">公式正典</a>
    <a href="{base}resources/reproduction.html">復演入口</a>
    <a href="{base}index.html#downloads">會員下載</a>
    <a href="https://github.com/jorsonbei/wuxing-theory-book3">GitHub</a>
    <button class="top-link-button favorite-list-open" type="button">我的收藏</button>
    <button class="top-link-button auth-open" type="button">登入</button>
    <button class="top-link-button auth-signout" type="button" hidden>登出</button>
  </nav>
</header>"""


def build_index(book_title: str, sections: list[dict]) -> str:
    catalog = nav_html(sections, base="")
    cards = "\n".join(
        f"""<a class="chapter-card {category(s['title'])}" href="chapters/{html.escape(s['filename'])}">
  <span>{html.escape(s['type_label'])}</span>
  <strong>{html.escape(s['title'])}</strong>
</a>"""
        for s in sections
    )
    body = f"""{header("")}
<main>
  <section class="hero">
    <div class="hero-copy">
      <p class="edition">物性論系列 · 公開閱讀平台</p>
      <h1>把龐大的物性論，拆成可以反覆閱讀的系列宇宙</h1>
      <p class="lead">這裡不只是一本書的展示頁，而是物性論長期公開閱讀、版本收藏、公式索引與復演入口。讀者可以先自由閱讀，再沿著入門、物理、AI、復演與公式正典的路線，一步一步走進整個體系。</p>
      <div class="hero-actions">
        <a class="button primary" href="chapters/preface.html">閱讀當前主書</a>
        <a class="button" href="#library">進入書庫</a>
        <a class="button" href="#reading-routes">選擇閱讀路線</a>
      </div>
      <div class="stats">
        <span><strong>1</strong> 本公開主書</span>
        <span><strong>7</strong> 部</span>
        <span><strong>26</strong> 章</span>
        <a href="resources/formula-canon.html"><strong>104</strong> 條公式正典</a>
        <a href="resources/reproduction.html"><strong>公開</strong> 復演入口</a>
      </div>
    </div>
    <figure class="cover-frame">
      <img src="assets/cover.jpg" alt="《宇宙是光之流體》封面">
    </figure>
  </section>

  <section id="library" class="library-section">
    <div class="section-heading">
      <p class="edition">系列書庫</p>
      <h2>物性論不應被壓縮成一本書</h2>
      <p>後續每一個版本、每一個分冊、每一條閱讀路線，都可以放在這裡。當前先公開主書，後續可加入入門版、AI 版、復演版、公式版與英文版。</p>
    </div>
    <div class="book-grid">
      <article class="book-card featured-book">
        <div class="book-cover-mini"><img src="assets/cover.jpg" alt="《宇宙是光之流體》封面"></div>
        <div class="book-card-copy">
          <p class="book-kicker">當前主書 · 投稿前總審版</p>
          <h3>{html.escape(book_title)}</h3>
          <p>從宇宙底層、經典公式、HFCD 復演、外部審判到物性 AI，建立一套可閱讀、可檢查、可被後來者接手的物性論主框架。</p>
          <div class="book-meta">
            <span>繁體中文</span>
            <span>26 章</span>
            <span>含公式正典與復演入口</span>
          </div>
          <div class="book-actions">
            <a class="button primary" href="chapters/preface.html">開始閱讀</a>
            <button class="button local-favorite" type="button" data-favorite-id="wuxing-theory-book3" data-favorite-type="book" data-favorite-url="chapters/preface.html" data-favorite-title="{html.escape(book_title)}">收藏到帳號</button>
            <button class="button gated-action" type="button" data-action-name="DOCX 下載" data-download-book-id="wuxing-theory-book3" data-download-format="docx">登入後下載</button>
          </div>
          <p class="small-note">閱讀無需登入；雲端收藏與下載需要登入。若後端尚未配置，系統會保留入口並提示管理員啟用。</p>
        </div>
      </article>
      <article class="book-card ghost-book">
        <p class="book-kicker">預留系列</p>
        <h3>物性論入門版</h3>
        <p>給第一次接觸物性論的讀者，降低公式密度，先建立世界觀、例子與核心語感。</p>
      </article>
      <article class="book-card ghost-book">
        <p class="book-kicker">預留系列</p>
        <h3>物性 AI 專卷</h3>
        <p>集中展開狀態生成、世界模型、產業成本、幻覺治理與下一代 AI 架構。</p>
      </article>
      <article class="book-card ghost-book">
        <p class="book-kicker">預留系列</p>
        <h3>公式與復演專卷</h3>
        <p>把 104 條公式、復演包、外部裁判與反駁入口整理成可查、可跑、可審的技術讀本。</p>
      </article>
    </div>
  </section>

  <section id="reading-routes" class="route-section">
    <div class="section-heading">
      <p class="edition">閱讀路線</p>
      <h2>不同讀者，不必從同一扇門進來</h2>
      <p>物性論體系太大，讀者需要路線，而不是被一整座山壓住。</p>
    </div>
    <div class="route-grid">
      <a class="route-card" href="chapters/preface.html"><strong>普通讀者</strong><span>先讀序章與第一部，用空間、光、物質、時間四個直覺入口建立底層圖像。</span></a>
      <a class="route-card" href="chapters/chapter-09.html"><strong>科學讀者</strong><span>從第三部開始，看舊公式如何被歸根，再進入常數、物質生成與外部審判。</span></a>
      <a class="route-card" href="chapters/chapter-22.html"><strong>AI 從業者</strong><span>直接進入第六部，看語言生成器為什麼接不住世界，以及物性 AI 怎樣轉向狀態生成。</span></a>
      <a class="route-card" href="resources/formula-canon.html"><strong>復演與公式讀者</strong><span>從 104 條公式正典與復演入口進入，把語氣交給材料、代碼、邊界與失敗定位。</span></a>
    </div>
  </section>

  <section class="reader-feature-section">
    <div class="section-heading">
      <p class="edition">閱讀工具</p>
      <h2>先把閱讀體驗做紮實</h2>
      <p>本版已加入本機閱讀器能力；下一步接入後端後，收藏、下載與評論就能從本機體驗升級為雲端帳號體驗。</p>
    </div>
    <div class="feature-grid">
      <div><strong>閱讀不登入</strong><span>所有章節仍可直接打開，適合傳播與引用。</span></div>
      <div><strong>閱讀器設定</strong><span>章節頁可切換字體、背景、字號、行距與版心寬度。</span></div>
      <div><strong>本機進度</strong><span>瀏覽器會記錄上次閱讀位置，首頁和章節頁都能返回。</span></div>
      <div><strong>雲端收藏</strong><span>登入後收藏寫入資料庫，不再只停留在本機瀏覽器。</span></div>
      <div><strong>公開評論</strong><span>讀者可免登入送出評論，先進入待審狀態，審核後公開顯示。</span></div>
      <div><strong>會員下載</strong><span>下載文件放入私有儲存，登入後由後端生成短期下載連結。</span></div>
    </div>
  </section>

  <section class="search-panel" aria-labelledby="search-title">
    <h2 id="search-title">站內搜尋</h2>
    <p>輸入「W 玻色子」「物性 AI」「關係腔」「復演」等關鍵詞，可以快速定位章節。</p>
    <label class="search-box">
      <span>搜尋</span>
      <input id="site-search" type="search" placeholder="輸入關鍵詞">
    </label>
    <div id="search-results" class="search-results" aria-live="polite"></div>
  </section>

  <section id="catalog" class="catalog">
    <div class="section-heading">
      <h2>完整目錄</h2>
      <p>每一章都已拆成獨立網頁，適合手機與桌面閱讀。</p>
    </div>
    <div class="catalog-grid">{cards}</div>
  </section>

  <section id="downloads" class="open-materials">
    <h2>資料中心</h2>
    <div class="material-grid">
      <button class="material-card gated-action" type="button" data-action-name="Markdown 下載" data-download-book-id="wuxing-theory-book3" data-download-format="markdown"><strong>Markdown 原稿</strong><span>登入後由私有儲存生成短期下載連結，適合校對、版本管理和引用。</span></button>
      <button class="material-card gated-action" type="button" data-action-name="DOCX 下載" data-download-book-id="wuxing-theory-book3" data-download-format="docx"><strong>KDP DOCX 書稿</strong><span>登入後由私有儲存生成短期下載連結，保留出版排版版本。</span></button>
      <a href="resources/formula-canon.html"><strong>104條公式正典</strong><span>逐條展示公式、算子角色、聲明類型與防污染守衛。</span></a>
      <a href="resources/reproduction.html"><strong>公開復演入口</strong><span>復演倉庫、發佈頁、在線復演室與原始資料入口。</span></a>
      <a href="https://github.com/jorsonbei/wuxing-v32-v33-v34-reproduction"><strong>V32 / V33 / V34 復演倉庫</strong><span>公式正典、復演包與在線復演室入口。</span></a>
    </div>
  </section>
</main>
<footer class="site-footer">
  <p>Copyright © 景龍鎖・貝記勝. All rights reserved. 本倉庫公開閱讀，不代表放棄著作權。</p>
</footer>"""
    return page_shell(title=book_title, body=body, base="")


def build_chapter_pages(book_title: str, sections: list[dict]) -> None:
    for i, s in enumerate(sections):
        prev_s = sections[i - 1] if i > 0 else None
        next_s = sections[i + 1] if i + 1 < len(sections) else None
        article = pandoc_fragment(s["markdown"])
        aside = nav_html(sections, current=s["filename"], base="../")
        prev_link = (
            f'<a class="button" href="{html.escape(prev_s["filename"])}">上一章</a>'
            if prev_s
            else ""
        )
        next_link = (
            f'<a class="button primary" href="{html.escape(next_s["filename"])}">下一章</a>'
            if next_s
            else ""
        )
        body = f"""{header("../")}
<div class="reader-shell">
  <main class="reader-main">
    <section class="reader-toolbar" aria-label="閱讀設定">
      <div class="reader-toolbar-head">
        <div>
          <p class="edition">閱讀器</p>
          <h2>{html.escape(s["title"])}</h2>
        </div>
        <div class="reader-toolbar-actions">
          <button class="button local-favorite" type="button" data-favorite-id="{html.escape(s["filename"])}" data-favorite-type="chapter" data-favorite-url="chapters/{html.escape(s["filename"])}" data-favorite-title="{html.escape(s["title"])}">收藏本章</button>
          <button class="button restore-reading" type="button">回到上次</button>
        </div>
      </div>
      <div class="reader-progress-track" aria-hidden="true"><span id="reader-progress"></span></div>
      <div class="reader-controls">
        <label><span>字體</span><select id="reader-font"><option value="serif">宋體</option><option value="sans">黑體</option><option value="kai">楷體</option></select></label>
        <label><span>背景</span><select id="reader-theme"><option value="paper">紙張</option><option value="warm">米黃</option><option value="green">護眼</option><option value="dark">夜間</option><option value="oled">OLED</option></select></label>
        <label><span>字號</span><input id="reader-size" type="range" min="17" max="24" step="1"></label>
        <label><span>行距</span><input id="reader-line" type="range" min="1.7" max="2.2" step="0.05"></label>
        <label><span>版心</span><input id="reader-width" type="range" min="680" max="980" step="20"></label>
      </div>
      <p class="small-note">閱讀設定與進度保存在本機瀏覽器；登入後可把章節收藏寫入雲端帳號。</p>
    </section>
    <article class="chapter-content">
      {article}
    </article>
    <section class="reader-comments" data-book-id="wuxing-theory-book3" data-chapter-path="{html.escape(s["filename"])}" data-chapter-title="{html.escape(s["title"])}">
      <h2>讀者評論</h2>
      <p>閱讀與評論不需要登入。評論送出後會先進入待審狀態，審核通過後公開顯示。</p>
      <form class="comment-form">
        <label><span>稱呼</span><input name="visitor_name" maxlength="80" placeholder="你的稱呼"></label>
        <label><span>評論</span><textarea name="body" maxlength="2000" required placeholder="寫下你的問題、感受或反駁"></textarea></label>
        <button class="button primary" type="submit">送出評論</button>
      </form>
      <p class="comment-status" aria-live="polite"></p>
      <div class="comment-list" data-comment-list></div>
    </section>
    <nav class="chapter-pager" aria-label="章節切換">{prev_link}{next_link}</nav>
  </main>
  <aside class="reader-nav" aria-label="章節目錄">
    <a class="back-home" href="../index.html">← 返回首頁</a>
    <label class="search-box compact">
      <span>搜尋</span>
      <input id="site-search" type="search" placeholder="搜尋全書">
    </label>
    <div id="search-results" class="search-results compact" aria-live="polite"></div>
    <nav>{aside}</nav>
  </aside>
</div>"""
        page = page_shell(
            title=f"{s['title']}｜{book_title}",
            body=body,
            base="../",
            description=plain_text(s["markdown"])[:150],
        )
        (CHAPTERS / s["filename"]).write_text(page, encoding="utf-8")


def build_formula_page(book_title: str) -> str:
    if not FORMULA_CANON.exists():
        raise FileNotFoundError(FORMULA_CANON)
    data = json.loads(FORMULA_CANON.read_text(encoding="utf-8"))
    formulas = data.get("formulas", [])
    rows = []
    for item in formulas:
        section_path = " / ".join(item.get("section_path") or [])
        guards = "、".join(item.get("anti_corruption_guards") or [])
        rows.append(
            f"""<article class="formula-card">
  <div class="formula-card-head">
    <span>{html.escape(item.get("formula_id", ""))}</span>
    <strong>{html.escape(item.get("operator_role", ""))}</strong>
  </div>
  <pre><code>{html.escape(item.get("formula", ""))}</code></pre>
  <dl>
    <div><dt>類別</dt><dd>{html.escape(item.get("category", ""))}</dd></div>
    <div><dt>聲明類型</dt><dd>{html.escape(item.get("claim_type", ""))}</dd></div>
    <div><dt>來源位置</dt><dd>{html.escape(section_path)}</dd></div>
    <div><dt>防污染守衛</dt><dd>{html.escape(guards)}</dd></div>
  </dl>
</article>"""
        )
    body = f"""{header("../")}
<main class="standalone-page">
  <article class="resource-content">
    <p class="edition">公開材料</p>
    <h1>104條公式正典</h1>
    <p class="resource-lead">這裡展示的是《物性論》公式算子正典庫。它的目的不是把公式當成裝飾，而是讓每一條公式都能說清楚自己的身份、角色、來源、聲明類型與防污染守衛。</p>
    <div class="resource-actions">
      <a class="button primary" href="FormulaOperatorCanon.json">下載 JSON</a>
      <a class="button" href="https://github.com/jorsonbei/wuxing-v32-v33-v34-reproduction/blob/main/release/FormulaOperatorCanon.json">查看復演倉庫版本</a>
    </div>
    <section class="resource-meta">
      <div><strong>{html.escape(str(data.get("formula_count", len(formulas))))}</strong><span>公式總數</span></div>
      <div><strong>{html.escape(data.get("route", ""))}</strong><span>生成路線</span></div>
      <div><strong>{html.escape(data.get("generated_at", ""))}</strong><span>生成時間</span></div>
    </section>
    <section class="formula-list">
      {"".join(rows)}
    </section>
  </article>
</main>"""
    return page_shell(
        title=f"104條公式正典｜{book_title}",
        body=body,
        base="../",
        description="《物性論》104條公式正典，包含公式、算子角色、聲明類型與防污染守衛。",
    )


def build_reproduction_page(book_title: str) -> str:
    cards = [
        (
            "復演倉庫",
            "V32 / V33 / V34 復演包、公式正典、在線復演室源碼與公開材料。",
            "https://github.com/jorsonbei/wuxing-v32-v33-v34-reproduction",
        ),
        (
            "復演包發佈頁",
            "固定版本發佈入口，方便後來者按同一套材料重跑與核對。",
            "https://github.com/jorsonbei/wuxing-v32-v33-v34-reproduction/releases/tag/v2026.07.03",
        ),
        (
            "在線復演室",
            "可視化入口，用瀏覽器查看復演流程與材料導覽。",
            "https://jorsonbei.github.io/wuxing-v32-v33-v34-reproduction/",
        ),
        (
            "公式正典 JSON",
            "104條公式與算子的原始結構化文件。",
            "FormulaOperatorCanon.json",
        ),
    ]
    card_html = "\n".join(
        f"""<a class="resource-card" href="{html.escape(url)}">
  <strong>{html.escape(title)}</strong>
  <span>{html.escape(desc)}</span>
</a>"""
        for title, desc, url in cards
    )
    body = f"""{header("../")}
<main class="standalone-page">
  <article class="resource-content">
    <p class="edition">公開材料</p>
    <h1>公開復演入口</h1>
    <p class="resource-lead">這裡放置《物性論》外部檢查與復演相關入口。它的意義不是要求讀者相信作者，而是把信任從語氣轉移到材料、流程、代碼、失敗定位和邊界聲明上。</p>
    <section class="resource-grid">{card_html}</section>
    <section class="resource-note">
      <h2>如何閱讀這些入口</h2>
      <p>不要把復演包當成「一鍵驗證真理」的軟體。真正的復演，是檢查邊界、破壞假設、尋找失敗，並確認系統是否會在不該通過的地方主動亮紅燈。</p>
      <p>如果你只看見綠色通過，就匆忙說「理論已經被證明」，那不是復演。真正有價值的是：你能否找出它在哪裡能過、在哪裡不能過、在哪裡仍然等待後來者推開新的房間。</p>
    </section>
  </article>
</main>"""
    return page_shell(
        title=f"公開復演入口｜{book_title}",
        body=body,
        base="../",
        description="《物性論》V32 / V33 / V34 復演倉庫、發佈頁、在線復演室與公式正典入口。",
    )


def build_resource_pages(book_title: str) -> None:
    RESOURCES.mkdir(exist_ok=True)
    (RESOURCES / "formula-canon.html").write_text(
        build_formula_page(book_title), encoding="utf-8"
    )
    (RESOURCES / "reproduction.html").write_text(
        build_reproduction_page(book_title), encoding="utf-8"
    )


def write_assets(sections: list[dict]) -> None:
    search = [
        {
            "title": s["title"],
            "url": "chapters/" + s["filename"],
            "text": plain_text(s["markdown"])[:5000],
            "excerpt": plain_text(s["markdown"])[:180],
        }
        for s in sections
    ]
    search.extend(
        [
            {
                "title": "104條公式正典",
                "url": "resources/formula-canon.html",
                "text": "104條公式正典 公式算子正典庫 FormulaOperatorCanon NoBackfit NoDoubleCounting NoTargetRead CovarianceCourt",
                "excerpt": "逐條展示公式、算子角色、聲明類型、來源位置與防污染守衛。",
            },
            {
                "title": "公開復演入口",
                "url": "resources/reproduction.html",
                "text": "公開復演入口 V32 V33 V34 復演倉庫 復演包 發佈頁 在線復演室 FormulaOperatorCanon",
                "excerpt": "復演倉庫、發佈頁、在線復演室與公式正典入口。",
            },
        ]
    )
    (ASSETS / "search-index.json").write_text(
        json.dumps(search, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    sitemap = [SITE_URL]
    sitemap += [SITE_URL + "chapters/" + s["filename"] for s in sections]
    sitemap += [
        SITE_URL + "resources/formula-canon.html",
        SITE_URL + "resources/reproduction.html",
        SITE_URL + "resources/FormulaOperatorCanon.json",
    ]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in sitemap)
        + "\n</urlset>\n",
        encoding="utf-8",
    )


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    book_title, sections = split_sections(markdown)
    for idx, s in enumerate(sections, 1):
        s["filename"] = filename_for(s["title"], idx)
        s["type_label"] = {
            "part": "部",
            "appendix": "附錄",
            "afterword": "後記",
            "preface": "序章",
        }.get(category(s["title"]), "章")
    CHAPTERS.mkdir(exist_ok=True)
    for old in CHAPTERS.glob("*.html"):
        old.unlink()
    build_chapter_pages(book_title, sections)
    build_resource_pages(book_title)
    (ROOT / "index.html").write_text(build_index(book_title, sections), encoding="utf-8")
    write_assets(sections)
    print(f"built {len(sections)} sections")


if __name__ == "__main__":
    main()
