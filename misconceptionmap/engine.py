"""MisconceptionMap core engine (offline, dependency-free).

Agents: Diagnoser -> Socratic Tutor -> Verifier, plus Curriculum Analyst helpers.
Retrieval: TF-IDF over course chunks (swap for FAISS/Chroma + embeddings in production).
"""
import json, math, os, random, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "data", "course.json"), encoding="utf-8"))
CONCEPTS = {c["id"]: c for c in DATA["concepts"]}
MIS = {m["id"]: m for m in DATA["misconceptions"]}
CHUNKS = {c["id"]: c for c in DATA["chunks"]}
STOP = set("the a an is are of to and in it that this be as for on with by or at from we you i can".split())


def norm(t):
    t = t.lower()
    for a, b in (("regularisation", "regularization"), ("minimise", "minimize"), ("optimise", "optimize"),
                 ("generalisation", "generalization"), ("memorise", "memorize")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def toks(t):
    return [w for w in norm(t).split() if w not in STOP]


# ---------- TF-IDF ----------
def _build():
    docs = {("c", k): toks(v["text"]) for k, v in CHUNKS.items()}
    docs.update({("m", k): toks(v["statement"] + " " + " ".join(v["phrases"])) for k, v in MIS.items()})
    df = Counter(w for d in docs.values() for w in set(d))
    n = len(docs)
    idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}
    return docs, idf


_DOCS, _IDF = _build()


def vec(tokens):
    tf = Counter(tokens)
    v = {w: c * _IDF.get(w, 1.0) for w, c in tf.items()}
    nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {w: x / nrm for w, x in v.items()}


def cos(a, b):
    return sum(x * b.get(w, 0.0) for w, x in a.items())


_CV = {k: vec(d) for (t, k), d in _DOCS.items() if t == "c"}
_MV = {k: vec(d) for (t, k), d in _DOCS.items() if t == "m"}
_extra = {}  # faculty-uploaded chunks


def add_chunk(src, concept, text):
    cid = "u%d" % (len(_extra) + 1)
    CHUNKS[cid] = {"id": cid, "src": src, "concept": concept, "text": text}
    _CV[cid] = vec(toks(text))
    _extra[cid] = True
    return cid


def retrieve(query, k=2):
    q = vec(toks(query))
    r = sorted(((cos(q, v), cid) for cid, v in _CV.items()), reverse=True)[:k]
    return [dict(CHUNKS[cid], score=round(s, 3)) for s, cid in r if s > 0.05]


# ---------- Diagnoser ----------
def _phrase_score(ans_n, ans_t, m):
    best = 0.0
    for p in m["phrases"]:
        pn = norm(p).strip()
        if pn in ans_n:
            return 1.0, True
        pt = [w for w in pn.split() if w not in STOP]
        if pt:
            frac = sum(w in ans_t for w in pt) / len(pt)
            if frac >= 0.85:
                best = max(best, 0.6)
    return best, False


def diagnose(answer, mode="hybrid", thr=None):
    """mode: keyword | tfidf | hybrid. Returns (misconception_id|None, confidence, ranking)."""
    an = " " + " ".join(norm(answer).split()) + " "
    at = set(an.split())
    av = vec(toks(answer))
    ranking = []
    for mid, m in MIS.items():
        ps, exact = _phrase_score(an, at, m)
        cs = cos(av, _MV[mid])
        if mode == "keyword":
            s = 1.0 if exact else 0.0
        elif mode == "tfidf":
            s = cs * 2
        else:
            s = ps + 2 * cs
        ranking.append((s, mid))
    ranking.sort(reverse=True)
    top, mid = ranking[0]
    conf = top / (top + 1.0)
    t = thr if thr is not None else {"keyword": 0.45, "tfidf": 0.33, "hybrid": 0.45}[mode]
    return (mid if conf >= t else None), round(conf, 3), ranking[:3]


