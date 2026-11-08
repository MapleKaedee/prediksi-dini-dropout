"""Konfigurasi halaman, pemeriksaan artefak, peringatan, dan navigasi."""

from pathlib import Path

import core
import streamlit as st

WARNING = (
    "Demo penelitian. Model dilatih dengan data satu institusi di Portugal dan belum divalidasi untuk kampus lain. "
    "Skor ini bukan dasar sanksi atau keputusan otomatis, dan harus ditinjau manusia."
)

st.set_page_config(page_title="Prediksi Dini Risiko Dropout", page_icon=":material/school:", layout="wide")
st.html(Path(__file__).parent / "style.css")

problems = core.check_artifacts()
if problems:
    st.error("Aplikasi tidak dapat dibuka karena artefak bermasalah.\n\n" + "\n\n".join(f"- {p}" for p in problems))
    st.stop()

page = st.navigation(
    {
        "Menu utama": [
            st.Page("views/dataset.py", title="Dataset", icon=":material/database:", default=True),
            st.Page("views/model.py", title="Model", icon=":material/monitoring:"),
            st.Page("views/prediksi.py", title="Prediksi", icon=":material/person_search:"),
            st.Page("views/prioritas.py", title="Daftar Prioritas", icon=":material/format_list_numbered:"),
        ]
    }
)
st.warning(WARNING, icon=":material/warning:")
page.run()
