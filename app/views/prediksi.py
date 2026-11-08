"""Halaman Prediksi (APP-30 sampai APP-36). Satu-satunya halaman yang menghitung skor secara langsung."""

import core
import labels
import loaders
import pandas as pd
import streamlit as st

GENERAL = "umum"
spec = loaders.json_file("form_spec.json")
rows = loaders.test_rows()

st.title("Prediksi")
st.markdown(
    "Isi profil mahasiswa untuk melihat skor risiko dari Random Forest. Model memakai bobot kelas, "
    "jadi skor risiko bukan peluang terkalibrasi."
)

left, middle, right = st.columns(3)
stage = left.radio("Tahap", core.STAGES, index=1, format_func=labels.STAGES.get, key="pred_stage")
financial = middle.toggle("Pakai atribut keuangan", value=True, key="pred_financial")
source = right.selectbox(
    "Sumber isian",
    [GENERAL, *rows.index],
    format_func=lambda option: "Nilai umum" if option == GENERAL else f"Mahasiswa data uji, row_id {option}",
    key="pred_source",
)

model_id = core.model_id(stage, financial)
model = loaders.model(model_id)
features = list(model.feature_names_in_)
shown = spec["models"][model_id]
base = core.default_row(spec) if source == GENERAL else rows.loc[[source]]

hidden_source = (
    "nilai umum dari data latih (median untuk numerik, modus untuk nominal dan biner)"
    if source == GENERAL
    else f"mahasiswa data uji dengan row_id {source}"
)
st.caption(
    f"Model `{model_id}` memakai {len(features)} atribut. Form menampilkan {len(shown)} atribut, dan "
    f"{len(features) - len(shown)} atribut tersembunyi mengikuti {hidden_source}."
)
sensitive = [labels.name(attribute) for attribute in shown if attribute in core.SENSITIVE]
if sensitive:
    st.info(
        f"Form memuat atribut sensitif: {', '.join(sensitive)}. Penggunaannya perlu diawasi, "
        "dan atribut ini tidak boleh menjadi dasar perlakuan yang merugikan mahasiswa."
    )

values = {}
with st.form(f"form_{model_id}_{source}"):
    columns = st.columns(3)
    for position, attribute in enumerate(shown):
        # Kunci memuat tahap, skenario, dan sumber, jadi mengganti pilihan mengisi ulang form (APP-30).
        key = f"{model_id}|{source}|{attribute}"
        current = base[attribute].iloc[0]
        with columns[position % 3]:
            if attribute in spec["categories"]:
                options = spec["categories"][attribute]
                values[attribute] = st.selectbox(
                    labels.name(attribute),
                    options,
                    index=options.index(int(current)),
                    format_func=lambda code, attribute=attribute: labels.category(attribute, code),
                    key=key,
                    help=attribute,
                )
            elif core.is_integer(spec, attribute):
                low, high = spec["ranges"][attribute]
                values[attribute] = st.number_input(
                    labels.name(attribute), low, high, int(current), step=1, key=key, help=attribute
                )
            else:
                low, high = spec["ranges"][attribute]
                values[attribute] = st.number_input(
                    labels.name(attribute),
                    float(low),
                    float(high),
                    float(current),
                    step=0.1,
                    format="%.3f",
                    key=key,
                    help=attribute,
                )
    submitted = st.form_submit_button("Hitung skor risiko", type="primary", key="pred_submit")

if submitted:
    row = core.build_row(features, values, base)
    problems = core.validate(row.iloc[0].to_dict(), stage, spec["grade_nonzero_range"])
    if problems:
        st.error("Skor tidak dihitung karena isian tidak konsisten.\n\n" + "\n\n".join(f"- {p}" for p in problems))
        st.stop()

    risk, top = core.score_and_explain(model, loaders.explainer(model_id), row)
    flagged = risk >= core.THRESHOLD
    score, status = st.columns(2)
    score.metric("Skor risiko", f"{risk:.3f}")
    status.metric("Status", "Perlu ditinjau" if flagged else "Tidak ditandai")
    st.caption(f'Mahasiswa ditandai "Perlu ditinjau" jika skor risiko ≥ {core.THRESHOLD}.')

    unchanged = source != GENERAL and all(values[a] == base[a].iloc[0] for a in shown)
    if unchanged:
        st.markdown(f"Status asli mahasiswa ini pada data historis: **{base['Target'].iloc[0]}**.")

    st.subheader("Lima atribut dengan pengaruh terbesar")
    st.dataframe(
        pd.DataFrame(
            {
                "Atribut": [labels.name(attribute) for attribute, _ in top],
                "Nilai input": [labels.value_text(attribute, row[attribute].iloc[0]) for attribute, _ in top],
                "Kontribusi SHAP": [contribution for _, contribution in top],
                "Arah": [labels.direction(contribution) for _, contribution in top],
            }
        ),
        hide_index=True,
        column_config={"Kontribusi SHAP": st.column_config.NumberColumn(format="%+.4f")},
    )
    st.caption("Kontribusi SHAP menunjukkan pola yang dipakai model, bukan sebab mahasiswa keluar.")
