(function () {
  const STORAGE_PREFIX = "wuxing-reader:";
  const base = document.body?.dataset?.base || "";

  function readJson(key, fallback) {
    try {
      const raw = localStorage.getItem(STORAGE_PREFIX + key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  function writeJson(key, value) {
    try {
      localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
    } catch {
      // Local storage may be blocked in strict privacy modes. Reading still works.
    }
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function toast(message) {
    let node = document.querySelector(".site-toast");
    if (!node) {
      node = document.createElement("div");
      node.className = "site-toast";
      document.body.appendChild(node);
    }
    node.textContent = message;
    node.classList.add("show");
    window.clearTimeout(node._hideTimer);
    node._hideTimer = window.setTimeout(() => node.classList.remove("show"), 2600);
  }

  async function initSearch() {
    const input = document.getElementById("site-search");
    const results = document.getElementById("search-results");
    if (!input || !results) return;

    let index = [];
    try {
      const response = await fetch(`${base}assets/search-index.json`);
      index = await response.json();
    } catch {
      results.innerHTML = '<p class="search-result"><strong>搜尋索引暫時無法載入。</strong></p>';
      return;
    }

    function normalize(value) {
      return (value || "").toString().trim().toLowerCase();
    }

    function render(items, query) {
      if (!query) {
        results.innerHTML = "";
        return;
      }
      if (!items.length) {
        results.innerHTML = '<p class="search-result"><strong>沒有找到相關章節。</strong><span>換一個更短或更核心的關鍵詞試試。</span></p>';
        return;
      }
      results.innerHTML = items.slice(0, 8).map((item) => {
        const url = base + item.url;
        return `<a class="search-result" href="${url}">
          <strong>${escapeHtml(item.title)}</strong>
          <span>${escapeHtml(item.excerpt)}</span>
        </a>`;
      }).join("");
    }

    input.addEventListener("input", () => {
      const query = normalize(input.value);
      if (query.length < 2) {
        render([], "");
        return;
      }
      const terms = query.split(/\s+/).filter(Boolean);
      const matches = index
        .map((item) => {
          const haystack = normalize(`${item.title} ${item.text}`);
          const score = terms.reduce((sum, term) => sum + (haystack.includes(term) ? 1 : 0), 0);
          return { item, score };
        })
        .filter((entry) => entry.score > 0)
        .sort((a, b) => b.score - a.score || a.item.title.localeCompare(b.item.title, "zh-Hant"))
        .map((entry) => entry.item);
      render(matches, query);
    });
  }

  function applyReaderSettings(settings) {
    const resolved = {
      font: settings.font || "serif",
      theme: settings.theme || "paper",
      size: settings.size || "19",
      line: settings.line || "1.95",
      width: settings.width || "820",
    };

    document.body.dataset.readerFont = resolved.font;
    document.body.dataset.readerTheme = resolved.theme;
    document.documentElement.style.setProperty("--reader-font-size", `${resolved.size}px`);
    document.documentElement.style.setProperty("--reader-line-height", resolved.line);
    document.documentElement.style.setProperty("--reader-width-dynamic", `${resolved.width}px`);

    const controls = {
      font: document.getElementById("reader-font"),
      theme: document.getElementById("reader-theme"),
      size: document.getElementById("reader-size"),
      line: document.getElementById("reader-line"),
      width: document.getElementById("reader-width"),
    };
    Object.entries(controls).forEach(([key, control]) => {
      if (control) control.value = resolved[key];
    });
  }

  function initReaderSettings() {
    const toolbar = document.querySelector(".reader-toolbar");
    const saved = readJson("settings", {});
    applyReaderSettings(saved);
    if (!toolbar) return;

    ["font", "theme", "size", "line", "width"].forEach((key) => {
      const control = document.getElementById(`reader-${key}`);
      if (!control) return;
      control.addEventListener("input", () => {
        const current = readJson("settings", {});
        current[key] = control.value;
        writeJson("settings", current);
        applyReaderSettings(current);
      });
    });
  }

  function getCurrentTitle() {
    const heading = document.querySelector(".chapter-content h1, h1");
    return heading ? heading.textContent.trim() : document.title;
  }

  function currentRelativeHref() {
    const parts = location.pathname.split("/").filter(Boolean);
    const chaptersIndex = parts.lastIndexOf("chapters");
    if (chaptersIndex >= 0 && parts[chaptersIndex + 1]) {
      return `chapters/${parts[chaptersIndex + 1]}`;
    }
    return parts.at(-1) || "index.html";
  }

  function initProgress() {
    const article = document.querySelector(".chapter-content");
    if (!article) return;

    const progressBar = document.getElementById("reader-progress");
    const key = `progress:${location.pathname}`;
    const restoreButton = document.querySelector(".restore-reading");

    function metrics() {
      const rect = article.getBoundingClientRect();
      const articleTop = rect.top + window.scrollY;
      const scrollable = Math.max(article.offsetHeight - window.innerHeight * 0.65, 1);
      const raw = (window.scrollY - articleTop) / scrollable;
      const percent = Math.min(100, Math.max(0, Math.round(raw * 100)));
      return { articleTop, percent };
    }

    function update() {
      const { percent } = metrics();
      if (progressBar) progressBar.style.width = `${percent}%`;
      writeJson(key, {
        y: Math.max(0, Math.round(window.scrollY)),
        percent,
        title: getCurrentTitle(),
        path: location.pathname,
        href: currentRelativeHref(),
        updatedAt: new Date().toISOString(),
      });
      writeJson("lastRead", {
        y: Math.max(0, Math.round(window.scrollY)),
        percent,
        title: getCurrentTitle(),
        path: location.pathname,
        href: currentRelativeHref(),
        updatedAt: new Date().toISOString(),
      });
    }

    let ticking = false;
    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        ticking = false;
        update();
      });
    }, { passive: true });
    update();

    if (restoreButton) {
      restoreButton.addEventListener("click", () => {
        const saved = readJson(key, null);
        if (!saved) {
          toast("這一章還沒有本機閱讀記錄。");
          return;
        }
        window.scrollTo({ top: saved.y || 0, behavior: "smooth" });
      });
    }
  }

  function initLastReadLink() {
    const last = readJson("lastRead", null);
    const heroActions = document.querySelector(".hero-actions");
    if (!last || !last.path || !heroActions) return;
    const link = document.createElement("a");
    link.className = "button";
    link.href = last.href || last.path.replace(/^\//, "");
    link.textContent = `繼續閱讀 ${Math.max(0, last.percent || 0)}%`;
    heroActions.appendChild(link);
  }

  function initFavorites() {
    const buttons = document.querySelectorAll(".local-favorite");
    if (!buttons.length) return;

    function favorites() {
      return readJson("favorites", []);
    }

    function saveFavorite(item) {
      const list = favorites().filter((entry) => entry.id !== item.id);
      list.unshift({ ...item, savedAt: new Date().toISOString() });
      writeJson("favorites", list.slice(0, 80));
    }

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.dataset.favoriteId || location.pathname;
        const title = button.dataset.favoriteTitle || getCurrentTitle();
        saveFavorite({ id, title, path: location.pathname, href: currentRelativeHref() });
        button.textContent = "已收藏";
        toast("已保存到本機收藏。正式帳號收藏需要後端接入。");
      });
    });
  }

  function initGatedActions() {
    document.querySelectorAll(".gated-action").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.actionName || "此功能";
        toast(`${action} 需要登入系統與私有儲存接入。當前版本先保留入口位。`);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initSearch();
    initReaderSettings();
    initProgress();
    initLastReadLink();
    initFavorites();
    initGatedActions();
  });
})();
