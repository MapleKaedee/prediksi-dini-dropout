"""Halaman Daftar Prioritas (APP-40 sampai APP-43). Angka dibaca dari `test_predictions.json`."""

import core
import labels
import loaders
import pandas as pd
import streamlit as st

rows = loaders.test_rows()

st.title("Daftar Prioritas")
st.markdown(
    "Daftar ini hanya memuat mahasiswa data uji, karena baris latih sudah dilihat model dan akan membuatnya tampak "
    "terlalu akurat. Status asli sudah diketahui karena ini data historis, jadi daftar ini menunjukkan cara kerja "
    "model, bukan daftar mahasiswa sungguhan."
)

left, right = st.columns(2)
stage = left.radio("Tahap", core.STAGES, index=1, format_func=labels.STAGES.get, key="prio_stage")
financial = right.toggle("Pakai atribut keuangan", value=True, key="prio_financial")
model_id = core.model_id(stage, financial)
table = loaders.priority(model_id)
summary = core.flag_summary(table)

flagged, precision, recall = st.columns(3)
flagged.metric("Perlu ditinjau", f"{summary['flagged']} dari {len(table)}")
precision.metric("Presisi", f"{summary['precision']:.3f}")
recall.metric("Recall", f"{summary['recall']:.3f}")
st.caption(
    f"Model `{model_id}`. Mahasiswa ditandai jika skor risiko ≥ {core.THRESHOLD}. Presisi adalah bagian mahasiswa "
    "ditandai yang benar-benar dropout, dan recall adalah bagian mahasiswa dropout yang ditandai."
)

st.dataframe(
    pd.DataFrame(
        {
            "Peringkat": table["rank"],
            "row_id": table["row_id"],
            "Skor risiko": table["risk"],
            "Penandaan": table["flagged"].map({True: "Perlu ditinjau", False: "Tidak ditandai"}),
            "Status asli": table["status"],
            "Atribut pengaruh utama": [labels.name(top[0][0]) for top in table["top"]],
        }
    ),
    hide_index=True,
    column_config={"Skor risiko": st.column_config.NumberColumn(format="%.3f")},
)

st.subheader("Rincian satu mahasiswa")
ranks = dict(zip(table["row_id"], table["rank"]))
chosen = st.selectbox(
    "row_id", table["row_id"], format_func=lambda row_id: f"{row_id} (peringkat {ranks[row_id]})", key="prio_row"
)
entry = table[table["row_id"] == chosen].iloc[0]
st.markdown(
    f"Skor risiko **{entry['risk']:.3f}**, "
    f"{'**Perlu ditinjau**' if entry['flagged'] else '**Tidak ditandai**'}, status asli **{entry['status']}**."
)
st.dataframe(
    pd.DataFrame(
        {
            "Atribut": [labels.name(attribute) for attribute, _ in entry["top"]],
            "Nilai": [labels.value_text(attribute, rows.loc[chosen, attribute]) for attribute, _ in entry["top"]],
            "Kontribusi SHAP": [contribution for _, contribution in entry["top"]],
            "Arah": [labels.direction(contribution) for _, contribution in entry["top"]],
        }
    ),
    hide_index=True,
    column_config={"Kontribusi SHAP": st.column_config.NumberColumn(format="%+.4f")},
)
