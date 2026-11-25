"""Builds synopsis.pdf, research_paper.pdf, project_report.pdf  (python docs/build_docs.py)"""
import json, os
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether)

HERE = os.path.dirname(os.path.abspath(__file__))
RES = json.load(open(os.path.join(HERE, "..", "eval", "results.json")))
NAVY = colors.HexColor("#0f2a4a")
NAME, REG = "Lavanya J", "SCA25MCA110"
TITLE = "MisconceptionMap: A Multi-Agent Generative AI System for Diagnosing Student Misconceptions and Auditing Course Design"
ss = getSampleStyleSheet()
B = ParagraphStyle("B", parent=ss["Normal"], fontName="Times-Roman", fontSize=11, leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15, textColor=NAVY, spaceBefore=10, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=NAVY, spaceBefore=8, spaceAfter=4)
CT = ParagraphStyle("CT", parent=B, alignment=TA_CENTER)
TT = ParagraphStyle("TT", parent=CT, fontName="Helvetica-Bold", fontSize=19, leading=24, textColor=NAVY)
BL = ParagraphStyle("BL", parent=B, leftIndent=16, bulletIndent=4, spaceAfter=3)
SM = ParagraphStyle("SM", parent=B, fontSize=9.5, leading=12, alignment=0)
CAP = ParagraphStyle("CAP", parent=SM, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))


def P(t, s=B): return Paragraph(t, s)
def bullets(items): return [Paragraph(i, BL, bulletText="•") for i in items]


def table(rows, widths=None, head=True):
    t = Table([[Paragraph(str(c), SM) for c in r] for r in rows], colWidths=widths, repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#94a3b8")), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    if head: st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")))
    t.setStyle(TableStyle(st)); return t


def arch():
    d = Drawing(440, 215)
    def box(x, y, w, h, txt, fill="#e0e7ff"):
        d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=colors.HexColor(fill), strokeColor=NAVY))
        for i, line in enumerate(txt.split("\n")):
            d.add(String(x + w / 2, y + h / 2 + 4 - i * 11 + (len(txt.split("\n")) - 1) * 5, line, fontSize=8, textAnchor="middle"))
    def arr(x1, y1, x2, y2): d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#64748b")))
    box(5, 160, 100, 40, "Slides / PDFs /\nTranscripts (Whisper)", "#fef9c3")
    box(170, 160, 100, 40, "Chunker + Index\n(TF-IDF / FAISS)")
    box(335, 160, 100, 40, "Concept Graph\n(Neo4j / JSON)")
    box(5, 85, 100, 40, "Student answer", "#dcfce7")
    box(170, 85, 100, 40, "Diagnoser agent\n(rules + LoRA)", "#fce7f3")
    box(335, 85, 100, 40, "Socratic Tutor\nagent")
    box(335, 20, 100, 40, "Verifier agent\n(grounding, leakage)", "#fee2e2")
    box(170, 20, 100, 40, "Curriculum Analyst\n(DP aggregates)", "#fce7f3")
    box(5, 20, 100, 40, "Faculty dashboard\n+ course fixes", "#dcfce7")
    arr(105, 180, 170, 180); arr(270, 180, 335, 180); arr(105, 105, 170, 105); arr(270, 105, 335, 105)
    arr(385, 160, 385, 125); arr(385, 85, 385, 60); arr(220, 160, 220, 125); arr(220, 85, 220, 60); arr(170, 40, 105, 40)
    return d


def chart():
    d = Drawing(400, 170)
    c = VerticalBarChart(); c.x, c.y, c.width, c.height = 40, 30, 330, 110
    c.data = [[r["precision"] for r in RES], [r["recall"] for r in RES], [r["f1"] for r in RES]]
    c.categoryAxis.categoryNames = ["Keyword", "TF-IDF", "Hybrid"]
    c.valueAxis.valueMin, c.valueAxis.valueMax, c.valueAxis.valueStep = 0.5, 1.0, 0.1
    for i, col in enumerate(["#94a3b8", "#60a5fa", "#7f1d1d"]): c.bars[i].fillColor = colors.HexColor(col)
    d.add(c)
    for i, (n, col) in enumerate([("Precision", "#94a3b8"), ("Recall", "#60a5fa"), ("F1", "#7f1d1d")]):
        d.add(Rect(120 + i * 70, 152, 8, 8, fillColor=colors.HexColor(col), strokeColor=None)); d.add(String(132 + i * 70, 152, n, fontSize=8))
    return d


