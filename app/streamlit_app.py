"""Konfigurasi halaman, pemeriksaan artefak, peringatan, dan navigasi."""

import core
import streamlit as st

WARNING = (
    "Demo penelitian. Model dilatih dengan data satu institusi di Portugal dan belum divalidasi untuk kampus lain. "
    "Skor ini bukan dasar sanksi atau keputusan otomatis, dan harus ditinjau manusia."
)

st.set_page_config(page_title="Prediksi Dini Risiko Dropout", layout="wide")

problems = core.check_artifacts()
if problems:
    st.error("Aplikasi tidak dapat dibuka karena artefak bermasalah.\n\n" + "\n\n".join(f"- {p}" for p in problems))
    st.stop()

page = st.navigation(
    [
        st.Page("views/dataset.py", title="Dataset", default=True),
        st.Page("views/model.py", title="Model"),
        st.Page("views/prediksi.py", title="Prediksi"),
        st.Page("views/prioritas.py", title="Daftar Prioritas"),
    ]
)
st.warning(WARNING)
page.run()
