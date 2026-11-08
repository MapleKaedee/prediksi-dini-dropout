import json

import core
import labels
import numpy as np
import pandas as pd
import pytest

HAS_ARTIFACTS = (core.ARTIFACTS / "manifest.json").is_file()
needs_artifacts = pytest.mark.skipif(
    not HAS_ARTIFACTS,
    reason="artifacts/ belum ada: unduh artifacts.zip dari Release artifacts-v1 atau jalankan notebook",
)
GRADES = {"1st": [9.8, 18.875], "2nd": [10.0, 18.571]}


def semester(semester="1st", enrolled=6, evaluations=8, approved=5, grade=12.5):
    fields = {"enrolled": enrolled, "evaluations": evaluations, "approved": approved, "grade": grade}
    return {f"Curricular units {semester} sem ({field})": value for field, value in fields.items()}


@pytest.fixture(scope="module")
def spec():
    return core.load_json("form_spec.json")


@pytest.fixture(scope="module")
def test_rows():
    return core.load_test_rows()


@pytest.fixture(scope="module")
def models():
    return {model_id: core.load_model(model_id) for model_id in core.MODEL_IDS}


@pytest.mark.parametrize(
    "values",
    [
        semester(),
        semester(approved=6, evaluations=6),
        semester(approved=0, evaluations=0, grade=0),
        semester(grade=9.8),
        semester(grade=18.875),
    ],
)
def test_validate_accepts_consistent_semester(values):
    assert core.validate(values, "T2", GRADES) == []


@pytest.mark.parametrize(
    "values, rule",
    [
        (semester(approved=7, evaluations=8), "V1"),
        (semester(evaluations=4), "V2"),
        (semester(approved=0, evaluations=3, grade=12.5), "V3"),
        (semester(grade=0), "V3"),
        (semester(grade=5.0), "V4"),
        (semester(grade=19.0), "V4"),
    ],
)
def test_validate_rejects_each_rule(values, rule):
    problems = core.validate(values, "T2", GRADES)
    assert len(problems) == 1 and f"{rule}:" in problems[0], problems


def test_validate_checks_only_semesters_of_the_stage():
    broken = semester("1st", approved=9) | semester("2nd", approved=9)
    assert core.validate(broken, "T1", GRADES) == []
    assert {p.split(",")[0] for p in core.validate(broken, "T2", GRADES)} == {"Semester 1"}
    assert {p.split(",")[0] for p in core.validate(broken, "T3", GRADES)} == {"Semester 1", "Semester 2"}


@needs_artifacts
def test_validate_accepts_all_test_rows_and_defaults(spec, test_rows):
    grades = spec["grade_nonzero_range"]
    failed = {row_id: core.validate(row, "T3", grades) for row_id, row in test_rows.iterrows()}
    assert len(test_rows) == 842
    assert {row_id: problems for row_id, problems in failed.items() if problems} == {}
    for model_id in core.MODEL_IDS:
        stage = model_id.split("_")[1]
        assert core.validate(spec["defaults"], stage, grades) == [], model_id


def test_aggregate_shap_keeps_sum_and_every_source():
    names = [
        "nominal__Course_33",
        "nominal__Course_infrequent_sklearn",
        "nominal__Previous qualification_3",
        "remainder__Previous qualification (grade)",
        "remainder__Debtor",
    ]
    values = np.array([0.5, -0.25, 0.125, 0.25, -0.375])
    totals = core.aggregate_shap(names, values)
    assert totals == {
        "Course": 0.25,
        "Previous qualification": 0.125,
        "Previous qualification (grade)": 0.25,
        "Debtor": -0.375,
    }
    assert sum(totals.values()) == pytest.approx(values.sum())


@needs_artifacts
def test_aggregate_shap_on_real_encoder(models):
    model = models["A_T3_rf"]
    names = model["enc"].get_feature_names_out()
    values = np.random.default_rng(0).normal(size=len(names))
    totals = core.aggregate_shap(names, values)
    assert set(totals) == set(model.feature_names_in_)
    assert sum(totals.values()) == pytest.approx(values.sum())


def test_check_artifacts_reports_missing_files(tmp_path):
    problems = core.check_artifacts(tmp_path)
    assert len(problems) == 1
    assert "manifest.json" in problems[0] and "models/B_T3_rf.joblib" in problems[0] and "artifacts-v1" in problems[0]