def results_table():
    rows = [["Diagnoser", "Precision", "Recall", "F1", "Accuracy (incl. no-misconception)"]]
    names = {"keyword": "Keyword/phrase only", "tfidf": "TF-IDF similarity only", "hybrid": "Hybrid (proposed)"}
    for r in RES: rows.append([names[r["mode"]], r["precision"], r["recall"], r["f1"], r["accuracy"]])
    return table(rows, [4.6 * cm, 2.2 * cm, 2.2 * cm, 2 * cm, 5 * cm])


def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
    c.drawString(2 * cm, 1.1 * cm, "MisconceptionMap | %s (%s) | RTD Open Elective" % (NAME, REG))
    c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, "Page %d" % d.page); c.restoreState()


def build(fn, story):
    SimpleDocTemplate(os.path.join(HERE, fn), pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                      title=TITLE, author="%s (%s)" % (NAME, REG)).build(story, onFirstPage=footer, onLaterPages=footer)


def cover(kind):
    return [Spacer(1, 3 * cm), P("RTD OPEN ELECTIVE", CT), Spacer(1, .6 * cm), P(kind, ParagraphStyle("k", parent=CT, fontName="Helvetica-Bold", fontSize=14)),
            Spacer(1, 1 * cm), P(TITLE, TT), Spacer(1, 1.5 * cm), P("Submitted by", CT),
            P("<b>%s</b><br/>Register No.: <b>%s</b><br/>Master of Computer Applications (MCA)" % (NAME, REG), CT), Spacer(1, 1 * cm),
            P("Guide / Faculty: ______________________ &nbsp;&nbsp; Date: ____________", CT), PageBreak()]


# ====================== SYNOPSIS ======================
def synopsis():
    s = cover("PROJECT SYNOPSIS")
    s += [P("1. Introduction", H1), P(
        "Universities increasingly deploy generative AI as question-answering chatbots. These tools tell a student <i>what</i> the answer is but do not diagnose <i>why</i> the student is wrong, "
        "and they give faculty no insight into which parts of a course are failing. MisconceptionMap reverses this: it reads course material and student explanations, builds a graph of concepts and "
        "prerequisites, detects specific misconceptions, tutors the student Socratically, and reports root causes to faculty."),
        P("2. Problem Statement", H1), P(
        "Existing educational LLM tools (a) leak answers and reduce learning effort, (b) hallucinate beyond course content, (c) ignore the prerequisite structure of knowledge, "
        "(d) expose student data, and (e) give instructors no actionable analytics. There is a need for a grounded, privacy-preserving system that audits teaching as well as learning."),
        P("3. Objectives", H1)]
    s += bullets(["Build a multimodal retrieval pipeline over slides, PDFs and lecture transcripts with citations for every tutor claim.",
                  "Construct a concept and prerequisite graph and map each misconception to a root-cause concept.",
                  "Design a multi-agent system: Diagnoser, Socratic Tutor, Verifier and Curriculum Analyst.",
                  "Compare rule/TF-IDF, prompted-LLM and LoRA fine-tuned classifiers for misconception detection.",
                  "Provide a role-based university portal for students, faculty and administrators.",
                  "Protect privacy with anonymisation, k-suppression and differential privacy; evaluate fairness and over-reliance."])
    s += [P("4. Proposed System and Methodology", H1), P(
        "Course content is chunked and indexed (TF-IDF in the prototype; FAISS/Chroma embeddings in the full design). A knowledge graph stores concepts, prerequisite edges and a catalogue of "
        "known misconceptions. The <b>Diagnoser</b> scores a student's explanation against the catalogue. The <b>Tutor</b> replies with a guiding question and a source pointer rather than the answer, "
        "revealing the cited passage only after repeated attempts. The <b>Verifier</b> blocks responses that are ungrounded or leak the answer, and an 'I'm not sure' fallback is used when confidence is low. "
        "The <b>Curriculum Analyst</b> aggregates results with differential-privacy noise and recommends fixes to the lecture that contains the root-cause gap."),
        P("5. Hardware and Software Requirements", H1)]
    s += [table([["Item", "Specification"], ["Language / framework", "Python 3.10+, Flask, SQLite"], ["AI stack", "LlamaIndex/LangGraph, FAISS/Chroma, Neo4j, Hugging Face + PEFT (LoRA), Whisper"],
                 ["Front end", "HTML5, CSS3, JavaScript (SVG graph)"], ["Hardware", "8 GB RAM prototype; single GPU (16 GB) for LoRA training"]], [4.5 * cm, 11.5 * cm]), Spacer(1, 8)]
    s += [P("6. Evaluation Plan", H1)] + bullets([
        "Misconception detection: precision, recall and F1 against faculty-labelled answers.",
        "Tutor quality: LLM-as-judge plus a human rubric (correctness, pedagogy, no answer leakage).",
        "Learning impact: A/B pilot with pre-test and post-test scores.",
        "Ablations: retrieval vs. no retrieval, fine-tuned vs. prompted, single-agent vs. multi-agent."])
    s += [P("7. Expected Outcomes", H1), P(
        "A working, role-based university web portal; a concept-prerequisite misconception graph for one pilot course (Introduction to Machine Learning); measured detection quality; and a faculty dashboard "
        "that turns student errors into concrete teaching improvements. The prototype already runs offline and reached F1 = %.2f on a small author-labelled set (see Report)." % RES[2]["f1"]),
        P("8. Novelty", H1), P("The system audits the <i>teaching</i> rather than only answering questions, and unifies tutoring, curriculum analytics and material feedback in one closed loop with privacy and fairness built in."),
        P("9. References", H1)]
    s += refs()
    build("synopsis.pdf", s)


