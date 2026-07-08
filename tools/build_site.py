#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("WUXING_SOURCE_MD", ROOT / "book" / "wuxing-theory-book3.md"))
CHAPTERS = ROOT / "chapters"
ASSETS = ROOT / "assets"
RESOURCES = ROOT / "resources"
SITE_URL = "https://jorsonbei.github.io/wuxing-theory-book3/"
FORMULA_CANON = RESOURCES / "FormulaOperatorCanon.json"
ASSET_VERSION = "20260708-platform-backend-v1"
BOOK_AUTHORS = ["景龍鎖", "貝記勝"]
BOOK_DESCRIPTION = "《宇宙是光之流體：物性論作為新的科學範式》公開閱讀網站，提供完整章節、104條公式正典、HFCD復演入口與物性AI框架。"
CORE_SEO_KEYWORDS = [
    "物性論",
    "宇宙是光之流體",
    "光之流體",
    "新科學範式",
    "宇宙不是空的",
    "背景海",
    "狀態接力",
    "結構化停頓",
    "勢差",
    "關係腔",
    "顯化之門",
    "觀察刻度",
    "物性 AI",
    "狀態生成",
    "AI 幻覺",
    "HFCD",
    "104條公式正典",
    "復演包",
    "W 玻色子",
    "標準模型",
    "EWPO",
    "Higgs",
]
TOPIC_PAGES = [
    {
        "filename": "what-is-wuxing-theory.html",
        "title": "物性論是什麼",
        "subtitle": "從空房間、光子小球與時間河流之外，重新理解宇宙如何生成穩定結構。",
        "description": "物性論是《宇宙是光之流體》提出的新科學範式，從背景海、狀態接力、結構化停頓、關係腔與顯化之門重新理解物質、時間、公式與智能。",
        "keywords": ["物性論", "物性論是什麼", "宇宙是光之流體", "背景海", "新科學範式"],
        "paragraphs": [
            "物性論不是把某一個公式改寫成新的符號，也不是在舊世界觀上增加一個漂亮比喻。它首先拆開的是我們習以為常的直覺：世界不是一個空盒子，光不是被丟出去的小球，物質不是天然死硬的磚塊，時間也不是把一切推向前方的河流。",
            "在這套語言裡，宇宙更像一片能承載狀態、傳播擾動、留下穩定結構的背景海。能留下來的東西，不是因為它被宇宙特別偏愛，而是因為它在身份、能量、承載、核心、邊界、顯化與黑點審查中一次次沒有崩潰。",
            "因此，物性論真正關心的不是一句口號，而是一條生成路徑：狀態如何被激發，如何被鄰近結構接住，如何在關係腔中獲得位置，如何穿過觀察刻度並被世界記錄。",
        ],
        "links": [("從序章開始閱讀", "chapters/preface.html"), ("第一章：世界不是空房間", "chapters/chapter-01.html"), ("104條公式正典", "resources/formula-canon.html")],
    },
    {
        "filename": "universe-light-fluid.html",
        "title": "宇宙不是空的：光、物質與時間的物性入口",
        "subtitle": "用普通讀者能進入的方式，理解世界不是空房間、光是狀態接力、物質是結構化停頓。",
        "description": "從物性論前三章進入《宇宙是光之流體》：宇宙不是空房間，光不是小球快遞，物質是一場結構化的停頓，時間則是事件留下的賬本。",
        "keywords": ["宇宙不是空的", "光不是小球快遞", "狀態接力", "結構化停頓", "時間不是河流"],
        "paragraphs": [
            "很多人理解宇宙時，會先想像一個巨大空房間，裡面擺著星球、粒子、光線與生命。物性論的第一步，是把這個房間模型拆掉：如果宇宙底層真的只是空，狀態就沒有地方被傳遞，關係也沒有地方被承載。",
            "光在這裡不再只是穿越虛無的小球，而是一場狀態接力。它像體育場裡的人浪，真正移動的不是某個人從頭跑到尾，而是一個狀態被附近的人接住、翻譯、再傳給下一個位置。",
            "物質也不再被理解成死硬磚塊，而是流動中的穩定停頓。像河流中的漩渦，它內部每一秒都在運動，卻能長時間保持可辨認的形狀。這正是物性論理解物質、生命與秩序的入口。",
        ],
        "links": [("第一章：世界不是空房間", "chapters/chapter-01.html"), ("第二章：光不是小球快遞", "chapters/chapter-02.html"), ("第三章：物質的真相", "chapters/chapter-03.html")],
    },
    {
        "filename": "physics-formulas-constants.html",
        "title": "物理公式與常數：物性論如何重讀舊公式",
        "subtitle": "從牛頓、麥克斯韋、薛定諤、愛因斯坦到常數，尋找公式背後共同的母結構。",
        "description": "物性論從公式形狀與常數角色重讀牛頓、麥克斯韋、薛定諤、愛因斯坦與熱力學，把物理公式放回共同的生成結構中理解。",
        "keywords": ["物理公式", "物理常數", "牛頓", "麥克斯韋", "薛定諤", "愛因斯坦", "物性歸根"],
        "paragraphs": [
            "一本真正有力量的新範式，不能只會否定舊理論。物性論對舊公式的態度，不是燒掉舊地圖，而是追問：為什麼這些公式會長成這種形狀？它們背後是否共享更深的結構？",
            "牛頓公式中的力，物性論會重讀為坡度和勢差；麥克斯韋方程中的場，會被放回關係腔的局域彎曲；薛定諤方程中的波函數，會被放進可能性、相位與顯化之門的邏輯裡。",
            "常數也不再只是表格裡冰冷的數字。光速、普朗克常數、引力常數與玻爾茲曼常數，更像宇宙不同賬本之間的轉接頭，規定時間、空間、能量、相位、熱與幾何如何彼此換算。",
        ],
        "links": [("第九章：新範式與舊公式", "chapters/chapter-09.html"), ("第十章：牛頓與引力", "chapters/chapter-10.html"), ("第十二章：常數不是死數字", "chapters/chapter-12.html")],
    },
    {
        "filename": "standard-model-w-boson-ewpo.html",
        "title": "物性論與標準模型：W 玻色子、Higgs 與 EWPO",
        "subtitle": "從外部審判看一套理論如何面對標準模型、協方差、Higgs 靜默與 Flavour 邊界。",
        "description": "物性論第五部進入標準模型外部審判，討論W玻色子質量、EWPO協方差、Higgs靜默與Flavour隔離腔體如何檢查新範式。",
        "keywords": ["標準模型", "W 玻色子", "EWPO", "Higgs", "Flavour", "外部審判"],
        "paragraphs": [
            "如果一套新範式只在自己的語言裡漂亮，它還沒有真正走上科學的法庭。物性論第五部把問題推到外部：標準模型、W 玻色子質量、EWPO 協方差、Higgs 與 Flavour 邊界，都是世界拿出來的硬尺。",
            "這裡的重點不是用華麗語氣宣告勝利，而是看一套內部生成邏輯能不能在外部讀數面前保持克制。命中不是終點，邊界同樣重要。哪裡能通過，哪裡不能亂動，哪裡必須隔離，都要被清楚標出。",
            "這種寫法也讓嚴肅讀者知道：物性論不是只把物理名詞當裝飾，而是在把自己的主張推向可檢查、可反駁、可被後來者追問的地方。",
        ],
        "links": [("第十七章：標準模型白盒化", "chapters/chapter-17.html"), ("第十八章：W 玻色子精準盲測", "chapters/chapter-18.html"), ("第十九章：EWPO 協方差", "chapters/chapter-19.html")],
    },
    {
        "filename": "wuxing-ai-state-generation.html",
        "title": "物性 AI 是什麼：從詞語預測走向狀態生成",
        "subtitle": "為什麼大模型看起來懂，卻常常沒有接住世界？物性 AI 試圖把智能重新接回狀態與外部裁判。",
        "description": "物性AI把AI幻覺、大模型成本、世界模型與狀態生成放在同一條路徑中理解，討論下一代AI如何從詞語預測走向物性狀態生成。",
        "keywords": ["物性 AI", "狀態生成", "AI 幻覺", "大模型", "世界模型", "詞語預測"],
        "paragraphs": [
            "大模型最迷人的地方，是它太會接話；大模型最危險的地方，也是它太會接話。它能把語言接得流暢，卻不一定真正接住世界的狀態。這就是物性 AI 要拆開的問題。",
            "在物性論裡，智能不能只被理解為下一個詞的預測。真正可靠的智能，要能辨認狀態、承載關係、通過外部裁判、記錄失敗，並在錯誤成本很高的現場減少走錯路。",
            "因此，物性 AI 的核心不是再做一個漂亮聊天界面，而是把 AI 從語言表面的順滑，推向狀態生成、世界校驗、成本控制與可復演的行動路徑。",
        ],
        "links": [("第二十二章：會接話的鸚鵡", "chapters/chapter-22.html"), ("第二十三章：大模型的真實賬單", "chapters/chapter-23.html"), ("第二十四章：物性 AI 六層架構", "chapters/chapter-24.html")],
    },
    {
        "filename": "hfcd-reproduction-formula-canon.html",
        "title": "HFCD 復演與 104 條公式正典",
        "subtitle": "把信任從語氣交給材料、流程、代碼、公式、邊界與失敗定位。",
        "description": "物性論公開HFCD復演入口、V32/V33/V34復演包、104條公式正典與FormulaOperatorCanon.json，方便讀者檢查、重跑與反駁。",
        "keywords": ["HFCD", "復演包", "104條公式正典", "FormulaOperatorCanon", "開源復演"],
        "paragraphs": [
            "對一套龐大的理論來說，最危險的不是被人反駁，而是只能靠作者的語氣活著。物性論把公式正典、復演包與在線復演入口公開出來，就是要讓讀者看見材料，而不只是聽見宣告。",
            "104 條公式正典不是把公式堆成裝飾，而是逐條標出身份、角色、來源、聲明類型與防污染守衛。這讓每一條公式都必須承認自己能說什麼、不能說什麼。",
            "HFCD 復演入口則把檢查變成公共路徑。讀者可以從倉庫、發佈頁、在線復演室與 JSON 正典進入，追問每一步如何產生、如何通過、如何失敗。",
        ],
        "links": [("104條公式正典", "resources/formula-canon.html"), ("公開復演入口", "resources/reproduction.html"), ("第二十六章：公式正典與證據矩陣", "chapters/chapter-26.html")],
    },
]


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


