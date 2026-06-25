let currentLang = {};
let currentCategory = "all";

const $ = (id) => document.getElementById(id);

function escapeHtml(text) {
    return String(text ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function setMessage(id, text, type = "ok") {
    const el = $(id);
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
    setTimeout(() => { el.textContent = ""; }, 3500);
}

function scrollToSection(id) {
    const el = $(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
}

async function changeLang(lang) {
    try {
        const res = await fetch(`/lang/${lang}.json`);
        currentLang = await res.json();

        document.querySelectorAll("[data-key]").forEach(el => {
            const key = el.getAttribute("data-key");
            el.innerText = currentLang[key] || key;
        });

        document.querySelectorAll("[data-placeholder]").forEach(el => {
            const key = el.getAttribute("data-placeholder");
            el.placeholder = currentLang[key] || key;
        });

        document.documentElement.lang = lang;
        localStorage.setItem("lang", lang);
        await Promise.all([loadServers(), loadPosts()]);
    } catch (err) {
        console.error("Language load failed", err);
    }
}

async function addServer() {
    const name = $("serverName").value.trim();
    const ip = $("serverIp").value.trim();

    if (!name || !ip) {
        setMessage("serverMessage", currentLang.required_server || "서버 이름과 IP는 필수입니다.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("ip", ip);
    formData.append("country", $("serverCountry").value || "KR");
    formData.append("mode", $("serverMode").value);
    formData.append("discord", $("serverDiscord").value);
    formData.append("description", $("serverDescription").value);
    formData.append("loot_rate", $("lootRate").value);
    formData.append("zombie_rate", $("zombieRate").value);
    formData.append("vehicle_rate", $("vehicleRate").value);
    formData.append("max_players", $("maxPlayers").value);

    const file = $("settingsFile").files[0];
    if (file) formData.append("settings_file", file);

    const res = await fetch("/api/servers", { method: "POST", body: formData });
    if (!res.ok) {
        setMessage("serverMessage", "서버 등록 실패", "error");
        return;
    }

    ["serverName", "serverIp", "serverCountry", "serverDiscord", "serverDescription", "lootRate", "zombieRate", "vehicleRate", "maxPlayers"].forEach(id => $(id).value = "");
    $("settingsFile").value = "";
    setMessage("serverMessage", currentLang.saved || "저장 완료", "ok");
    await loadServers();
}

async function loadServers() {
    const query = encodeURIComponent($("serverSearch")?.value || "");
    const mode = encodeURIComponent($("modeFilter")?.value || "all");
    const res = await fetch(`/api/servers?q=${query}&mode=${mode}`);
    const servers = await res.json();
    const list = $("serverList");
    list.innerHTML = "";

    if (!servers.length) {
        list.innerHTML = `<p class="empty">${currentLang.no_servers || "등록된 서버가 없습니다."}</p>`;
        return;
    }

    servers.forEach(server => {
        const card = document.createElement("div");
        card.className = "server-card";
        card.innerHTML = `
            <div class="card-top">
                <span class="badge">${escapeHtml(server.country || "KR")}</span>
                <span class="badge pink">${escapeHtml(server.mode || "PvP")}</span>
            </div>
            <h3>${escapeHtml(server.name)}</h3>
            <p><b>IP</b> ${escapeHtml(server.ip)}</p>
            <p><b>Discord</b> ${escapeHtml(server.discord || "-")}</p>
            <p>${escapeHtml(server.description || "")}</p>
            <div class="tags">
                <span>Loot ${escapeHtml(server.loot_rate || "-")}</span>
                <span>Zombie ${escapeHtml(server.zombie_rate || "-")}</span>
                <span>Vehicle ${escapeHtml(server.vehicle_rate || "-")}</span>
                <span>Max ${escapeHtml(server.max_players || "-")}</span>
            </div>
            <div class="diagnosis">${escapeHtml(server.diagnosis || "")}</div>
            <div class="actions">
                <button onclick="likeServer(${server.id})">❤️ ${server.likes || 0}</button>
                <button class="danger" onclick="deleteServer(${server.id})">${currentLang.delete || "삭제"}</button>
            </div>
        `;
        list.appendChild(card);
    });
}

async function likeServer(id) {
    await fetch(`/api/servers/${id}/like`, { method: "POST" });
    await loadServers();
}

async function deleteServer(id) {
    if (!confirm(currentLang.confirm_delete || "삭제할까요?")) return;
    await fetch(`/api/servers/${id}`, { method: "DELETE" });
    await loadServers();
}

function setCategory(category) {
    currentCategory = category;
    loadPosts();
}

async function addPost() {
    const category = $("postCategory").value;
    const title = $("postTitle").value.trim();
    const author = $("postAuthor").value.trim();
    const content = $("postContent").value.trim();

    if (!title || !content) {
        setMessage("postMessage", currentLang.required_post || "제목과 내용은 필수입니다.", "error");
        return;
    }

    const res = await fetch("/api/posts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category, title, author, content })
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setMessage("postMessage", data.error || "게시글 등록 실패", "error");
        return;
    }

    $("postTitle").value = "";
    $("postAuthor").value = "";
    $("postContent").value = "";
    setMessage("postMessage", currentLang.saved || "저장 완료", "ok");
    await loadPosts();
}

async function loadPosts() {
    const query = encodeURIComponent($("postSearch")?.value || "");
    const res = await fetch(`/api/posts?category=${encodeURIComponent(currentCategory)}&q=${query}`);
    const posts = await res.json();
    const list = $("postList");
    list.innerHTML = "";

    if (!posts.length) {
        list.innerHTML = `<p class="empty">${currentLang.no_posts || "게시글이 없습니다."}</p>`;
        return;
    }

    posts.forEach(post => {
        const card = document.createElement("div");
        card.className = "post-card";
        card.innerHTML = `
            <div class="post-head" onclick="openPost(${post.id})">
                <span class="badge">${escapeHtml(post.category || "free")}</span>
                <h3>${escapeHtml(post.title)}</h3>
            </div>
            <p class="meta">${escapeHtml(post.author || "Anonymous")} · 👁 ${post.views || 0} · ❤️ ${post.likes || 0} · ${escapeHtml(post.created_at || "")}</p>
            <p>${escapeHtml(post.content || "").slice(0, 130)}</p>
            <div class="actions">
                <button onclick="likePost(${post.id})">❤️ LIKE</button>
                <button onclick="openPost(${post.id})">OPEN</button>
                <button class="danger" onclick="deletePost(${post.id})">${currentLang.delete || "삭제"}</button>
            </div>
        `;
        list.appendChild(card);
    });
}

async function openPost(id) {
    const res = await fetch(`/api/posts/${id}`);
    if (!res.ok) return;
    const data = await res.json();
    const post = data.post;
    const comments = data.comments || [];

    const detail = $("postDetail");
    detail.innerHTML = `
        <div class="detail-card">
            <span class="badge pink">${escapeHtml(post.category)}</span>
            <h2>${escapeHtml(post.title)}</h2>
            <p class="meta">${escapeHtml(post.author || "Anonymous")} · 👁 ${post.views || 0} · ❤️ ${post.likes || 0} · ${escapeHtml(post.created_at || "")}</p>
            <p class="detail-content">${escapeHtml(post.content)}</p>

            <h3>💬 Comments</h3>
            <input id="commentAuthor" placeholder="작성자">
            <textarea id="commentContent" placeholder="댓글 내용"></textarea>
            <button class="neon-btn" onclick="addComment(${post.id})">댓글 등록</button>

            <div class="comments">
                ${comments.length ? comments.map(comment => `
                    <div class="comment-card">
                        <p class="meta"><b>${escapeHtml(comment.author || "Anonymous")}</b> · ${escapeHtml(comment.created_at || "")}</p>
                        <p>${escapeHtml(comment.content)}</p>
                        <button class="danger small" onclick="deleteComment(${comment.id}, ${post.id})">${currentLang.delete || "삭제"}</button>
                    </div>
                `).join("") : `<p class="empty">댓글이 없습니다.</p>`}
            </div>
        </div>
    `;
    await loadPosts();
}

async function likePost(id) {
    await fetch(`/api/posts/${id}/like`, { method: "POST" });
    await loadPosts();
}

async function addComment(postId) {
    const author = $("commentAuthor").value.trim();
    const content = $("commentContent").value.trim();
    if (!content) return;

    const res = await fetch(`/api/posts/${postId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ author, content })
    });
    if (res.ok) await openPost(postId);
}

async function deletePost(id) {
    if (!confirm(currentLang.confirm_delete || "삭제할까요?")) return;
    await fetch(`/api/posts/${id}`, { method: "DELETE" });
    $("postDetail").innerHTML = "";
    await loadPosts();
}

async function deleteComment(commentId, postId) {
    if (!confirm(currentLang.confirm_delete || "삭제할까요?")) return;
    await fetch(`/api/comments/${commentId}`, { method: "DELETE" });
    await openPost(postId);
}

window.addEventListener("DOMContentLoaded", () => {
    changeLang(localStorage.getItem("lang") || "ko");
});