# ---------- Tutor + Verifier ----------
FRAMES = {
    "en": {"ack": "I notice a common misconception here: {label}.", "hint": "Hint (source: {src}): ",
           "fallback": "I'm not sure what misconception this is, so I won't guess. Please review these course materials and restate your idea:",
           "short": "Please write your explanation in at least one full sentence so I can help.",
           "reveal": "Let's look at the course material together ({src}):", "own": "Now explain it back in your own words.",
           "guard": "You've asked for a lot of help today - try working the next one out on your own first."},
    "hi": {"ack": "आपके उत्तर में एक आम भ्रांति दिखती है: {label}।", "hint": "संकेत (स्रोत: {src}): ",
           "fallback": "मुझे यकीन नहीं है, इसलिए मैं अनुमान नहीं लगाऊँगा। कृपया ये पाठ्य-सामग्री देखें और फिर से समझाएँ:",
           "short": "कृपया अपना उत्तर कम से कम एक पूरे वाक्य में लिखें।",
           "reveal": "आइए पाठ्य-सामग्री साथ देखें ({src}):", "own": "अब इसे अपने शब्दों में समझाइए।",
           "guard": "आज आपने काफ़ी मदद ली है - अगला प्रश्न पहले ख़ुद हल करने की कोशिश करें।"},
    "ta": {"ack": "உங்கள் பதிலில் ஒரு பொதுவான தவறான புரிதல் தெரிகிறது: {label}.", "hint": "குறிப்பு (ஆதாரம்: {src}): ",
           "fallback": "எனக்கு உறுதியாகத் தெரியவில்லை, அதனால் ஊகிக்க மாட்டேன். இந்தப் பாடப்பொருளைப் பார்த்து மீண்டும் விளக்கவும்:",
           "short": "உங்கள் பதிலை குறைந்தது ஒரு முழு வாக்கியத்தில் எழுதவும்.",
           "reveal": "பாடப்பொருளை சேர்ந்து பார்ப்போம் ({src}):", "own": "இப்போது அதை உங்கள் சொந்த வார்த்தைகளில் விளக்குங்கள்.",
           "guard": "இன்று நிறைய உதவி கேட்டுள்ளீர்கள் - அடுத்ததை முதலில் நீங்களே முயற்சிக்கவும்."},
}
LANGS = {"en": "English", "hi": "हिन्दी", "ta": "தமிழ்"}


def verify(text, mid, turn, chunks):
    """Verifier agent: grounded (has citation) and leak-free before the guided reveal."""
    leak = turn < 3 and MIS[mid]["correct"] in text.lower() if mid else False
    return {"grounded": bool(chunks), "leak_free": not leak, "ok": bool(chunks) and not leak}


def tutor_reply(mid, turn, lang="en", guard=False):
    f = FRAMES.get(lang, FRAMES["en"])
    m = MIS[mid]
    ch = CHUNKS[m["chunk"]]
    q = m["questions"][min(turn - 1, len(m["questions"]) - 1)]
    parts = []
    if turn == 1:
        parts.append(f["ack"].format(label=m["label"]))
    parts.append(f["hint"].format(src=ch["src"]) + m["hint"].format(src=ch["src"]) if turn == 1 else "")
    parts.append(q)
    body = [p for p in parts if p]
    if turn >= 3:
        body = [f["reveal"].format(src=ch["src"]), '"' + ch["text"] + '"', f["own"]]
    if guard:
        body.append(f["guard"])
    text = "\n".join(body)
    v = verify("\n".join(body[:-1] if guard else body), mid, turn, [ch])
    return {"text": text, "citations": [{"src": ch["src"], "id": ch["id"]}], "verifier": v,
            "root": CONCEPTS[m["root"]]["name"]}


def fallback_reply(answer, lang="en"):
    f = FRAMES.get(lang, FRAMES["en"])
    ch = retrieve(answer, 2)
    return {"text": f["fallback"], "citations": [{"src": c["src"], "id": c["id"]} for c in ch],
            "verifier": {"grounded": bool(ch), "leak_free": True, "ok": True}, "root": None}


# ---------- Privacy ----------
def laplace(scale):
    u = random.random() - 0.5
    return -scale * (1 if u >= 0 else -1) * math.log(1 - 2 * abs(u) + 1e-12)


def dp_count(raw, eps=1.0, k=3):
    """k-anonymity suppression + epsilon-DP Laplace noise (sensitivity 1)."""
    if raw < k:
        return None
    return max(0, round(raw + laplace(1.0 / eps)))


def recommendation(mid):
    m = MIS[mid]
    root = CONCEPTS[m["root"]]
    return "Revisit %s (%s) and add a worked example contrasting the correct idea with: \"%s\"." % (
        root["name"], root["lecture"], m["label"])