def absolute_url(path: str = "") -> str:
    return SITE_URL + path.lstrip("/")


def compact_text(value: str, limit: int = 156) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rstrip("，。、；：,. ")
    return cut + "…"


def extract_keywords(*texts: str, extra: list[str] | None = None, limit: int = 12) -> list[str]:
    joined = " ".join(texts)
    keywords: list[str] = []
    for item in extra or []:
        if item and item not in keywords:
            keywords.append(item)
    for item in CORE_SEO_KEYWORDS:
        if item in joined and item not in keywords:
            keywords.append(item)
    for item in CORE_SEO_KEYWORDS:
        if item not in keywords:
            keywords.append(item)
        if len(keywords) >= limit:
            break
    return keywords[:limit]


def author_schema() -> list[dict]:
    return [{"@type": "Person", "name": name} for name in BOOK_AUTHORS]


def book_schema(book_title: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": book_title,
        "alternateName": ["宇宙是光之流體", "物性論3"],
        "description": BOOK_DESCRIPTION,
        "inLanguage": "zh-Hant",
        "author": author_schema(),
        "url": SITE_URL,
        "image": absolute_url("assets/cover.jpg"),
        "keywords": CORE_SEO_KEYWORDS,
        "workExample": {
            "@type": "Book",
            "bookFormat": "https://schema.org/EBook",
            "url": SITE_URL,
            "inLanguage": "zh-Hant",
        },
    }


