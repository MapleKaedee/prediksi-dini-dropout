from pathlib import Path

import core
import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
PAGES = ["views/dataset.py", "views/model.py", "views/prediksi.py", "views/prioritas.py"]
pytestmark = pytest.mark.skipif(
    not (core.ARTIFACTS / "manifest.json").is_file(),
    reason="artifacts/ belum ada: unduh artifacts.zip dari Release artifacts-v1 atau jalankan notebook",
)


def open_page(page):
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    return app.switch_page(page).run()


def submit(app):
    return app.button(key="pred_submit").click().run()


def test_missing_artifacts_stop_the_app_with_a_fix(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "ARTIFACTS", tmp_path)
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    assert len(app.error) == 1 and "manifest.json" in app.error[0].value and "artifacts-v1" in app.error[0].value
    assert not app.title


@pytest.mark.parametrize("page", PAGES)
def test_page_runs_with_warning(page):
    app = open_page(page)
    assert not app.exception, app.exception
    assert not app.error, [error.value for error in app.error]
    assert any(warning.value.startswith("Demo penelitian.") for warning in app.warning)


@pytest.mark.parametrize("financial", [True, False])
@pytest.mark.parametrize("stage", core.STAGES)
def test_prediction_gives_a_score(stage, financial):
    app = open_page("views/prediksi.py")
    app.segmented_control(key="pred_stage").set_value(stage)
    app.toggle(key="pred_financial").set_value(financial)
    app = submit(app.run())
    assert not app.exception and not app.error
    assert [metric.label for metric in app.metric] == ["Skor risiko", "Status"]
    assert 0 <= float(app.metric[0].value) <= 1
    assert app.metric[1].value in {"Perlu ditinjau", "Tidak ditandai"}


def test_invalid_input_shows_rules_and_no_score():
    app = open_page("views/prediksi.py")
    approved = app.number_input(key="A_T2_rf|umum|Curricular units 1st sem (approved)")
    enrolled = app.number_input(key="A_T2_rf|umum|Curricular units 1st sem (enrolled)").value
    approved.set_value(enrolled + 1)
    app = submit(app)
    assert not app.exception
    assert len(app.error) == 1 and "V1:" in app.error[0].value
    assert len(app.metric) == 0


def test_unchanged_student_matches_saved_score():
    expected = next(
        entry
        for entry in core.load_json("test_predictions.json")
        if entry["model_id"] == "A_T2_rf" and entry["flagged"] and entry["status"] == "Dropout"
    )
    app = open_page("views/prediksi.py")
    app.selectbox(key="pred_source").set_value(expected["row_id"])
    app = submit(app.run())
    assert app.metric[0].value == f"{expected['risk']:.3f}"
    assert app.metric[1].value == "Perlu ditinjau"
    assert any("Dropout" in markdown.value for markdown in app.markdown if "Status asli" in markdown.value)
