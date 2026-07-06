(async function () {
  const base = document.body?.dataset?.base || "";
  const input = document.getElementById("site-search");
  const results = document.getElementById("search-results");
  if (!input || !results) return;

  let index = [];
  try {
    const response = await fetch(`${base}assets/search-index.json`);
    index = await response.json();
  } catch (error) {
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

  function escapeHtml(value) {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
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
})();