def refs():
    r = ["Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS.",
         "Hu, E. J. et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models. arXiv:2106.09685.",
         "Dwork, C. and Roth, A. (2014). The Algorithmic Foundations of Differential Privacy. Foundations and Trends in Theoretical Computer Science.",
         "Radford, A. et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision (Whisper). arXiv:2212.04356.",
         "Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS.",
         "Ji, Z. et al. (2023). Survey of Hallucination in Natural Language Generation. ACM Computing Surveys.",
         "Piech, C. et al. (2015). Deep Knowledge Tracing. NeurIPS.",
         "Bloom, B. S. (1984). The 2 Sigma Problem: The Search for Methods of Group Instruction as Effective as One-to-One Tutoring. Educational Researcher.",
         "Vaswani, A. et al. (2017). Attention Is All You Need. NeurIPS."]
    return [P("[%d] %s" % (i + 1, t), SM) for i, t in enumerate(r)]


# ====================== RESEARCH PAPER ======================
def paper():
    s = [P(TITLE, TT), Spacer(1, 6), P("<b>%s</b> (%s)<br/>Master of Computer Applications, RTD Open Elective" % (NAME, REG), CT), Spacer(1, 10),
         P("<b>Abstract.</b> Educational chatbots answer questions but rarely explain why a student is wrong, and give instructors no view of which lectures cause confusion. We present MisconceptionMap, "
           "a retrieval-grounded multi-agent system that detects named misconceptions in student explanations, maps each to a root-cause prerequisite in a concept graph, tutors Socratically without leaking the answer, "
           "and reports differentially private aggregates to faculty. We implement a deployable role-based web portal (student, faculty, administrator) and evaluate the Diagnoser on a small author-labelled set of %d answers over "
           "eight misconceptions from an introductory machine-learning course. A hybrid phrase and TF-IDF diagnoser reaches F1 = %.2f (precision %.2f, recall %.2f), outperforming keyword-only (F1 %.2f) and TF-IDF-only (F1 %.2f) baselines. "
           "These results are preliminary and use synthetic data; we describe the faculty-labelled pilot, LoRA fine-tuning and A/B learning study needed to validate the approach." % (
               RES[0]["n"], RES[2]["f1"], RES[2]["precision"], RES[2]["recall"], RES[0]["f1"], RES[1]["f1"]), B),
         P("<b>Keywords:</b> generative AI, large language models, retrieval-augmented generation, intelligent tutoring, misconception detection, differential privacy.", B),
         P("1. Introduction", H1), P(
        "Large language models (LLMs) can explain almost any topic, yet unrestricted use in university courses raises three concerns: answer leakage that reduces productive struggle, hallucination outside the syllabus, and privacy "
        "of student data. One-to-one tutoring is known to produce large learning gains [8]; scaling it requires systems that diagnose the student's specific misunderstanding, not only produce fluent text. "
        "Meanwhile faculty see only grades, not the conceptual errors behind them."),
        P("Our contributions: (i) a misconception-centred architecture that links tutoring and curriculum analytics in a closed loop; (ii) a concept-prerequisite graph used for root-cause attribution; "
          "(iii) a Verifier agent enforcing grounding and no-leakage, with an explicit 'I'm not sure' fallback; (iv) privacy by design (hashing, k-suppression, Laplace noise); and (v) an open, role-based web implementation."),
        P("2. Related Work", H1), P(
        "Retrieval-augmented generation grounds model output in external documents [1]. Knowledge tracing predicts student mastery from interaction sequences [7] but does not name <i>what</i> the student believes. "
        "Parameter-efficient fine-tuning such as LoRA enables small open models to be specialised cheaply [2]. LLM-as-judge protocols allow scalable evaluation of generated text [5], and hallucination remains an open risk in generation [6]. "
        "Differential privacy provides formal guarantees for aggregate statistics [3]. Our work combines these in one educational workflow focused on misconceptions."),
        P("3. System Architecture", H1), arch(), P("Fig. 1. MisconceptionMap pipeline: ingestion, diagnosis, tutoring, verification and curriculum analytics.", CAP),
        P("<b>Ingestion.</b> Slides, PDFs and Whisper [4] lecture transcripts are chunked with a source label (e.g. 'L4 slide 9'). <b>Concept graph.</b> Concepts and prerequisite edges are stored in Neo4j (JSON in the prototype); every "
          "misconception has a concept and a root-cause concept. <b>Diagnoser.</b> Scores a student explanation against a catalogue of misconceptions; the prototype combines exact/partial phrase match with TF-IDF cosine similarity, "
          "and a LoRA-tuned classifier is the designed upgrade. <b>Tutor.</b> Produces a guiding question and a source pointer; after three attempts on the same misconception it reveals the cited passage and asks the student to restate it. "
          "<b>Verifier.</b> Rejects replies lacking a citation or containing the answer key before the reveal stage. <b>Curriculum Analyst.</b> Aggregates distinct-student counts per misconception with Laplace noise and recommends a revision to the root-cause lecture."),
        P("4. Method", H1), P("4.1 Diagnosis", H2), P(
        "For answer <i>a</i> and misconception <i>m</i>, the hybrid score is s(a,m) = p(a,m) + 2·cos(v<sub>a</sub>, v<sub>m</sub>), where p is 1.0 for an exact catalogue phrase and 0.6 when at least 85% of a phrase's content words occur in <i>a</i>, "
        "and v are TF-IDF vectors. Confidence is s/(s+1); below 0.45 the system abstains and routes the student to retrieved course material instead of guessing."),
        P("4.2 Grounded Socratic tutoring", H2), P("Each reply carries a citation to a retrieved chunk. Before the third attempt the Verifier checks that the key correct phrase of the misconception does not appear in the reply (leak-free). A daily-usage guard nudges students to attempt problems independently, countering over-reliance."),
        P("4.3 Privacy", H2), P("Faculty views show hashed student identifiers. Counts n of distinct students per misconception are released as max(0, round(n + Lap(1/ε))) with ε = 1 by default (sensitivity 1), and groups with n &lt; 3 are suppressed entirely. "
                                "Per-answer text is never shown to faculty. Deployment is on-premise with open-source components."),
        P("4.4 Role-based access", H2), P("Students access the tutor and concept map; faculty access analytics, the misconception graph, materials and anonymised export; administrators additionally manage users and view an audit log. "
                                           "All state-changing requests carry CSRF tokens and passwords are salted hashes."),
        P("5. Experimental Setup", H1), P(
        "We built a catalogue of eight misconceptions for an introductory ML course (overfit/underfit inversion, tuning on the test set, accuracy-only evaluation, training-loss fallacy, learning-rate and global-minimum beliefs, regularisation-increases-complexity, "
        "bias/variance confusion, loss-equals-accuracy). The evaluation set has %d author-written answers: 40 containing a misconception (5 each, paraphrased with varied wording) and 6 correct or off-topic answers. Precision, recall and F1 are "
        "micro-averaged over misconception predictions; accuracy also counts correct abstentions. Because the set is hand-written by the system author and the catalogue was designed alongside it, results are optimistic and should not be read as classroom performance." % RES[0]["n"]),
        P("6. Results", H1), results_table(), Spacer(1, 6), chart(), P("Fig. 2. Ablation of the Diagnoser on the prototype set.", CAP),
        P("Keyword-only matching is precise (1.00) but misses paraphrases (recall %.2f). TF-IDF alone recovers paraphrases (recall %.2f) but confuses overlapping topics such as accuracy-related misconceptions (precision %.2f). "
          "The hybrid combines both and gives the best F1 (%.2f) and accuracy (%.2f)." % (RES[0]["recall"], RES[1]["recall"], RES[1]["precision"], RES[2]["f1"], RES[2]["accuracy"])),
        P("Functional verification of the portal confirmed role separation (student requests to analytics and admin return HTTP 403), CSRF rejection of forged posts, the three-turn tutor flow with guided reveal, and DP-suppressed analytics.")]
    s += [P("7. Discussion and Limitations", H1)] + bullets([
        "Evaluation data are synthetic and author-labelled; inter-annotator agreement with faculty labels has not been measured.",
        "LoRA fine-tuning and prompted-LLM baselines are specified (ml/lora_finetune.py) but were not run; no claim is made about their relative accuracy.",
        "Only the tutor's frame text is multilingual (English, Hindi, Tamil); guiding questions are English in the prototype. Fairness across language proficiency is therefore untested.",
        "Learning impact requires a controlled pilot with pre/post tests; none was conducted.",
        "Retrieval uses TF-IDF; dense embeddings and cross-modal slide-image retrieval are future work."])
    s += [P("8. Conclusion and Future Work", H1), P(
        "MisconceptionMap shows that tutoring, curriculum auditing and privacy can be unified around misconceptions in a deployable university portal. Future work: collect faculty-labelled data, fine-tune a small open model with LoRA, "
        "run the A/B learning study, extend fairness audits across language levels, and add multimodal retrieval over slide images."), P("References", H1)] + refs()
    build("research_paper.pdf", s)


