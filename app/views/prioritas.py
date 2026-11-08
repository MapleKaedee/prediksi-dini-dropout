"""Halaman Daftar Prioritas (APP-40 sampai APP-43). Angka dibaca dari `test_predictions.json`."""

import charts
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


with st.container(border=True):
    left, right = st.columns([3, 2], vertical_alignment="center")
    stage = left.segmented_control(
        "Tahap", core.STAGES, default="T2", required=True, format_func=labels.STAGES.get, key="prio_stage"
    )
    financial = right.toggle("Pakai atribut keuangan", value=True, key="prio_financial")
model_id = core.model_id(stage, financial)
table = loaders.priority(model_id)
summary = core.flag_summary(table)

kpis = st.columns(4)
kpis[0].metric("Perlu ditinjau", f"{summary['flagged']} dari {len(table)}", border=True)
kpis[1].metric("Presisi", f"{summary['precision']:.3f}", border=True)
kpis[2].metric("Recall", f"{summary['recall']:.3f}", border=True)
kpis[3].metric("Dropout sebenarnya", int((table["status"] == "Dropout").sum()), border=True)
st.caption(
    f"Model `{model_id}`. Mahasiswa ditandai jika skor risiko ≥ {core.THRESHOLD}. Presisi adalah bagian mahasiswa "
    "ditandai yang benar-benar dropout, dan recall adalah bagian mahasiswa dropout yang ditandai."
)

histogram = core.risk_histogram(table)
chart, counts = st.columns(2, gap="large")
with chart:
    st.markdown("**Sebaran skor risiko menurut status asli**")
    st.bar_chart(
        histogram.reset_index().astype({"Rentang skor": str}),
        x="Rentang skor",
        y=list(charts.STATUS_COLORS),
        color=list(charts.STATUS_COLORS.values()),
        x_label="Rentang skor",
        y_label="Jumlah mahasiswa",
    )
with counts:
    st.markdown("**Tabel sebaran skor**")
    st.dataframe(histogram)
    st.caption("Rentang 0.5–0.6 ke atas adalah mahasiswa yang ditandai.")

st.subheader("Daftar mahasiswa data uji")
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
    column_config={
        "Skor risiko": st.column_config.ProgressColumn(format="%.3f", min_value=0.0, max_value=1.0),
    },
)

st.subheader("Rincian satu mahasiswa")
ranks = dict(zip(table["row_id"], table["rank"]))
chosen = st.selectbox(
    "row_id", table["row_id"], format_func=lambda row_id: f"{row_id} (peringkat {ranks[row_id]})", key="prio_row"
)
entry = table[table["row_id"] == chosen].iloc[0]
factors = pd.DataFrame(
    {
        "Atribut": [labels.name(attribute) for attribute, _ in entry["top"]],
        "Nilai": [labels.value_text(attribute, rows.loc[chosen, attribute]) for attribute, _ in entry["top"]],
        "Kontribusi SHAP": [contribution for _, contribution in entry["top"]],
        "Arah": [labels.direction(contribution) for _, contribution in entry["top"]],
    }
)
detail, chart = st.columns([1, 2], gap="large")
with detail:
    st.metric("Skor risiko", f"{entry['risk']:.3f}", border=True)
    st.metric("Penandaan", "Perlu ditinjau" if entry["flagged"] else "Tidak ditandai", border=True)
    st.markdown(f"Status asli: **{entry['status']}**.")
with chart:
    st.markdown("**Lima atribut dengan pengaruh terbesar**")
    st.altair_chart(charts.bars(factors, "Atribut", "Kontribusi SHAP", color="Arah", colors=charts.RISK_COLORS))
st.dataframe(factors, hide_index=True, column_config={"Kontribusi SHAP": st.column_config.NumberColumn(format="%+.4f")})
