from flask import Flask, render_template, request, jsonify, send_from_directory
from database import get_db, init_db, rows_to_dicts

app = Flask(__name__)
init_db()


def analyze_settings(text: str) -> str:
    lower = (text or "").lower()
    score = 0
    found = []

    checks = [
        ("zombie", 2, "좀비 설정 감지"),
        ("loot", 2, "루팅 설정 감지"),
        ("vehicle", 2, "차량 설정 감지"),
        ("maxplayers", 3, "최대 인원 설정 감지"),
        ("maxallowed", 3, "최대 제한 설정 감지"),
        ("spawn", 2, "스폰 설정 감지"),
        ("drone", 1, "드론/관리 설정 감지"),
        ("sentry", 2, "센트리 설정 감지"),
        ("animal", 1, "동물 설정 감지"),
    ]

    for key, point, label in checks:
        if key in lower:
            score += point
            found.append(label)

    if score <= 2:
        load = "낮음"
    elif score <= 6:
        load = "중간"
    else:
        load = "높음"

    if not found:
        return "설정파일 분석 결과: 주요 부하 설정 감지 없음"

    return f"예상 서버 부하: {load} / " + ", ".join(found)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.route("/lang/<path:filename>")
def lang(filename):
    return send_from_directory("lang", filename)


@app.route("/api/servers", methods=["GET"])
def get_servers():
    query = request.args.get("q", "").strip().lower()
    mode = request.args.get("mode", "all")

    conn = get_db()
    cur = conn.cursor()

    sql = "SELECT * FROM servers WHERE 1=1"
    params = []

    if query:
        sql += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(ip) LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if mode != "all":
        sql += " AND mode = ?"
        params.append(mode)

    sql += " ORDER BY id DESC"

    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


@app.route("/api/servers", methods=["POST"])
def add_server():
    data = request.form
    name = data.get("name", "").strip()
    ip = data.get("ip", "").strip()

    if not name or not ip:
        return jsonify({"success": False, "error": "name and ip required"}), 400

    diagnosis = "설정파일 없음"
    file = request.files.get("settings_file")
    if file and file.filename:
        content = file.read().decode("utf-8", errors="ignore")
        diagnosis = analyze_settings(content)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO servers
        (name, ip, country, mode, discord, description, loot_rate, zombie_rate, vehicle_rate, max_players, diagnosis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        ip,
        data.get("country", "KR"),
        data.get("mode", "PvP"),
        data.get("discord", ""),
        data.get("description", ""),
        data.get("loot_rate", ""),
        data.get("zombie_rate", ""),
        data.get("vehicle_rate", ""),
        data.get("max_players", ""),
        diagnosis,
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/servers/<int:server_id>/like", methods=["POST"])
def like_server(server_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE servers SET likes = likes + 1 WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/servers/<int:server_id>", methods=["DELETE"])
def delete_server(server_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/posts", methods=["GET"])
def get_posts():
    category = request.args.get("category", "all")
    query = request.args.get("q", "").strip().lower()

    conn = get_db()
    cur = conn.cursor()

    sql = "SELECT * FROM posts WHERE 1=1"
    params = []

    if category != "all":
        sql += " AND category = ?"
        params.append(category)

    if query:
        sql += " AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(author) LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    sql += " ORDER BY id DESC"

    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return jsonify(rows_to_dicts(rows))


@app.route("/api/posts", methods=["POST"])
def add_post():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title or not content:
        return jsonify({"success": False, "error": "title and content required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO posts (category, title, author, content)
        VALUES (?, ?, ?, ?)
    """, (
        data.get("category", "free"),
        title,
        data.get("author", "Anonymous") or "Anonymous",
        content,
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET views = views + 1 WHERE id = ?", (post_id,))
    post = cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    comments = cur.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY id ASC", (post_id,)).fetchall()
    conn.commit()
    conn.close()

    if not post:
        return jsonify({"success": False, "error": "post not found"}), 404

    return jsonify({"post": dict(post), "comments": rows_to_dicts(comments)})


@app.route("/api/posts/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/posts/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()

    if not content:
        return jsonify({"success": False, "error": "content required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO comments (post_id, author, content)
        VALUES (?, ?, ?)
    """, (
        post_id,
        data.get("author", "Anonymous") or "Anonymous",
        content,
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    cur.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