# ====================== PROJECT REPORT ======================
def report():
    s = cover("PROJECT REPORT")
    s += [P("DECLARATION", H1), P("I, <b>%s</b> (Register No. <b>%s</b>), declare that this project report titled '<i>%s</i>' is my original work carried out for the RTD Open Elective and has not been submitted elsewhere." % (NAME, REG, TITLE)),
          Spacer(1, 1.2 * cm), P("Place: ____________ &nbsp;&nbsp;&nbsp;&nbsp; Signature: ______________ (%s)" % NAME, B), PageBreak(),
          P("ABSTRACT", H1), P("Generative AI tools in universities mostly answer questions. This project builds MisconceptionMap, a role-based university portal that identifies the specific misconceptions behind student errors, traces them to prerequisite concept gaps, "
                                "tutors students Socratically with cited course material, and gives faculty privacy-preserving analytics on where teaching needs improvement. The implemented prototype (Flask, SQLite, offline retrieval and diagnosis) "
                                "reached F1 = %.2f on a small author-labelled evaluation set. The report documents requirements, design, implementation, testing, limitations and the roadmap to a full LLM-based deployment." % RES[2]["f1"]), PageBreak(),
          P("TABLE OF CONTENTS", H1)]
    toc = ["1. Introduction", "2. Literature Survey", "3. Problem Statement and Objectives", "4. Requirements Analysis", "5. System Design", "6. Implementation", "7. Generative AI Components",
           "8. Privacy, Fairness and Ethics", "9. Testing", "10. Results and Evaluation", "11. User Guide", "12. Limitations", "13. Conclusion and Future Scope", "References"]
    s += [P(t) for t in toc] + [PageBreak()]
    s += [P("1. Introduction", H1), P(
        "University instructors rarely see why students fail: assessments show wrong answers but not the mistaken beliefs behind them. Students, meanwhile, increasingly use general chatbots that give answers directly. "
        "MisconceptionMap addresses both by treating the <b>misconception</b> as the unit of teaching and analytics."),
        P("1.1 Scope", H2), P("The prototype is piloted on one course, CS301 Introduction to Machine Learning, covering eight concepts and eight misconceptions. The architecture generalises to other courses by replacing the data file."),
        P("1.2 Novelty", H2), P("(i) It audits teaching, not only learners; (ii) tutoring, curriculum analytics and material feedback form one closed loop; (iii) misconceptions are tied to a prerequisite graph for root-cause analysis; (iv) a Verifier enforces grounding and no answer leakage; (v) privacy and fairness are first-class requirements."),
        P("2. Literature Survey", H1), P(
        "Intelligent tutoring systems have long shown that individual tutoring outperforms group instruction [8]. Knowledge tracing models student mastery from response sequences [7]. Retrieval-augmented generation [1] reduces hallucination "
        "by conditioning generation on retrieved passages, although hallucination is not eliminated [6]. LoRA [2] enables low-cost specialisation of open models, supporting on-premise deployment. LLM-as-judge methods [5] give scalable evaluation of free-text tutor replies "
        "but need human calibration. Differential privacy [3] gives quantifiable guarantees for aggregate statistics, relevant for small cohorts. Speech models such as Whisper [4] allow lecture video to be turned into searchable text."),
        table([["Approach", "Strength", "Gap addressed here"], ["General chatbots", "Fluent answers", "Leak answers, ungrounded, no analytics"], ["Knowledge tracing", "Predicts mastery", "Does not name the misconception"],
               ["Plain RAG Q&amp;A", "Grounded answers", "Not diagnostic, no teaching audit"], ["MisconceptionMap", "Diagnose + tutor + audit", "Closed loop with privacy"]], [4 * cm, 4.5 * cm, 7.5 * cm]), Spacer(1, 6),
        P("3. Problem Statement and Objectives", H1), P("Design and implement a grounded, privacy-preserving generative-AI system that detects student misconceptions, tutors without giving away answers, and reports root-cause teaching gaps to faculty through a role-based university portal."),
        ] + bullets(["O1: Retrieval over course material with citations.", "O2: Concept and prerequisite graph with misconception-to-root mapping.", "O3: Diagnoser, Tutor, Verifier, Analyst agents.",
                     "O4: Role-based web portal for student, faculty, admin.", "O5: Privacy (hashing, k-suppression, DP) and basic fairness/over-reliance safeguards.", "O6: Quantitative evaluation with ablations."])
    s += [P("4. Requirements Analysis", H1), P("4.1 Functional requirements", H2), table([
        ["ID", "Requirement", "Role"], ["F1", "Secure login with role-based access", "All"], ["F2", "Submit explanation and receive Socratic reply with citation", "Student"], ["F3", "View personal focus areas and history", "Student"],
        ["F4", "View misconception analytics with DP counts and recommendations", "Faculty/Admin"], ["F5", "View concept graph heat-map", "Faculty/Admin"], ["F6", "Upload and index course material", "Faculty/Admin"],
        ["F7", "Export anonymised data (CSV)", "Faculty/Admin"], ["F8", "Create/disable users, view audit log", "Admin"]], [1.4 * cm, 11 * cm, 3.6 * cm]),
        P("4.2 Non-functional requirements", H2)] + bullets(["Privacy: no personal identifiers in faculty views; small groups suppressed.", "Reliability: abstain with 'I'm not sure' rather than guess.",
                                                              "Security: hashed passwords, CSRF tokens, session cookies HttpOnly/SameSite, server-side role checks.", "Usability: responsive portal in light/dark mode; mobile-friendly.",
                                                              "Deployability: runs offline on a laptop; no cloud dependency."])
    s += [P("4.3 Software and hardware", H2), P("Python 3.12, Flask 3, SQLite, vanilla JavaScript/SVG. Planned: LlamaIndex/LangGraph, FAISS/Chroma, Neo4j, Hugging Face Transformers + PEFT, Whisper. Any modern laptop (8 GB RAM) runs the prototype; LoRA training needs one 16 GB GPU."),
          P("5. System Design", H1), arch(), P("Fig. 1. System architecture.", CAP),
          P("5.1 Roles and access matrix", H2), table([["Page", "Student", "Faculty", "Admin"], ["Home / dashboard", "Yes", "Redirect to analytics", "Redirect to admin"], ["Socratic tutor", "Yes", "No (403)", "No (403)"],
                                                    ["Concept graph", "Plain map", "Heat-map", "Heat-map"], ["Analytics, export", "No (403)", "Yes", "Yes (raw n)"], ["Course materials", "No (403)", "Yes", "Yes"], ["User admin, audit log", "No (403)", "No (403)", "Yes"]], [4.5 * cm, 3.5 * cm, 4 * cm, 4 * cm]),
          P("5.2 Data model", H2), table([["Table", "Key fields"], ["users", "id, username, name, password hash, role, reg_no, lang, active"], ["attempts", "id, user_id, answer, misconception id, confidence, timestamp, synthetic flag"], ["audit", "id, timestamp, actor, action"],
                                         ["course.json", "concepts, prerequisite edges, material chunks, misconception catalogue (phrases, questions, hints, root cause)"]], [3.5 * cm, 12.5 * cm]),
          P("5.3 Tutor interaction flow", H2)] + bullets(["Student writes an explanation (at least four words).", "Diagnoser returns a misconception and confidence, or abstains below 0.45.",
                                                          "Turn 1: acknowledge + source pointer + guiding question. Turn 2: another guiding question. Turn 3+: reveal cited passage and ask the student to restate it.",
                                                          "Verifier checks grounding and answer leakage before display; abstentions show retrieved materials.", "Attempt is logged for the Curriculum Analyst."])
    s += [P("6. Implementation", H1), table([["File", "Purpose"], ["app.py", "Flask routes, RBAC decorator, CSRF, SQLite, seeding, CSV export, admin"], ["engine.py", "TF-IDF retrieval, Diagnoser, Tutor, Verifier, multilingual frames, DP"],
                                            ["data/course.json", "Course knowledge base"], ["templates/ + static/", "Portal UI (navy/maroon university theme, SVG graph)"], ["eval/evaluate.py", "Precision/recall/F1 ablation"],
                                            ["ml/lora_finetune.py", "LoRA sequence-classification script (not run in this build)"], ["docs/build_docs.py", "Generates the three PDFs"]], [4 * cm, 12 * cm]),
          P("The RBAC decorator <font name='Courier'>login_required(*roles)</font> redirects unauthenticated users to login and returns 403 for disallowed roles, enforced server-side on every route. Passwords use Werkzeug salted hashes; "
            "each session carries a CSRF token validated on all POST requests."),
          P("7. Generative AI Components", H1), P("7.1 Retrieval (RAG)", H2), P("Course text is split into source-labelled chunks and indexed with TF-IDF; retrieval returns the top chunks with similarity scores and citations. The production design replaces TF-IDF with embeddings in FAISS/Chroma and adds slide-image and transcript chunks."),
          P("7.2 Knowledge graph", H2), P("Eight concepts and eight prerequisite edges (e.g. Data Splits → Bias-Variance → Overfitting → Regularisation). Each misconception stores its concept and a root concept; the Analyst groups results by root to point to the lecture to revise."),
          P("7.3 Multi-agent orchestration", H2), P("The prototype chains Diagnoser → Tutor → Verifier in code. The planned LangGraph version adds an LLM Tutor (phrasing only, grounded on the cited chunk) and a Curriculum Analyst agent that drafts revised examples and quiz items."),
          P("7.4 Fine-tuning plan", H2), P("<font name='Courier'>ml/lora_finetune.py</font> trains a LoRA adapter (r = 8, α = 16, q/v projections) on a small open model for sequence classification over the misconception labels plus 'none'. "
                                          "It will be compared against a prompted general LLM and the hybrid baseline using the same faculty-labelled split. No results from this experiment are claimed."),
          P("7.5 Hallucination control", H2)] + bullets(["Every tutor reply cites retrieved course material.", "Verifier rejects ungrounded or answer-leaking replies.", "Low confidence leads to 'I'm not sure' plus retrieved sources."]) + [
        P("8. Privacy, Fairness and Ethics", H1)] + bullets([
            "Anonymisation: faculty exports use salted SHA-256 student hashes; raw answers are never shown to faculty.", "Differential privacy: Laplace noise (ε configurable, default 1) on counts; groups under 3 suppressed.",
            "On-premise, open-source deployment; no student text leaves the server in the prototype.", "Fairness plan: compare detection recall across English proficiency levels and backgrounds; the prototype has not yet done this.",
            "Over-reliance guard: guided reveal only after three attempts, 'explain it back' prompt, daily-usage nudge.", "Multilingual: tutor framing available in English, Hindi and Tamil; question translation is future work."])
    s += [P("9. Testing", H1), table([["Test", "Expected", "Result"], ["Student opens /analytics or /admin", "HTTP 403", "Pass"], ["Faculty opens /admin", "HTTP 403", "Pass"], ["Faculty/admin open analytics, materials, graph, CSV", "HTTP 200", "Pass"],
                                      ["POST without CSRF token", "HTTP 400", "Pass"], ["Unauthenticated access", "Redirect to login", "Pass"], ["Tutor: same misconception three times", "Turn 3 reveals cited passage", "Pass"],
                                      ["Analytics with groups under 3", "Shown as '&lt;3'", "Pass (by design)"], ["Admin creates user", "User listed and audit entry", "Pass"]], [7 * cm, 5 * cm, 4 * cm]),
          P("10. Results and Evaluation", H1), P("The Diagnoser was evaluated on %d author-written answers (40 with a misconception, 6 correct or off-topic). This is a prototype check, not classroom evidence." % RES[0]["n"]), results_table(), Spacer(1, 6), chart(),
          P("Fig. 2. Precision, recall and F1 for the three diagnoser variants.", CAP), P(
        "Hybrid scoring gave the best F1 (%.2f). Keyword-only had perfect precision but lower recall (%.2f); TF-IDF-only had high recall (%.2f) with lower precision (%.2f). Because the author wrote both catalogue and test set, true performance on real students is expected to be lower."
        % (RES[2]["f1"], RES[0]["recall"], RES[1]["recall"], RES[1]["precision"])),
          P("10.1 Planned full evaluation", H2), table([["Dimension", "Method"], ["Detection", "Precision/recall/F1 vs faculty-labelled anonymised answers; inter-annotator agreement"], ["Tutor quality", "LLM-as-judge + human rubric: correctness, pedagogy, no leakage"],
                                                       ["Learning impact", "A/B pilot: pre-test, post-test, effect size"], ["Ablations", "RAG vs none; LoRA vs prompted; single vs multi-agent"], ["Fairness", "Metrics by language level/background"]], [3.5 * cm, 12.5 * cm]),
          P("11. User Guide", H1)] + bullets(["Install: <font name='Courier'>pip install -r requirements.txt</font>; start: <font name='Courier'>python app.py</font>; open http://127.0.0.1:5000.",
                                              "Student (lavanya / student123): open Socratic Tutor, write an explanation, answer the guiding questions, review focus areas on Home.",
                                              "Faculty (faculty / faculty123): review Analytics and recommendations, inspect the graph heat-map, add materials, export CSV.",
                                              "Admin (admin / admin123): create/disable users and read the audit log. Change all demo passwords and set SECRET_KEY before real use."])
    s += [P("12. Limitations", H1)] + bullets(["Seed analytics and the evaluation set are synthetic; no real students were involved.", "The prototype uses TF-IDF and phrase matching; LLM, LoRA, Whisper, FAISS and Neo4j are designed but not integrated.",
                                                "Only tutor frame text is translated; fairness across languages untested.", "Single course, eight misconceptions; coverage will need faculty input.", "Session-based chat history, no production-grade rate limiting or HTTPS configuration."])
    s += [P("13. Conclusion and Future Scope", H1), P("MisconceptionMap demonstrates a deployable, role-based university portal that moves generative AI in education from answering to diagnosing. Next steps are faculty-labelled data, LoRA fine-tuning, the A/B learning pilot, "
                                                     "multimodal retrieval over slide images, and fairness audits across language levels."), P("References", H1)] + refs()
    build("project_report.pdf", s)


if __name__ == "__main__":
    synopsis(); paper(); report(); print("built")
