(function () {
  const STORAGE_PREFIX = "wuxing-reader:";
  const base = document.body?.dataset?.base || "";
  const pageLang = document.body?.dataset?.lang || "zh-Hant";
  const isEnglishPage = pageLang === "en";
  const config = window.WUXING_PLATFORM_CONFIG || {};
  let supabaseClient = null;
  let currentSession = null;
  const UI = {
    zh: {
      searchLoadFail: "搜尋索引暫時無法載入。",
      searchEmpty: "沒有找到相關章節。",
      searchHint: "換一個更短或更核心的關鍵詞試試。",
      noFavorites: "目前還沒有收藏。",
      favoriteLocalMode: "後端尚未啟用，這裡顯示本機收藏。",
      favoriteNeedLogin: "查看雲端收藏需要登入。",
      favoriteLoading: "正在載入雲端收藏...",
      favoriteEmptyCloud: "雲端帳號目前還沒有收藏。",
      book: "書籍",
      resource: "資料",
      chapter: "章節",
      signIn: "登入",
      platformNotReady: "會員系統尚未配置 Supabase。請先填寫 assets/platform-config.js 並部署後端。",
      signedOut: "已登出。",
      authNotReady: "會員系統尚未啟用。",
      sendingLink: "正在寄出登入連結...",
      linkSent: "登入連結已寄出，請到 Email 信箱確認。",
      favoriteSavedLocal: "後端尚未啟用，已暫存到本機收藏。",
      favoriteNeedsLogin: "收藏需要登入。登入後會保存到雲端帳號。",
      savedCloud: "已保存到雲端收藏。",
      savedLocalButton: "已本機收藏",
      savedButton: "已收藏",
      downloadNotReady: "會員下載尚未啟用：請先配置 Supabase、私有 Storage 與下載 Edge Function。",
      downloadNeedsLogin: "下載需要登入。登入後系統會生成短期下載連結。",
      generatingLink: "正在生成連結...",
      downloadReady: "下載連結已生成，請在新視窗下載。",
      featureNeedsBackend: "此功能需要先配置 Supabase 後端。",
      signedInFeatureReady: "你已登入，此功能後端已準備接入。",
      commentsDisabled: "評論後端尚未啟用；請配置 Supabase 後開放讀者評論。",
      commentEmpty: "目前還沒有公開評論。",
      anonymous: "匿名讀者",
      commentBackendDisabled: "評論後端尚未啟用。",
      commentTooShort: "評論內容太短。",
      commentSending: "正在送出評論...",
      commentSent: "評論已送出，等待審核後公開。",
    },
    en: {
      searchLoadFail: "Search index is temporarily unavailable.",
      searchEmpty: "No matching chapter found.",
      searchHint: "Try a shorter or more central keyword.",
      noFavorites: "No favorites yet.",
      favoriteLocalMode: "Backend is not enabled. Local browser favorites are shown here.",
      favoriteNeedLogin: "Sign in to view cloud favorites.",
      favoriteLoading: "Loading cloud favorites...",
      favoriteEmptyCloud: "This account has no cloud favorites yet.",
      book: "Book",
      resource: "Resource",
      chapter: "Chapter",
      signIn: "Sign in",
      platformNotReady: "Member access is not configured yet. Please enable Supabase and deploy the backend.",
      signedOut: "Signed out.",
      authNotReady: "Member access is not enabled yet.",
      sendingLink: "Sending sign-in link...",
      linkSent: "Sign-in link sent. Please check your email.",
      favoriteSavedLocal: "Backend is not enabled. Saved to local browser favorites.",
      favoriteNeedsLogin: "Sign in to save this favorite to your cloud account.",
      savedCloud: "Saved to cloud favorites.",
      savedLocalButton: "Saved locally",
      savedButton: "Saved",
      downloadNotReady: "Member downloads are not enabled yet. Supabase, private storage, and the download function must be configured first.",
      downloadNeedsLogin: "Sign in to generate a short-lived download link.",
      generatingLink: "Generating link...",
      downloadReady: "Download link generated. Please download in the new window.",
      featureNeedsBackend: "This feature requires the Supabase backend.",
      signedInFeatureReady: "You are signed in. This backend feature is ready to connect.",
      commentsDisabled: "Comment backend is not enabled yet.",
      commentEmpty: "No public comments yet.",
      anonymous: "Anonymous reader",
      commentBackendDisabled: "Comment backend is not enabled yet.",
      commentTooShort: "Comment is too short.",
      commentSending: "Submitting comment...",
      commentSent: "Comment submitted. It will appear after review.",
    },
  };
  const T = UI[isEnglishPage ? "en" : "zh"];

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

  function initLanguageLinks() {
    document.querySelectorAll("[data-lang-choice]").forEach((link) => {
      link.addEventListener("click", () => {
        try {
          localStorage.setItem(STORAGE_PREFIX + "langChoice", link.dataset.langChoice || "");
        } catch {
          // Ignore local storage failures; navigation still works.
        }
      });
    });
  }

  function rootHomePath() {
    const path = location.pathname;
    return /\/wuxing-theory-book3\/?$/.test(path) || /\/wuxing-theory-book3\/index\.html$/.test(path);
  }

  function browserLanguageGuess() {
    const langs = navigator.languages?.length ? navigator.languages : [navigator.language || ""];
    return langs.some((item) => /^zh/i.test(item)) ? "zh" : "en";
  }

  async function geoLanguageGuess() {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 1200);
    try {
      const response = await fetch("https://ipapi.co/json/", { signal: controller.signal });
      const data = await response.json();
      const country = String(data.country_code || "").toUpperCase();
      if (["CN", "TW", "HK", "MO"].includes(country)) return "zh";
      if (country) return "en";
    } catch {
      // IP lookup is best effort only. Fall back to browser language.
    } finally {
      window.clearTimeout(timer);
    }
    return browserLanguageGuess();
  }

  async function initLanguageAutoSwitch() {
    if (!rootHomePath()) return;
    let stored = "";
    try {
      stored = localStorage.getItem(STORAGE_PREFIX + "langChoice") || "";
    } catch {
      stored = "";
    }
    if (stored) {
      if (stored === "en" && !isEnglishPage) location.replace("en/index.html");
      return;
    }
    const guess = await geoLanguageGuess();
    if (guess === "en" && !isEnglishPage) {
      location.replace("en/index.html");
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
      results.innerHTML = `<p class="search-result"><strong>${escapeHtml(T.searchLoadFail)}</strong></p>`;
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
        results.innerHTML = `<p class="search-result"><strong>${escapeHtml(T.searchEmpty)}</strong><span>${escapeHtml(T.searchHint)}</span></p>`;
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
          toast(isEnglishPage ? "No local reading position has been saved for this chapter yet." : "這一章還沒有本機閱讀記錄。");
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
      list.innerHTML = `<p class="comment-empty">${escapeHtml(T.noFavorites)}</p>`;
      return;
    }
    list.innerHTML = items.map((item) => {
      const title = item.item_title || item.title || (isEnglishPage ? "Untitled favorite" : "未命名收藏");
      const type = item.item_type || item.type || "chapter";
      const href = item.item_url || item.href || item.path || "";
      const updated = item.updated_at || item.savedAt || "";
      const date = updated ? new Date(updated).toLocaleDateString(isEnglishPage ? "en" : "zh-Hant") : "";
      return `<a class="favorite-item" href="${escapeHtml(resolveRelativeLink(href))}">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(type === "book" ? T.book : type === "resource" ? T.resource : T.chapter)}${date ? ` · ${escapeHtml(date)}` : ""}</span>
      </a>`;
    }).join("");
  }

  async function loadFavoriteList() {
    if (!platformEnabled()) {
      renderFavoriteList(readJson("favorites", []), T.favoriteLocalMode);
      openFavoritesModal();
      return;
    }
    if (!currentSession?.user) {
      openAuthModal(T.favoriteNeedLogin);
      return;
    }
    openFavoritesModal();
    renderFavoriteList([], T.favoriteLoading);
    const { data, error } = await supabaseClient
      .from("user_favorites")
      .select("item_id,item_type,item_title,item_url,updated_at")
      .order("updated_at", { ascending: false })
      .limit(100);
    if (error) {
      renderFavoriteList([], `收藏載入失敗：${error.message}`);
      return;
    }
    renderFavoriteList(data || [], data?.length ? "" : T.favoriteEmptyCloud);
  }

  function updateAuthUi() {
    const signedIn = Boolean(currentSession?.user);
    document.querySelectorAll(".auth-open").forEach((button) => {
      button.hidden = signedIn;
      button.textContent = signedIn ? currentSession.user.email : T.signIn;
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
          toast(T.platformNotReady);
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
        toast(T.signedOut);
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
        setAuthStatus(T.authNotReady);
        return;
      }
      const email = new FormData(event.currentTarget).get("email");
      setAuthStatus(T.sendingLink);
      const { error } = await supabaseClient.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: window.location.href },
      });
      setAuthStatus(error ? `Failed: ${error.message}` : T.linkSent);
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
          button.textContent = T.savedLocalButton;
          toast(T.favoriteSavedLocal);
          return;
        }
        if (!currentSession?.user) {
          openAuthModal(T.favoriteNeedsLogin);
          return;
        }
        const result = await saveCloudFavorite(item);
        if (result.error) {
          toast(`收藏失敗：${result.error.message}`);
          return;
        }
        button.textContent = T.savedButton;
        toast(T.savedCloud);
      });
    });
  }

  async function handleDownload(button) {
    const bookId = button.dataset.downloadBookId || config.bookId || "wuxing-theory-book3";
    const format = button.dataset.downloadFormat || "docx";
    if (!platformEnabled()) {
      toast(T.downloadNotReady);
      return;
    }
    if (!currentSession?.access_token) {
      openAuthModal(T.downloadNeedsLogin);
      return;
    }
    button.disabled = true;
    const originalText = button.textContent;
    button.textContent = T.generatingLink;
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
      toast(T.downloadReady);
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
          toast(T.featureNeedsBackend);
          return;
        }
        if (!currentSession?.user) {
          const action = button.dataset.actionName || (isEnglishPage ? "This feature" : "此功能");
          openAuthModal(isEnglishPage ? `${action} requires sign-in.` : `${action} 需要登入。`);
          return;
        }
        toast(T.signedInFeatureReady);
      });
    });
  }

  function renderComments(container, comments) {
    const list = container.querySelector("[data-comment-list]");
    if (!list) return;
    if (!comments.length) {
      list.innerHTML = `<p class="comment-empty">${escapeHtml(T.commentEmpty)}</p>`;
      return;
    }
    list.innerHTML = comments.map((comment) => `
      <article class="comment-item">
        <strong>${escapeHtml(comment.visitor_name || T.anonymous)}</strong>
        <time>${escapeHtml(new Date(comment.created_at).toLocaleDateString(isEnglishPage ? "en" : "zh-Hant"))}</time>
        <p>${escapeHtml(comment.body)}</p>
      </article>
    `).join("");
  }

  async function loadComments() {
    const container = document.querySelector(".reader-comments");
    if (!container) return;
    const status = container.querySelector(".comment-status");
    if (!platformEnabled() || !supabaseClient) {
      if (status) status.textContent = T.commentsDisabled;
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
        if (status) status.textContent = T.commentBackendDisabled;
        return;
      }
      const formData = new FormData(form);
      const body = String(formData.get("body") || "").trim();
      const visitorName = String(formData.get("visitor_name") || "匿名讀者").trim();
      if (body.length < 2) {
        if (status) status.textContent = T.commentTooShort;
        return;
      }
      if (status) status.textContent = T.commentSending;
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
          : T.commentSent;
      }
      if (!error) form.reset();
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    initLanguageLinks();
    initLanguageAutoSwitch();
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
