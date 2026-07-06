#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "book" / "wuxing-theory-book3.md"
CHAPTERS = ROOT / "chapters"
ASSETS = ROOT / "assets"
RESOURCES = ROOT / "resources"
SITE_URL = "https://jorsonbei.github.io/wuxing-theory-book3/"
FORMULA_CANON = RESOURCES / "FormulaOperatorCanon.json"
ASSET_VERSION = "20260706-mobile-reader"


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
    part = re.search(r"第(.+?)部", title)
    if part:
        n = cn_to_int(part.group(1)) or index
        return f"part-{n:02d}.html"
    chapter = re.search(r"第(.+?)章", title)
    if chapter:
        n = cn_to_int(chapter.group(1)) or index
        return f"chapter-{n:02d}.html"
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
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <script defer src="{base}assets/site.js?v={ASSET_VERSION}"></script>
</head>
<body data-base="{base}">
{body}
</body>
</html>
"""


def header(base: str = "") -> str:
    return f"""<header class="site-header">
  <a class="brand" href="{base}index.html">宇宙是光之流體</a>
  <nav class="top-links">
    <a href="{base}index.html#catalog">目錄</a>
    <a href="{base}resources/formula-canon.html">公式正典</a>
    <a href="{base}resources/reproduction.html">復演入口</a>
    <a href="{base}book/wuxing-theory-book3.md">Markdown</a>
    <a href="{base}book/wuxing-theory-book3.docx">DOCX</a>
    <a href="https://github.com/jorsonbei/wuxing-theory-book3">GitHub</a>
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
      <p class="edition">第二版 · 繁體中文公開閱讀版</p>
      <h1>{html.escape(book_title)}</h1>
      <p class="lead">一場從宇宙底層、物理公式、復演實驗到 AI 時代的範式重構。這不是把舊公式重新包裝，而是追問：世界究竟靠什麼承載、傳播、留下來，並接受外部審判。</p>
      <div class="hero-actions">
        <a class="button primary" href="chapters/preface.html">開始閱讀</a>
        <a class="button" href="#catalog">查看目錄</a>
      </div>
      <div class="stats">
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

  <section class="open-materials">
    <h2>公開材料</h2>
    <div class="material-grid">
      <a href="book/wuxing-theory-book3.md"><strong>Markdown 原稿</strong><span>適合校對、版本管理和引用。</span></a>
      <a href="book/wuxing-theory-book3.docx"><strong>KDP DOCX 書稿</strong><span>保留出版排版版本。</span></a>
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
    <article class="chapter-content">
      {article}
    </article>
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
      <p>不要把復演包當成「一鍵驗證真理」的軟件。真正的復演，是檢查邊界、破壞假設、尋找失敗，並確認系統是否會在不該通過的地方主動亮紅燈。</p>
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
