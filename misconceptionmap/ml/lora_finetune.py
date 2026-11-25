"""LoRA fine-tuning of a small open model for misconception classification.
Not executed in the sandbox build (needs GPU + internet). Run:
  pip install transformers peft datasets accelerate torch
  python ml/lora_finetune.py --data data/labelled.jsonl --base mistralai/Mistral-7B-v0.1
labelled.jsonl rows: {"answer": "...", "label": "m1"}   (label "none" for correct answers)
"""
import argparse, json
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments)

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--base", default="mistralai/Mistral-7B-v0.1")
ap.add_argument("--out", default="ml/out"); a = ap.parse_args()

rows = [json.loads(l) for l in open(a.data, encoding="utf-8")]
labels = sorted({r["label"] for r in rows}); l2i = {l: i for i, l in enumerate(labels)}
tok = AutoTokenizer.from_pretrained(a.base); tok.pad_token = tok.pad_token or tok.eos_token
ds = Dataset.from_list([{"text": r["answer"], "label": l2i[r["label"]]} for r in rows]).train_test_split(0.2, seed=1)
ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=128, padding="max_length"), batched=True)
model = AutoModelForSequenceClassification.from_pretrained(a.base, num_labels=len(labels))
model.config.pad_token_id = tok.pad_token_id
model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, task_type="SEQ_CLS",
                                         target_modules=["q_proj", "v_proj"]))
model.print_trainable_parameters()
Trainer(model=model, train_dataset=ds["train"], eval_dataset=ds["test"],
        args=TrainingArguments(a.out, per_device_train_batch_size=8, num_train_epochs=4, learning_rate=2e-4,
                               logging_steps=10, report_to=[])).train()
model.save_pretrained(a.out)
