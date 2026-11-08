"""Logika aplikasi tanpa Streamlit, supaya dapat diuji dengan pytest (NFR-13)."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

ARTIFACTS = Path(__file__).resolve().parent.parent / "artifacts"
SCHEMA_VERSION = 1
THRESHOLD = 0.5
MIN_DIFFERENCE = 0.05
STAGES = ["T1", "T2", "T3"]
SEMESTERS = {"T1": [], "T2": ["1st"], "T3": ["1st", "2nd"]}
FINANCIAL = ["Debtor", "Tuition fees up to date", "Scholarship holder"]
SENSITIVE = [*FINANCIAL, "Gender"]
NOMINAL = [
    "Marital status",
    "Application mode",
    "Course",
    "Previous qualification",
    "Nacionality",
    "Mother's qualification",
    "Father's qualification",
    "Mother's occupation",
    "Father's occupation",
]
MODEL_IDS = [f"{scenario}_{stage}_rf" for scenario in "AB" for stage in STAGES]
RESULT_FILES = [
    "manifest.json",
    "dataset_summary.json",
    "metrics.json",
    "comparisons.json",
    "shap_global.json",
    "test_predictions.json",
    "test_rows.csv",
    "form_spec.json",
]
# Patokan G2 dari rancangan (PRD bagian 3), bukan hasil penelitian.
G2_T1_PR_AUC = 0.60
G2_T2_PR_AUC = 0.80
G2_T2_RECALL = 0.70

DOWNLOAD_FIX = (
    "Unduh `artifacts.zip` dari GitHub Release `artifacts-v1`, lalu jalankan `unzip -q artifacts.zip -d artifacts` "
    "dari folder proyek. Cara lain: jalankan ulang notebook dengan `run-notebook`."
)


def model_id(stage, financial):
    return f"{'A' if financial else 'B'}_{stage}_rf"


def check_artifacts(root=None) -> list[str]:
    """APP-02: daftar masalah artefak dan versi. Daftar kosong berarti aplikasi boleh berjalan."""
    root = Path(root or ARTIFACTS)
    expected = RESULT_FILES + [f"models/{model}.joblib" for model in MODEL_IDS]
    missing = [name for name in expected if not (root / name).is_file()]
    if missing:
        return [f"File artefak tidak ditemukan di `{root.name}/`: {', '.join(missing)}. {DOWNLOAD_FIX}"]

    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        schema, threshold = manifest["schema_version"], manifest["threshold"]
        trained_sklearn, trained_numpy = manifest["versions"]["scikit-learn"], manifest["versions"]["numpy"]
    except (ValueError, KeyError, TypeError) as error:
        return [f"`manifest.json` tidak dapat dibaca ({type(error).__name__}: {error}). {DOWNLOAD_FIX}"]

    nix_fix = (
        "Jalankan aplikasi dari shell Nix proyek (`nix develop`, lalu `app`), dan jangan memperbarui `flake.lock`."
    )
    problems = []
    if schema != SCHEMA_VERSION:
        problems.append(
            f"`schema_version` artefak {schema}, sedangkan aplikasi membutuhkan {SCHEMA_VERSION}. "
            "Pakai artefak dan kode dari versi yang sama."
        )
    if sklearn.__version__ != trained_sklearn:
        problems.append(
            f"scikit-learn {sklearn.__version__} terpasang, sedangkan model dibuat dengan {trained_sklearn}. {nix_fix}"
        )
    if np.__version__.split(".")[0] != str(trained_numpy).split(".")[0]:
        problems.append(f"numpy {np.__version__} terpasang, sedangkan model dibuat dengan {trained_numpy}. {nix_fix}")
    if threshold != THRESHOLD:
        problems.append(f"Ambang di `manifest.json` {threshold}, sedangkan aplikasi memakai {THRESHOLD}.")
    return problems


def load_json(name, root=ARTIFACTS):
    return json.loads((Path(root) / name).read_text(encoding="utf-8"))


def load_test_rows(root=ARTIFACTS):
    return pd.read_csv(Path(root) / "test_rows.csv", index_col="row_id")


def load_model(model, root=ARTIFACTS):
    # joblib.load dapat menjalankan kode, jadi hanya enam model hasil notebook sendiri yang boleh dimuat.
    if model not in MODEL_IDS:
        raise ValueError(f"Model tidak dikenal: {model}")
    return joblib.load(Path(root) / "models" / f"{model}.joblib")


def make_explainer(model):
    import shap  # diimpor saat dibutuhkan, karena impornya memperlambat halaman pertama

    return shap.TreeExplainer(model["clf"])


def default_row(spec):
    """Satu baris berisi `defaults` dari data latih, dengan tipe int atau float seperti di `form_spec.json`."""
    return pd.DataFrame([spec["defaults"]])


def is_integer(spec, attribute):
    return isinstance(spec["defaults"][attribute], int)


def build_row(features, values, base):
    """Menggabungkan isian form dengan atribut tersembunyi dari `base` (satu baris DataFrame)."""
    row = base[features].reset_index(drop=True)
    for attribute, value in values.items():
        row[attribute] = row[attribute].dtype.type(value)
    return row


def validate(values, stage, grade_range) -> list[str]:
    """APP-33: aturan V1 sampai V4 untuk tiap semester yang tersedia pada tahap ini."""
    problems = []
    for semester in SEMESTERS[stage]:
        label = "Semester 1" if semester == "1st" else "Semester 2"
        enrolled, evaluations, approved, grade = (
            values[f"Curricular units {semester} sem ({field})"]
            for field in ["enrolled", "evaluations", "approved", "grade"]
        )
        low, high = grade_range[semester]
        if approved > enrolled:
            problems.append(
                f"{label}, V1: mata kuliah lulus ({approved:g}) tidak boleh melebihi mata kuliah diambil ({enrolled:g})."
            )
        if evaluations < approved:
            problems.append(
                f"{label}, V2: jumlah evaluasi ({evaluations:g}) tidak boleh kurang dari mata kuliah lulus ({approved:g})."
            )
        if approved == 0 and grade != 0:
            problems.append(f"{label}, V3: jika tidak ada mata kuliah lulus, rata-rata nilai harus 0.")
        if approved > 0 and grade == 0:
            problems.append(f"{label}, V3: jika ada mata kuliah lulus, rata-rata nilai tidak boleh 0.")
        if grade > 0 and not low <= grade <= high:
            problems.append(f"{label}, V4: rata-rata nilai di atas 0 harus berada antara {low:.3f} dan {high:.3f}.")
    return problems


def source_attribute(column):
    group, name = column.split("__", 1)
    return name if group == "remainder" else next(a for a in NOMINAL if name.startswith(f"{a}_"))


def aggregate_shap(names, values) -> dict:
    """Menjumlahkan nilai SHAP kolom one-hot ke atribut asalnya, untuk satu baris."""
    totals = {}
    for column, value in zip(names, values):
        attribute = source_attribute(column)
        totals[attribute] = totals.get(attribute, 0.0) + float(value)
    return totals


def score_and_explain(model, explainer, row, k=5):
    """Skor risiko satu baris dan k atribut dengan nilai absolut SHAP terbesar, seperti `top` di notebook."""
    attributes = list(model.feature_names_in_)
    frame = row[attributes]
    risk = float(model.predict_proba(frame)[0, 1])
    values = explainer.shap_values(model["enc"].transform(frame))[0, :, 1]
    totals = aggregate_shap(model["enc"].get_feature_names_out(), values)
    contributions = np.array([totals[attribute] for attribute in attributes])
    order = np.argsort(-np.abs(contributions), kind="stable")[:k]
    return risk, [(attributes[i], float(contributions[i])) for i in order]


def target_status(metrics, scenario):
    """Target G2 dan tahap paling dini yang memenuhinya, sama dengan NB-12."""
    by_id = {entry["model_id"]: entry for entry in metrics}
    t1, t2 = by_id[f"{scenario}_T1_rf"], by_id[f"{scenario}_T2_rf"]
    t1_met = t1["pr_auc"] >= G2_T1_PR_AUC
    t2_met = t2["pr_auc"] >= G2_T2_PR_AUC and t2["recall"] >= G2_T2_RECALL
    return {
        "scenario": scenario,
        "t1_pr_auc": t1["pr_auc"],
        "t2_pr_auc": t2["pr_auc"],
        "t2_recall": t2["recall"],
        "t1_met": t1_met,
        "t2_met": t2_met,
        "g2": t1_met and t2_met,
        "earliest": "T1" if t1_met else "T2" if t2_met else "tidak ada",
    }


def priority_table(predictions, model):
    """Mahasiswa data uji untuk satu model, diurutkan dari skor tertinggi."""
    frame = pd.DataFrame([entry for entry in predictions if entry["model_id"] == model])
    frame = frame.sort_values(["risk", "row_id"], ascending=[False, True], kind="stable").reset_index(drop=True)
    frame.insert(0, "rank", range(1, len(frame) + 1))
    return frame


def flag_summary(frame):
    """Jumlah ditandai, presisi, dan recall dari aturan `risk >= 0.5` yang tersimpan di `flagged`."""
    flagged, dropout = frame["flagged"].astype(bool), frame["status"] == "Dropout"
    tp, fp, fn = int((flagged & dropout).sum()), int((flagged & ~dropout).sum()), int((~flagged & dropout).sum())
    return {
        "flagged": tp + fp,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
    }
