"""Halaman Dataset (APP-10)."""

import charts
import labels
import loaders
import pandas as pd
import streamlit as st

summary = loaders.json_file("dataset_summary.json")
quality, course, exploration = summary["quality"], summary["course_171"], summary["exploration"]
after = summary["status_counts"]["after_exclusion"]

st.title("Dataset")
st.markdown(
    "Sumber: Realinho dkk. (2021), *Predict students' dropout and academic success*, "
    "UCI Machine Learning Repository, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). "
    "Data berasal dari satu politeknik di Portugal dan sudah dianonimkan oleh pembuatnya."
)

kpis = st.columns(4)
kpis[0].metric("Mahasiswa dianalisis", quality["rows_after_exclusion"], border=True)
kpis[1].metric("Program studi", quality["programs_after_exclusion"], border=True)
kpis[2].metric("Proporsi dropout", f"{after['Dropout'] / sum(after.values()) * 100:.1f}%", border=True)
kpis[3].metric("Atribut masukan", summary["stage_attributes"]["T3"]["with"], border=True)

st.header("Jumlah status")
counts = (
    pd.DataFrame(summary["status_counts"])
    .rename(columns={"file": "File asli", "after_exclusion": "Setelah pengeluaran"})
    .rename_axis("Status")
)
chart, table = st.columns(2, gap="large")
with chart:
    st.markdown("**Jumlah mahasiswa per status**")
    long = counts.reset_index().melt(id_vars="Status", var_name="Data", value_name="Jumlah mahasiswa")
    st.bar_chart(long, x="Status", y="Jumlah mahasiswa", color="Data", stack=False)
with table:
    st.markdown("**Tabel jumlah status**")
    st.dataframe(pd.concat([counts, counts.sum().to_frame("Jumlah").T]))
    st.markdown(
        f"Seluruh {course['rows']} baris program **{course['name']}** (`Course` 171) dikeluarkan. "
        f"Sebanyak {course['zero_units_both_semesters']} baris di antaranya memiliki 0 mata kuliah di kedua "
        f"semester, dan {course['zero_units_graduate']} dari baris itu berlabel Graduate. Polanya menunjukkan "
        "kekosongan data, bukan perilaku mahasiswa, dan mempertahankannya dapat mengacaukan T2 dan T3. "
        f"Tersisa {quality['rows_after_exclusion']} baris dan {quality['programs_after_exclusion']} program studi."
    )
    st.caption("Target `dropout` bernilai 1 untuk Dropout, dan 0 untuk Graduate serta Enrolled.")

st.header("Atribut dan kualitas data")
stages, checks = st.columns(2, gap="large")
with stages:
    st.markdown("**Jumlah atribut per tahap**")
    stage_table = pd.DataFrame(summary["stage_attributes"]).T
    stage_table = stage_table.rename(columns={"with": "Dengan keuangan", "without": "Tanpa keuangan"})
    st.dataframe(stage_table.rename(index=labels.STAGES).rename_axis("Tahap"))
with checks:
    st.markdown("**Pemeriksaan kualitas data**")
    results = {
        "Baris pada file asli": quality["rows"],
        "Kolom pada file asli": quality["columns"],
        "Sel kosong": quality["empty_cells"],
        "Baris duplikat persis": quality["exact_duplicates"],
        "Baris setelah pengeluaran": quality["rows_after_exclusion"],
        "Program studi setelah pengeluaran": quality["programs_after_exclusion"],
        "Baris dengan rata-rata nilai 0, semester 1": quality["grade_zero_rows"]["1st"],
        "Baris dengan rata-rata nilai 0, semester 2": quality["grade_zero_rows"]["2nd"],
        "Pelanggaran aturan konsistensi": quality["consistency_violations"],
    }
    st.dataframe(pd.DataFrame({"Pemeriksaan": results.keys(), "Hasil": results.values()}), hide_index=True)
    st.caption(
        "Rata-rata nilai 0 terjadi tepat pada baris tanpa mata kuliah lulus, jadi nilainya tidak dianggap kosong."
    )

st.header("Proporsi dropout per atribut keuangan")
financial = summary["financial_dropout_rates"]
rates = pd.DataFrame(financial["rows"])
rates["Atribut"] = rates["attribute"].map(labels.name)
rates["Nilai"] = [labels.category(a, c) for a, c in zip(rates["attribute"], rates["category"])]
rates["Proporsi dropout (%)"] = (rates["dropout_rate"] * 100).round(1)
chart, table = st.columns(2, gap="large")
with chart:
    st.markdown("**Proporsi dropout (%)**")
    st.altair_chart(charts.bars(rates, "Atribut", "Proporsi dropout (%)", color="Nilai", grouped=True))
with table:
    st.markdown("**Tabel proporsi dropout**")
    st.dataframe(
        rates[["Atribut", "Nilai", "Proporsi dropout (%)", "n", "Dropout"]].rename(
            columns={"n": "Jumlah mahasiswa", "Dropout": "Jumlah dropout"}
        ),
        hide_index=True,
    )
    st.caption(
        f"Dihitung dari seluruh {financial['n_rows']} baris setelah pengeluaran, sama dengan proposal Tabel 5. "
        "Angka ini deskriptif dan tidak menunjukkan hubungan sebab akibat."
    )

st.header("Eksplorasi: korelasi dengan dropout")
st.caption(
    f"**Data latih saja**, {exploration['n_rows']} baris dengan {exploration['dropout_rate'] * 100:.1f}% dropout. "
    "Data uji tidak dipakai di sini. Nilai r adalah korelasi Pearson antara atribut numerik atau biner dan target."
)
correlations = pd.DataFrame(exploration["target_correlations"])
correlations["Atribut"] = correlations["attribute"].map(labels.name)
correlations = correlations.rename(columns={"r": "r dengan dropout", "stage": "Tersedia sejak"})
chart = charts.bars(correlations, "Atribut", "r dengan dropout", color="Tersedia sejak", colors=charts.STAGE_COLORS)
left, right = st.columns(2, gap="large")
with left:
    st.markdown("**Korelasi tiap atribut dengan dropout**")
    st.altair_chart(chart)
with right:
    st.markdown("**Tabel korelasi**")
    st.dataframe(
        correlations[["Atribut", "r dengan dropout", "Tersedia sejak"]],
        hide_index=True,
        height=chart.height,
        column_config={"r dengan dropout": st.column_config.NumberColumn(format="%.3f")},
    )
