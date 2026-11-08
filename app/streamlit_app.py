"""Konfigurasi halaman, pemeriksaan artefak, peringatan, dan navigasi."""

import core
import streamlit as st
from streamlit_option_menu import option_menu

WARNING = (
    "Demo penelitian. Model dilatih dengan data satu institusi di Portugal dan belum divalidasi untuk kampus lain. "
    "Skor ini bukan dasar sanksi atau keputusan otomatis, dan harus ditinjau manusia."
)
# Halaman dan ikon Bootstrap untuk menu sidebar.
PAGES = {
    "Dataset": ("views/dataset.py", "database"),
    "Model": ("views/model.py", "graph-up"),
    "Prediksi": ("views/prediksi.py", "person-bounding-box"),
    "Daftar Prioritas": ("views/prioritas.py", "list-ol"),
}

st.set_page_config(page_title="Prediksi Dini Risiko Dropout", page_icon=":material/school:", layout="wide")

problems = core.check_artifacts()
if problems:
    st.error("Aplikasi tidak dapat dibuka karena artefak bermasalah.\n\n" + "\n\n".join(f"- {p}" for p in problems))
    st.stop()

pages = {
    title: st.Page(path, title=title, default=index == 0) for index, (title, (path, _)) in enumerate(PAGES.items())
}
page = st.navigation(list(pages.values()), position="hidden")
titles = list(pages)
with st.sidebar:
    # Tanpa key, menu dibuat ulang tiap halaman dan selalu mulai dari halaman yang sedang dibuka,
    # jadi tombol Back di browser tidak memantul ke pilihan menu sebelumnya.
    chosen = option_menu(
        "Menu utama",
        titles,
        icons=[icon for _, icon in PAGES.values()],
        menu_icon="cast",
        default_index=titles.index(page.title),
    )
if chosen != page.title:
    st.switch_page(pages[chosen])

st.warning(WARNING, icon=":material/warning:")
page.run()
