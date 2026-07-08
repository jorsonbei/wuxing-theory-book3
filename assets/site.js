(function () {
  const STORAGE_PREFIX = "wuxing-reader:";
  const base = document.body?.dataset?.base || "";
  const config = window.WUXING_PLATFORM_CONFIG || {};
  let supabaseClient = null;
  let currentSession = null;

  function platformEnabled() {
    return Boolean(
      config.enabled &&
      config.supabaseUrl &&
      config.supabaseAnonKey &&
      window.supabase?.createClient
    );
  }

  function getDownloadFunctionUrl() {
    if (config.downloadFunctionUrl) return config.downloadFunctionUrl;
    if (!config.supabaseUrl) return "";
    return `${config.supabaseUrl.replace(/\/$/, "")}/functions/v1/download`;
  }

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
    node._hideTimer = window.setTimeout(() => node.classList.remove("show"), 3000);
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
      return { percent };
    }

    function update() {
      const { percent } = metrics();
      if (progressBar) progressBar.style.width = `${percent}%`;
      const record = {
        y: Math.max(0, Math.round(window.scrollY)),
        percent,
        title: getCurrentTitle(),
        path: location.pathname,
        href: currentRelativeHref(),
        updatedAt: new Date().toISOString(),
      };
      writeJson(key, record);
      writeJson("lastRead", record);
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

  function setAuthStatus(message) {
    const node = document.querySelector(".auth-status");
    if (node) node.textContent = message || "";
  }

  function openAuthModal(message) {
    const modal = document.getElementById("auth-modal");
    if (!modal) return;
    if (message) setAuthStatus(message);
    modal.hidden = false;
    const input = document.getElementById("auth-email-input");
    if (input) input.focus();
  }

  function closeAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.hidden = true;
  }

  function openFavoritesModal() {
    const modal = document.getElementById("favorites-modal");
    if (modal) modal.hidden = false;
  }

  function closeFavoritesModal() {
    const modal = document.getElementById("favorites-modal");
    if (modal) modal.hidden = true;
  }

  function resolveRelativeLink(href) {
    if (!href) return base || "index.html";
    if (/^(https?:)?\/\//.test(href) || href.startsWith("#")) return href;
    return `${base}${href}`.replace(/\/{2,}/g, "/");
  }

  function renderFavoriteList(items, statusText) {
    const status = document.querySelector(".favorite-status");
    const list = document.querySelector("[data-favorite-list]");
    if (status) status.textContent = statusText || "";
    if (!list) return;
    if (!items.length) {
      list.innerHTML = '<p class="comment-empty">目前還沒有收藏。</p>';
      return;
    }
    list.innerHTML = items.map((item) => {
      const title = item.item_title || item.title || "未命名收藏";
      const type = item.item_type || item.type || "chapter";
      const href = item.item_url || item.href || item.path || "";
      const updated = item.updated_at || item.savedAt || "";
      const date = updated ? new Date(updated).toLocaleDateString("zh-Hant") : "";
      return `<a class="favorite-item" href="${escapeHtml(resolveRelativeLink(href))}">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(type === "book" ? "書籍" : type === "resource" ? "資料" : "章節")}${date ? ` · ${escapeHtml(date)}` : ""}</span>
      </a>`;
    }).join("");
  }

  async function loadFavoriteList() {
    if (!platformEnabled()) {
      renderFavoriteList(readJson("favorites", []), "後端尚未啟用，這裡顯示本機收藏。");
      openFavoritesModal();
      return;
    }
    if (!currentSession?.user) {
      openAuthModal("查看雲端收藏需要登入。");
      return;
    }
    openFavoritesModal();
    renderFavoriteList([], "正在載入雲端收藏...");
    const { data, error } = await supabaseClient
      .from("user_favorites")
      .select("item_id,item_type,item_title,item_url,updated_at")
      .order("updated_at", { ascending: false })
      .limit(100);
    if (error) {
      renderFavoriteList([], `收藏載入失敗：${error.message}`);
      return;
    }
    renderFavoriteList(data || [], data?.length ? "" : "雲端帳號目前還沒有收藏。");
  }

  function updateAuthUi() {
    const signedIn = Boolean(currentSession?.user);
    document.querySelectorAll(".auth-open").forEach((button) => {
      button.hidden = signedIn;
      button.textContent = signedIn ? currentSession.user.email : "登入";
    });
    document.querySelectorAll(".auth-signout").forEach((button) => {
      button.hidden = !signedIn;
    });
    document.body.dataset.platform = platformEnabled() ? "enabled" : "disabled";
    document.body.dataset.auth = signedIn ? "signed-in" : "signed-out";
  }

  async function initPlatform() {
    if (!platformEnabled()) {
      updateAuthUi();
      return;
    }
    supabaseClient = window.supabase.createClient(config.supabaseUrl, config.supabaseAnonKey);
    const { data } = await supabaseClient.auth.getSession();
    currentSession = data.session;
    updateAuthUi();

    supabaseClient.auth.onAuthStateChange((_event, session) => {
      currentSession = session;
      updateAuthUi();
      loadComments();
    });
  }

  function initAuthUi() {
    document.querySelectorAll(".auth-open").forEach((button) => {
      button.addEventListener("click", () => {
        if (!platformEnabled()) {
          toast("會員系統尚未配置 Supabase。請先填寫 assets/platform-config.js 並部署後端。");
          return;
        }
        openAuthModal("");
      });
    });
    document.querySelectorAll(".auth-signout").forEach((button) => {
      button.addEventListener("click", async () => {
        if (supabaseClient) await supabaseClient.auth.signOut();
        currentSession = null;
        updateAuthUi();
        toast("已登出。");
      });
    });
    document.querySelectorAll(".auth-close").forEach((button) => button.addEventListener("click", closeAuthModal));
    document.getElementById("auth-modal")?.addEventListener("click", (event) => {
      if (event.target?.id === "auth-modal") closeAuthModal();
    });
    document.querySelectorAll(".favorite-list-open").forEach((button) => {
      button.addEventListener("click", loadFavoriteList);
    });
    document.querySelectorAll(".favorites-close").forEach((button) => button.addEventListener("click", closeFavoritesModal));
    document.getElementById("favorites-modal")?.addEventListener("click", (event) => {
      if (event.target?.id === "favorites-modal") closeFavoritesModal();
    });
    document.querySelector(".auth-form")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!supabaseClient) {
        setAuthStatus("會員系統尚未啟用。");
        return;
      }
      const email = new FormData(event.currentTarget).get("email");
      setAuthStatus("正在寄出登入連結...");
      const { error } = await supabaseClient.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: window.location.href },
      });
      setAuthStatus(error ? `寄送失敗：${error.message}` : "登入連結已寄出，請到 Email 信箱確認。");
    });
  }

  async function saveCloudFavorite(item) {
    const user = currentSession?.user;
    if (!supabaseClient || !user) return { needsAuth: true };
    const payload = {
      user_id: user.id,
      item_id: item.id,
      item_type: item.type || "chapter",
      item_title: item.title,
      item_url: item.href || item.path || "",
      updated_at: new Date().toISOString(),
    };
    const { error } = await supabaseClient
      .from("user_favorites")
      .upsert(payload, { onConflict: "user_id,item_id" });
    return { error };
  }

  function saveLocalFavorite(item) {
    const list = readJson("favorites", []).filter((entry) => entry.id !== item.id);
    list.unshift({ ...item, savedAt: new Date().toISOString() });
    writeJson("favorites", list.slice(0, 80));
  }

  function initFavorites() {
    document.querySelectorAll(".local-favorite").forEach((button) => {
      button.addEventListener("click", async () => {
        const item = {
          id: button.dataset.favoriteId || location.pathname,
          type: button.dataset.favoriteType || "chapter",
          title: button.dataset.favoriteTitle || getCurrentTitle(),
          path: location.pathname,
          href: button.dataset.favoriteUrl || currentRelativeHref(),
        };
        if (!platformEnabled()) {
          saveLocalFavorite(item);
          button.textContent = "已本機收藏";
          toast("後端尚未啟用，已暫存到本機收藏。");
          return;
        }
        if (!currentSession?.user) {
          openAuthModal("收藏需要登入。登入後會保存到雲端帳號。");
          return;
        }
        const result = await saveCloudFavorite(item);
        if (result.error) {
          toast(`收藏失敗：${result.error.message}`);
          return;
        }
        button.textContent = "已收藏";
        toast("已保存到雲端收藏。");
      });
    });
  }

  async function handleDownload(button) {
    const bookId = button.dataset.downloadBookId || config.bookId || "wuxing-theory-book3";
    const format = button.dataset.downloadFormat || "docx";
    if (!platformEnabled()) {
      toast("會員下載尚未啟用：請先配置 Supabase、私有 Storage 與下載 Edge Function。");
      return;
    }
    if (!currentSession?.access_token) {
      openAuthModal("下載需要登入。登入後系統會生成短期下載連結。");
      return;
    }
    button.disabled = true;
    const originalText = button.textContent;
    button.textContent = "正在生成連結...";
    try {
      const response = await fetch(getDownloadFunctionUrl(), {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${currentSession.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ bookId, format }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.signedUrl) {
        throw new Error(data.error || "下載連結生成失敗");
      }
      window.open(data.signedUrl, "_blank", "noopener,noreferrer");
      toast("下載連結已生成，請在新視窗下載。");
    } catch (error) {
      toast(`下載失敗：${error.message}`);
    } finally {
      button.disabled = false;
      button.textContent = originalText;
    }
  }

  function initGatedActions() {
    document.querySelectorAll(".gated-action").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.downloadFormat) {
          handleDownload(button);
          return;
        }
        if (!platformEnabled()) {
          toast("此功能需要先配置 Supabase 後端。");
          return;
        }
        if (!currentSession?.user) {
          openAuthModal(`${button.dataset.actionName || "此功能"} 需要登入。`);
          return;
        }
        toast("你已登入，此功能後端已準備接入。");
      });
    });
  }

  function renderComments(container, comments) {
    const list = container.querySelector("[data-comment-list]");
    if (!list) return;
    if (!comments.length) {
      list.innerHTML = '<p class="comment-empty">目前還沒有公開評論。</p>';
      return;
    }
    list.innerHTML = comments.map((comment) => `
      <article class="comment-item">
        <strong>${escapeHtml(comment.visitor_name || "匿名讀者")}</strong>
        <time>${escapeHtml(new Date(comment.created_at).toLocaleDateString("zh-Hant"))}</time>
        <p>${escapeHtml(comment.body)}</p>
      </article>
    `).join("");
  }

  async function loadComments() {
    const container = document.querySelector(".reader-comments");
    if (!container) return;
    const status = container.querySelector(".comment-status");
    if (!platformEnabled() || !supabaseClient) {
      if (status) status.textContent = "評論後端尚未啟用；請配置 Supabase 後開放讀者評論。";
      return;
    }
    const { data, error } = await supabaseClient
      .from("book_comments")
      .select("id,visitor_name,body,created_at")
      .eq("book_id", container.dataset.bookId)
      .eq("chapter_path", container.dataset.chapterPath)
      .eq("status", "approved")
      .order("created_at", { ascending: false })
      .limit(30);
    if (status) status.textContent = error ? `評論載入失敗：${error.message}` : "";
    if (!error) renderComments(container, data || []);
  }

  function initComments() {
    const container = document.querySelector(".reader-comments");
    if (!container) return;
    loadComments();
    const form = container.querySelector(".comment-form");
    const status = container.querySelector(".comment-status");
    form?.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!platformEnabled() || !supabaseClient) {
        if (status) status.textContent = "評論後端尚未啟用。";
        return;
      }
      const formData = new FormData(form);
      const body = String(formData.get("body") || "").trim();
      const visitorName = String(formData.get("visitor_name") || "匿名讀者").trim();
      if (body.length < 2) {
        if (status) status.textContent = "評論內容太短。";
        return;
      }
      if (status) status.textContent = "正在送出評論...";
      const { error } = await supabaseClient.from("book_comments").insert({
        book_id: container.dataset.bookId,
        chapter_path: container.dataset.chapterPath,
        chapter_title: container.dataset.chapterTitle,
        visitor_name: visitorName.slice(0, 80),
        body: body.slice(0, 2000),
        status: "pending",
        user_id: currentSession?.user?.id || null,
      });
      if (status) {
        status.textContent = error
          ? `評論送出失敗：${error.message}`
          : "評論已送出，等待審核後公開。";
      }
      if (!error) form.reset();
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    initSearch();
    initReaderSettings();
    initProgress();
    initLastReadLink();
    initAuthUi();
    await initPlatform();
    initFavorites();
    initGatedActions();
    initComments();
  });
})();
