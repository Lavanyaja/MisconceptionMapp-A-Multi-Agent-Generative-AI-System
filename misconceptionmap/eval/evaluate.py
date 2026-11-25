"""Prototype evaluation of the Diagnoser (ablation: keyword vs tfidf vs hybrid).
The set below is a small hand-written, author-labelled dataset (NOT real student data).
Replace with faculty-labelled anonymised answers for the real pilot."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine import diagnose, MIS

DATA = [
 ("m1", "I think overfitting is when the model is too simple to learn the data."),
 ("m1", "Overfitting means underfitting basically, the model is a simple one."),
 ("m1", "A model overfits because it is too simple and misses patterns."),
 ("m1", "Underfitting happens when the model is too complex for the task."),
 ("m1", "When a model is overfit it has too few parameters, so it is very simple."),
 ("m2", "To pick the best hyperparameters I tune on the test set and keep the highest score."),
 ("m2", "We should choose the best model using the test set since it is unseen."),
 ("m2", "I use the test data to tune the learning rate and depth."),
 ("m2", "Select hyperparameters using the test results, then report that same score."),
 ("m2", "Try many settings, check each on the held-out test split, keep the winner."),
 ("m3", "Accuracy is enough to judge any classifier."),
 ("m3", "High accuracy means the model is good, so I only need accuracy."),
 ("m3", "I think accuracy alone is enough for a fraud detector."),
 ("m3", "A 99% accurate model is always a great model, no other metric needed."),
 ("m3", "Accuracy is all you need when comparing classifiers."),
 ("m4", "Lower training loss means better model, so I train until it is zero."),
 ("m4", "Training longer is always better for the network."),
 ("m4", "Zero training error means perfect model."),
 ("m4", "More epochs always better, loss keeps going down so it keeps improving."),
 ("m4", "As the training loss is low the model must be good."),
 ("m5", "A larger learning rate is always faster so I set it high."),
 ("m5", "Gradient descent always finds the global minimum."),
 ("m5", "Increase the learning rate to converge faster, there is no downside."),
 ("m5", "Gradient descent guarantees the global optimum for any network."),
 ("m5", "Higher learning rate always speeds up training."),
 ("m6", "Regularization adds more features to the model."),
 ("m6", "Regularisation increases model complexity because of the extra term."),
 ("m6", "Regularization makes the model more complex so it fits better."),
 ("m6", "I believe regularization increases the number of parameters."),
 ("m6", "With regularization the model gets more complex and flexible."),
 ("m7", "High variance means underfitting."),
 ("m7", "Bias and variance are the same thing, just two names."),
 ("m7", "High bias leads to overfitting."),
 ("m7", "Variance is the same as bias in a model."),
 ("m7", "A high variance model underfits because of variance."),
 ("m8", "Loss and accuracy are the same thing."),
 ("m8", "We minimize accuracy using gradient descent."),
 ("m8", "The loss function is accuracy."),
 ("m8", "Loss is just accuracy measured differently, so we optimise accuracy directly."),
 ("m8", "Loss means accuracy of the model."),
 (None, "Overfitting happens when a model is too complex and memorises noise in training data."),
 (None, "We tune hyperparameters on the validation set and use the test set once at the end."),
 (None, "On imbalanced data I would report precision, recall and F1 instead of accuracy only."),
 (None, "Regularization adds a penalty on large weights which reduces variance."),
 (None, "Gradient descent can overshoot if the learning rate is too large."),
 (None, "What time is the lab tomorrow?"),
]


def run(mode):
    tp = {k: 0 for k in MIS}; fp = dict(tp); fn = dict(tp); correct = 0
    for gold, ans in DATA:
        pred, _, _ = diagnose(ans, mode)
        correct += pred == gold
        if pred == gold and gold:
            tp[gold] += 1
        else:
            if pred: fp[pred] += 1
            if gold: fn[gold] += 1
    T, F, N = sum(tp.values()), sum(fp.values()), sum(fn.values())
    p = T / (T + F) if T + F else 0; r = T / (T + N) if T + N else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    return dict(mode=mode, precision=round(p, 3), recall=round(r, 3), f1=round(f1, 3),
                accuracy=round(correct / len(DATA), 3), n=len(DATA))


if __name__ == "__main__":
    res = [run(m) for m in ("keyword", "tfidf", "hybrid")]
    for r in res:
        print(r)
    json.dump(res, open(os.path.join(os.path.dirname(__file__), "results.json"), "w"), indent=2)
