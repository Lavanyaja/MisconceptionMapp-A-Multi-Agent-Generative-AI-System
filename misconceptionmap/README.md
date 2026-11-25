# MisconceptionMap - University Portal (Generative AI project)
Author: **Lavanya J (SCA25MCA110)** · RTD Open Elective

An AI system that finds *why* students fail: it detects misconceptions in student explanations, traces them to prerequisite gaps in a concept graph, tutors Socratically with cited course material, and gives faculty privacy-preserving analytics.

## Run
```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
python eval/evaluate.py  # diagnoser ablation (keyword / tf-idf / hybrid)
```
Demo logins: `lavanya/student123` (student), `faculty/faculty123` (faculty), `admin/admin123` (admin).
Set `SECRET_KEY`, `ANON_SALT`, `DP_EPSILON` env vars for real use.

## Roles
| Role | Access |
|---|---|
| Student | Home, Socratic Tutor, concept map |
| Faculty | Analytics (DP counts), misconception graph heat-map, course materials upload, anonymised CSV export |
| Admin | All faculty pages + user management + audit log |

## Layout
`app.py` web app + RBAC + CSRF · `engine.py` retrieval, Diagnoser, Tutor, Verifier, DP · `data/course.json` concepts, prerequisites, materials, misconceptions · `eval/` ablation · `ml/lora_finetune.py` LoRA classifier (needs GPU) · `docs/` research paper, project report, synopsis (PDF) + builder.

## Honest scope notes
* The prototype runs fully offline: TF-IDF retrieval and rule/phrase diagnoser. The LLM hooks (LoRA classifier, LLM tutor phrasing, Whisper transcripts, Neo4j, FAISS) are designed in the report; `ml/lora_finetune.py` is provided but not run here.
* Seed analytics are synthetic. The 46-answer evaluation set is author-written, not real student data.
* Only the tutor's framing text is translated (English/Hindi/Tamil); questions are English in the prototype.