def breadcrumb_schema(items: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": idx,
                "name": name,
                "item": absolute_url(url),
            }
            for idx, (name, url) in enumerate(items, 1)
        ],
    }


def article_schema(
    *,
    headline: str,
    description: str,
    url: str,
    keywords: list[str],
    book_title: str,
    position: int | None = None,
) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "description": description,
        "inLanguage": "zh-Hant",
        "author": author_schema(),
        "isPartOf": {"@type": "Book", "name": book_title, "url": SITE_URL},
        "mainEntityOfPage": absolute_url(url),
        "url": absolute_url(url),
        "image": absolute_url("assets/cover.jpg"),
        "keywords": keywords,
    }
    if position is not None:
        data["position"] = position
    return data


def json_ld_block(data: dict | list[dict] | None) -> str:
    if not data:
        return ""
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'  <script type="application/ld+json">\n{payload}\n  </script>\n'


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
    description: str = BOOK_DESCRIPTION,
    canonical_url: str | None = None,
    og_type: str = "website",
    keywords: list[str] | None = None,
    structured_data: dict | list[dict] | None = None,
) -> str:
    safe_title = html.escape(title)
    description = compact_text(description, 160)
    safe_desc = html.escape(description)
    canonical_url = canonical_url or SITE_URL
    safe_canonical = html.escape(canonical_url)
    keyword_meta = ""
    if keywords:
        keyword_meta = f'  <meta name="keywords" content="{html.escape(", ".join(keywords))}">\n'
    schema = json_ld_block(structured_data)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <meta name="description" content="{safe_desc}">
{keyword_meta}  <link rel="canonical" href="{safe_canonical}">
  <meta property="og:title" content="{safe_title}">
  <meta property="og:description" content="{safe_desc}">
  <meta property="og:type" content="{html.escape(og_type)}">
  <meta property="og:url" content="{safe_canonical}">
  <meta property="og:site_name" content="物性論閱讀平台">
  <meta property="og:locale" content="zh_TW">
  <meta property="og:image" content="{absolute_url("assets/cover.jpg")}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{safe_title}">
  <meta name="twitter:description" content="{safe_desc}">
  <meta name="twitter:image" content="{absolute_url("assets/cover.jpg")}">
  <link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{base}assets/styles.css?v={ASSET_VERSION}">
{schema}  <script>
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
    topic_cards = "\n".join(
        f"""<a class="resource-card" href="resources/{html.escape(topic['filename'])}">
  <strong>{html.escape(topic['title'])}</strong>
  <span>{html.escape(topic['description'])}</span>
</a>"""
        for topic in TOPIC_PAGES
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
      <p>後續每一個版本、每一個分冊，都可以放在這裡。當前先公開主書，後續可加入入門版、AI 版、復演版、公式版與英文版。</p>
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

  <section class="search-panel" aria-labelledby="search-title">
    <h2 id="search-title">站內搜尋</h2>
    <p>輸入「W 玻色子」「物性 AI」「關係腔」「復演」等關鍵詞，可以快速定位章節。</p>
    <label class="search-box">
      <span>搜尋</span>
      <input id="site-search" type="search" placeholder="輸入關鍵詞">
    </label>
    <div id="search-results" class="search-results" aria-live="polite"></div>
  </section>

  <section id="topics" class="open-materials topic-index">
    <h2>主題索引</h2>
    <p>把書中最容易被搜尋、引用與分享的入口整理成獨立頁面，方便新讀者先抓住核心問題。</p>
    <div class="resource-grid">{topic_cards}</div>
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
    keywords = extract_keywords(book_title, BOOK_DESCRIPTION, extra=["物性論公開閱讀", "物性論3"])
    return page_shell(
        title=f"{book_title}｜物性論公開閱讀",
        body=body,
        base="",
        description=BOOK_DESCRIPTION,
        canonical_url=SITE_URL,
        og_type="book",
        keywords=keywords,
        structured_data=[
            book_schema(book_title),
            breadcrumb_schema([("首頁", "")]),
        ],
    )


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
        section_text = plain_text(s["markdown"])
        desc = compact_text(f"閱讀《{s['title']}》：{section_text}", 155)
        keywords = extract_keywords(s["title"], section_text)
        page_url = f"chapters/{s['filename']}"
        page = page_shell(
            title=f"{s['title']}｜{book_title}",
            body=body,
            base="../",
            description=desc,
            canonical_url=absolute_url(page_url),
            og_type="article",
            keywords=keywords,
            structured_data=[
                article_schema(
                    headline=s["title"],
                    description=desc,
                    url=page_url,
                    keywords=keywords,
                    book_title=book_title,
                    position=i + 1,
                ),
                breadcrumb_schema([("首頁", ""), ("章節", "index.html#catalog"), (s["title"], page_url)]),
            ],
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
    desc = "《物性論》104條公式正典，包含公式、算子角色、聲明類型、來源位置與防污染守衛。"
    keywords = extract_keywords(desc, extra=["104條公式正典", "FormulaOperatorCanon", "公式算子正典庫"])
    return page_shell(
        title=f"104條公式正典｜{book_title}",
        body=body,
        base="../",
        description=desc,
        canonical_url=absolute_url("resources/formula-canon.html"),
        og_type="article",
        keywords=keywords,
        structured_data=[
            article_schema(
                headline="104條公式正典",
                description=desc,
                url="resources/formula-canon.html",
                keywords=keywords,
                book_title=book_title,
            ),
            breadcrumb_schema([("首頁", ""), ("資料中心", "index.html#downloads"), ("104條公式正典", "resources/formula-canon.html")]),
        ],
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
    desc = "《物性論》V32 / V33 / V34 復演倉庫、發佈頁、在線復演室與公式正典入口。"
    keywords = extract_keywords(desc, extra=["HFCD 復演", "V32 V33 V34", "公開復演入口", "復演包"])
    return page_shell(
        title=f"公開復演入口｜{book_title}",
        body=body,
        base="../",
        description=desc,
        canonical_url=absolute_url("resources/reproduction.html"),
        og_type="article",
        keywords=keywords,
        structured_data=[
            article_schema(
                headline="公開復演入口",
                description=desc,
                url="resources/reproduction.html",
                keywords=keywords,
                book_title=book_title,
            ),
            breadcrumb_schema([("首頁", ""), ("資料中心", "index.html#downloads"), ("公開復演入口", "resources/reproduction.html")]),
        ],
    )


def build_resource_pages(book_title: str) -> None:
    RESOURCES.mkdir(exist_ok=True)
    (RESOURCES / "formula-canon.html").write_text(
        build_formula_page(book_title), encoding="utf-8"
    )
    (RESOURCES / "reproduction.html").write_text(
        build_reproduction_page(book_title), encoding="utf-8"
    )
    build_topic_pages(book_title)


def build_topic_pages(book_title: str) -> None:
    for topic in TOPIC_PAGES:
        links = "\n".join(
            f'<a class="resource-card" href="../{html.escape(href)}"><strong>{html.escape(label)}</strong><span>進入相關章節或公開材料。</span></a>'
            for label, href in topic["links"]
        )
        paragraphs = "\n".join(f"<p>{html.escape(p)}</p>" for p in topic["paragraphs"])
        keyword_list = "".join(f"<li>{html.escape(k)}</li>" for k in topic["keywords"])
        body = f"""{header("../")}
<main class="standalone-page">
  <article class="resource-content topic-content">
    <p class="edition">物性論專題入口</p>
    <h1>{html.escape(topic["title"])}</h1>
    <p class="resource-lead">{html.escape(topic["subtitle"])}</p>
    <section class="topic-body">{paragraphs}</section>
    <section class="topic-links">
      <h2>延伸閱讀</h2>
      <div class="resource-grid">{links}</div>
    </section>
    <section class="topic-keywords" aria-label="相關關鍵詞">
      <h2>相關關鍵詞</h2>
      <ul>{keyword_list}</ul>
    </section>
  </article>
</main>"""
        url = f"resources/{topic['filename']}"
        keywords = extract_keywords(topic["title"], topic["description"], extra=topic["keywords"])
        page = page_shell(
            title=f"{topic['title']}｜{book_title}",
            body=body,
            base="../",
            description=topic["description"],
            canonical_url=absolute_url(url),
            og_type="article",
            keywords=keywords,
            structured_data=[
                article_schema(
                    headline=topic["title"],
                    description=topic["description"],
                    url=url,
                    keywords=keywords,
                    book_title=book_title,
                ),
                breadcrumb_schema([("首頁", ""), ("物性論專題", "index.html#topics"), (topic["title"], url)]),
            ],
        )
        (RESOURCES / topic["filename"]).write_text(page, encoding="utf-8")


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
    search.extend(
        {
            "title": topic["title"],
            "url": "resources/" + topic["filename"],
            "text": " ".join([topic["title"], topic["subtitle"], topic["description"], *topic["keywords"], *topic["paragraphs"]]),
            "excerpt": topic["description"],
        }
        for topic in TOPIC_PAGES
    )
    (ASSETS / "search-index.json").write_text(
        json.dumps(search, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    sitemap = [SITE_URL]
    sitemap += [SITE_URL + "chapters/" + s["filename"] for s in sections]
    sitemap += [SITE_URL + "resources/" + topic["filename"] for topic in TOPIC_PAGES]
    sitemap += [
        SITE_URL + "resources/formula-canon.html",
        SITE_URL + "resources/reproduction.html",
        SITE_URL + "resources/FormulaOperatorCanon.json",
    ]
    lastmod = date.today().isoformat()
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(
            f"  <url><loc>{html.escape(url)}</loc><lastmod>{lastmod}</lastmod></url>"
            for url in sitemap
        )
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
