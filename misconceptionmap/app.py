"""MisconceptionMap - university portal (Flask). Roles: student, faculty, admin.
Run:  pip install -r requirements.txt && python app.py   ->  http://127.0.0.1:5000
"""
import csv, hashlib, io, os, random, sqlite3, time
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, Response, abort, flash, g, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
import engine as E

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portal.db")
EPS = float(os.environ.get("DP_EPSILON", "1.0"))
SALT = os.environ.get("ANON_SALT", "mm-salt")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close(_):
    d = g.pop("db", None)
    if d:
        d.close()


def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, name TEXT, pw TEXT,
        role TEXT, reg_no TEXT, lang TEXT DEFAULT 'en', active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER, answer TEXT, mid TEXT,
        conf REAL, ts TEXT, synthetic INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts TEXT, actor TEXT, action TEXT);
    """)
    if not c.execute("SELECT 1 FROM users").fetchone():
        def add(u, n, p, r, reg=""):
            c.execute("INSERT INTO users(username,name,pw,role,reg_no) VALUES(?,?,?,?,?)",
                      (u, n, generate_password_hash(p), r, reg))
        add("admin", "System Administrator", "admin123", "admin", "ADM001")
        add("faculty", "Dr. Meera Nair", "faculty123", "faculty", "FAC101")
        add("lavanya", "Lavanya J", "student123", "student", "SCA25MCA110")
        for i in range(1, 13):
            add("student%d" % i, "Student %02d" % i, "student123", "student", "SCA25MCA%03d" % (200 + i))
        rnd = random.Random(7)
        weights = {"m1": 9, "m2": 5, "m3": 7, "m4": 6, "m5": 4, "m6": 3, "m7": 6, "m8": 2}
        ids = [r[0] for r in c.execute("SELECT id FROM users WHERE role='student'")]
        for uid in ids:
            for _ in range(rnd.randint(2, 4)):
                mid = rnd.choices(list(weights), list(weights.values()))[0]
                ts = (datetime.now() - timedelta(days=rnd.randint(0, 20))).strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO attempts(user_id,answer,mid,conf,ts,synthetic) VALUES(?,?,?,?,?,1)",
                          (uid, "(synthetic seed)", mid, round(rnd.uniform(.5, .95), 2), ts))
    c.commit(); c.close()


def log(action):
    db().execute("INSERT INTO audit(ts,actor,action) VALUES(?,?,?)",
                 (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session.get("username", "-"), action))
    db().commit()


# ---------- RBAC ----------
def login_required(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if "uid" not in session:
                return redirect(url_for("login", next=request.path))
            if roles and session["role"] not in roles:
                abort(403)
            return f(*a, **k)
        return w
    return deco


@app.context_processor
def inject():
    return dict(S=session, LANGS=E.LANGS, COURSE=E.DATA["course"])


@app.errorhandler(403)
def e403(_):
    return render_template("error.html", code=403, msg="Your role does not have access to this page."), 403


@app.errorhandler(404)
def e404(_):
    return render_template("error.html", code=404, msg="Page not found."), 404


def csrf_ok():
    t = request.form.get("_t") or request.headers.get("X-CSRF-Token")
    return bool(t) and t == session.get("_t")


@app.before_request
def csrf():
    session.setdefault("_t", hashlib.sha256(os.urandom(16)).hexdigest())
    if request.method == "POST" and not csrf_ok():
        abort(400)


app.jinja_env.globals["token"] = lambda: session.get("_t", "")


# ---------- Auth ----------
@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("dashboard") if "uid" in session else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM users WHERE username=? AND active=1",
                         (request.form["username"].strip(),)).fetchone()
        if u and check_password_hash(u["pw"], request.form["password"]):
            session.clear()
            session.update(uid=u["id"], username=u["username"], name=u["name"], role=u["role"],
                           reg=u["reg_no"], lang=u["lang"], _t=hashlib.sha256(os.urandom(16)).hexdigest())
            log("login")
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid username or password.", "err")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    log("logout"); session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required()
def dashboard():
    r = session["role"]
    if r == "faculty":
        return redirect(url_for("analytics"))
    if r == "admin":
        return redirect(url_for("admin"))
    rows = db().execute("SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 15", (session["uid"],)).fetchall()
    stats = {}
    for x in rows:
        if x["mid"]:
            stats[x["mid"]] = stats.get(x["mid"], 0) + 1
    focus = [(E.MIS[m], n) for m, n in sorted(stats.items(), key=lambda t: -t[1])[:3]]
    return render_template("dashboard.html", rows=rows, MIS=E.MIS, focus=focus, CONCEPTS=E.CONCEPTS)


# ---------- Student: Socratic tutor ----------
@app.route("/tutor", methods=["GET", "POST"])
@login_required("student")
def tutor():
    chat = session.get("chat", [])
    if request.method == "POST":
        lang = request.form.get("lang", "en")
        session["lang"] = lang
        ans = request.form.get("answer", "").strip()[:1000]
        today = datetime.now().strftime("%Y-%m-%d")
        n_today = db().execute("SELECT COUNT(*) FROM attempts WHERE user_id=? AND ts LIKE ?",
                               (session["uid"], today + "%")).fetchone()[0]
        if len(ans.split()) < 4:
            r = {"text": E.FRAMES[lang]["short"], "citations": [], "verifier": {"ok": True}, "root": None}
            mid, conf = None, 0
        else:
            mid, conf, _ = E.diagnose(ans)
            if mid:
                turn = sum(1 for c in chat if c.get("mid") == mid) + 1
                r = E.tutor_reply(mid, turn, lang, guard=n_today >= 10)
            else:
                r = E.fallback_reply(ans, lang)
            db().execute("INSERT INTO attempts(user_id,answer,mid,conf,ts) VALUES(?,?,?,?,?)",
                         (session["uid"], ans, mid, conf, datetime.now().strftime("%Y-%m-%d %H:%M")))
            db().commit()
        chat.append({"you": ans, "bot": r, "mid": mid, "conf": conf})
        session["chat"] = chat[-8:]
        return redirect(url_for("tutor"))
    return render_template("tutor.html", chat=chat)


@app.route("/tutor/reset", methods=["POST"])
@login_required("student")
def tutor_reset():
    session.pop("chat", None)
    return redirect(url_for("tutor"))


@app.route("/graph")
@login_required()
def graph():
    counts = {}
    for r in db().execute("SELECT mid, COUNT(DISTINCT user_id) n FROM attempts WHERE mid IS NOT NULL GROUP BY mid"):
        counts[r["mid"]] = r["n"]
    by_concept = {}
    for mid, n in counts.items():
        cid = E.MIS[mid]["concept"]
        by_concept[cid] = by_concept.get(cid, 0) + n
    heat = {c: (by_concept.get(c, 0) if session["role"] != "student" else 0) for c in E.CONCEPTS}
    return render_template("graph.html", concepts=E.DATA["concepts"], edges=E.DATA["edges"], heat=heat)


# ---------- Faculty ----------
@app.route("/analytics")
@login_required("faculty", "admin")
def analytics():
    total = db().execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    rows = db().execute("SELECT mid, COUNT(DISTINCT user_id) n FROM attempts WHERE mid IS NOT NULL GROUP BY mid").fetchall()
    out = []
    for r in rows:
        noisy = E.dp_count(r["n"], EPS)
        m = E.MIS[r["mid"]]
        out.append(dict(m=m, raw=r["n"], noisy=noisy,
                        pct=None if noisy is None else min(100, round(100 * noisy / total)),
                        root=E.CONCEPTS[m["root"]]["name"], rec=E.recommendation(r["mid"])))
    out.sort(key=lambda x: -(x["noisy"] or 0))
    unsure = db().execute("SELECT COUNT(*) FROM attempts WHERE mid IS NULL").fetchone()[0]
    return render_template("analytics.html", out=out, total=total, eps=EPS, unsure=unsure,
                           show_raw=session["role"] == "admin")


@app.route("/analytics/export.csv")
@login_required("faculty", "admin")
def export():
    s = io.StringIO(); w = csv.writer(s)
    w.writerow(["student_hash", "misconception", "concept", "root_cause", "confidence", "timestamp"])
    for r in db().execute("SELECT * FROM attempts WHERE mid IS NOT NULL ORDER BY id"):
        m = E.MIS[r["mid"]]
        h = hashlib.sha256((SALT + str(r["user_id"])).encode()).hexdigest()[:10]
        w.writerow([h, m["label"], E.CONCEPTS[m["concept"]]["name"], E.CONCEPTS[m["root"]]["name"], r["conf"], r["ts"]])
    log("export csv")
    return Response(s.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=misconceptions_anonymised.csv"})


@app.route("/materials", methods=["GET", "POST"])
@login_required("faculty", "admin")
def materials():
    if request.method == "POST":
        src, cid, text = request.form["src"].strip(), request.form["concept"], request.form["text"].strip()
        if src and text and cid in E.CONCEPTS:
            E.add_chunk(src, cid, text[:2000]); log("add material " + src); flash("Material indexed for retrieval.", "ok")
        return redirect(url_for("materials"))
    return render_template("materials.html", chunks=E.CHUNKS.values(), CONCEPTS=E.CONCEPTS)


# ---------- Admin ----------
@app.route("/admin", methods=["GET", "POST"])
@login_required("admin")
def admin():
    if request.method == "POST":
        f = request.form
        if f["do"] == "create":
            try:
                db().execute("INSERT INTO users(username,name,pw,role,reg_no) VALUES(?,?,?,?,?)",
                             (f["username"].strip(), f["name"].strip(), generate_password_hash(f["password"]),
                              f["role"] if f["role"] in ("student", "faculty", "admin") else "student", f["reg"].strip()))
                db().commit(); log("create user " + f["username"]); flash("User created.", "ok")
            except sqlite3.IntegrityError:
                flash("Username already exists.", "err")
        elif f["do"] == "toggle":
            db().execute("UPDATE users SET active=1-active WHERE id=? AND id<>?", (f["id"], session["uid"]))
            db().commit(); log("toggle user " + f["id"])
        return redirect(url_for("admin"))
    users = db().execute("SELECT * FROM users ORDER BY role, id").fetchall()
    audit = db().execute("SELECT * FROM audit ORDER BY id DESC LIMIT 12").fetchall()
    return render_template("admin.html", users=users, audit=audit)


@app.route("/api/diagnose", methods=["POST"])
@login_required("faculty", "admin")
def api_diag():
    d = request.get_json(silent=True) or {}
    mid, conf, rk = E.diagnose(d.get("answer", ""))
    return jsonify(misconception=mid, confidence=conf)


if __name__ == "__main__":
    init_db()
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