def test_check_artifacts_reports_version_mismatch(tmp_path):
    for name in core.RESULT_FILES + [f"models/{model_id}.joblib" for model_id in core.MODEL_IDS]:
        (tmp_path / name).parent.mkdir(exist_ok=True)
        (tmp_path / name).write_text("")
    manifest = {"schema_version": 1, "threshold": 0.5, "versions": {"scikit-learn": "0.0.1", "numpy": "1.26.4"}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    problems = core.check_artifacts(tmp_path)
    assert len(problems) == 2
    assert "scikit-learn" in problems[0] and "0.0.1" in problems[0]
    assert "numpy" in problems[1] and "1.26.4" in problems[1]

    (tmp_path / "manifest.json").write_text("{")
    assert "manifest.json" in core.check_artifacts(tmp_path)[0]


@needs_artifacts
def test_check_artifacts_accepts_final_artifacts():
    assert core.check_artifacts() == []


@needs_artifacts
def test_priority_summary_matches_metrics():
    predictions = core.load_json("test_predictions.json")
    metrics = {entry["model_id"]: entry for entry in core.load_json("metrics.json")}
    for model_id in core.MODEL_IDS:
        table = core.priority_table(predictions, model_id)
        summary = core.flag_summary(table)
        expected = metrics[model_id]
        assert len(table) == 842 and table["risk"].is_monotonic_decreasing, model_id
        assert summary["flagged"] == expected["tp"] + expected["fp"], model_id
        assert round(summary["precision"], 6) == expected["precision"], model_id
        assert round(summary["recall"], 6) == expected["recall"], model_id


@needs_artifacts
def test_scores_of_20_students_match_predictions(models, spec, test_rows):
    predictions = {(entry["model_id"], entry["row_id"]): entry for entry in core.load_json("test_predictions.json")}
    students = test_rows.index[::42][:20]
    assert len(students) == 20
    for position, row_id in enumerate(students):
        model_id = core.MODEL_IDS[position % len(core.MODEL_IDS)]
        model = models[model_id]
        base = test_rows.loc[[row_id]]
        values = {attribute: base[attribute].iloc[0] for attribute in spec["models"][model_id]}
        row = core.build_row(list(model.feature_names_in_), values, base)
        risk, top = core.score_and_explain(model, core.make_explainer(model), row)
        expected = predictions[(model_id, row_id)]
        assert round(risk, 6) == expected["risk"], (model_id, row_id)
        assert [attribute for attribute, _ in top] == [attribute for attribute, _ in expected["top"]], (
            model_id,
            row_id,
        )
        assert [round(value, 6) for _, value in top] == [value for _, value in expected["top"]], (model_id, row_id)


@needs_artifacts
def test_default_row_scores_for_every_model(models, spec):
    for model_id, model in models.items():
        row = core.build_row(list(model.feature_names_in_), {}, core.default_row(spec))
        risk = model.predict_proba(row)[0, 1]
        assert 0 <= risk <= 1 and list(row.columns) == list(model.feature_names_in_), model_id


def test_build_row_keeps_column_types():
    base = pd.DataFrame([{"Age at enrollment": 20, "Admission grade": 125.7, "Course": 9500}])
    row = core.build_row(["Course", "Admission grade"], {"Admission grade": 130, "Course": 33}, base)
    assert list(row.columns) == ["Course", "Admission grade"]
    assert row.dtypes.to_dict() == {"Course": np.dtype("int64"), "Admission grade": np.dtype("float64")}
    assert row.iloc[0].to_dict() == {"Course": 33, "Admission grade": 130.0}


def test_target_status_picks_earliest_stage():
    def entry(model_id, pr_auc, recall=0.0):
        return {"model_id": model_id, "pr_auc": pr_auc, "recall": recall}

    both = [entry("A_T1_rf", 0.60), entry("A_T2_rf", 0.80, 0.70)]
    only_t2 = [entry("A_T1_rf", 0.59), entry("A_T2_rf", 0.85, 0.71)]
    neither = [entry("A_T1_rf", 0.59), entry("A_T2_rf", 0.85, 0.69)]
    assert core.target_status(both, "A")["earliest"] == "T1" and core.target_status(both, "A")["g2"]
    assert core.target_status(only_t2, "A")["earliest"] == "T2" and not core.target_status(only_t2, "A")["g2"]
    assert core.target_status(neither, "A")["earliest"] == "tidak ada"


def test_load_model_rejects_unknown_id():
    with pytest.raises(ValueError):
        core.load_model("../../etc/passwd")


@needs_artifacts
def test_every_category_in_form_spec_has_a_label(spec):
    missing = [
        (attribute, code)
        for attribute, codes in spec["categories"].items()
        for code in codes
        if labels.category(attribute, code).startswith("Kode ")
    ]
    assert missing == []
    assert set(spec["defaults"]) <= set(labels.NAMES)
    assert len(labels.NAMES) == 36


def test_unknown_code_falls_back_to_number():
    assert labels.category("Course", 12345) == "Kode 12345"
    assert labels.category("Atribut baru", 7) == "Kode 7"
