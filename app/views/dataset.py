"""Halaman Dataset (APP-10)."""

import labels
import loaders
import pandas as pd
import streamlit as st

summary = loaders.json_file("dataset_summary.json")
quality, course, exploration = summary["quality"], summary["course_171"], summary["exploration"]

st.title("Dataset")
st.markdown(
    "Sumber: Realinho dkk. (2021), *Predict students' dropout and academic success*, "
    "UCI Machine Learning Repository, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). "
    "Data berasal dari satu politeknik di Portugal dan sudah dianonimkan oleh pembuatnya."
)

st.header("Jumlah status")
counts = pd.DataFrame(summary["status_counts"]).rename(
    columns={"file": "File asli", "after_exclusion": "Setelah Course 171 dikeluarkan"}
)
counts.loc["Jumlah"] = counts.sum()
st.dataframe(counts.rename_axis("Status"))
st.markdown(
    f"Seluruh {course['rows']} baris program **{course['name']}** (`Course` 171) dikeluarkan. "
    f"Sebanyak {course['zero_units_both_semesters']} baris di antaranya memiliki 0 mata kuliah di kedua semester, "
    f"dan {course['zero_units_graduate']} dari baris itu berlabel Graduate. Polanya menunjukkan kekosongan data, "
    "bukan perilaku mahasiswa, dan mempertahankannya dapat mengacaukan T2 dan T3. "
    f"Tersisa {quality['rows_after_exclusion']} baris dan {quality['programs_after_exclusion']} program studi."
)
st.markdown("Target `dropout` bernilai 1 untuk Dropout, dan 0 untuk Graduate serta Enrolled.")

st.header("Atribut per tahap")
stages = pd.DataFrame(summary["stage_attributes"]).T.rename(
    columns={"with": "Dengan keuangan", "without": "Tanpa keuangan"}
)
st.dataframe(stages.rename(index=labels.STAGES).rename_axis("Tahap"))

st.header("Pemeriksaan kualitas data")
checks = {
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
st.dataframe(pd.DataFrame({"Pemeriksaan": checks.keys(), "Hasil": checks.values()}), hide_index=True)
st.caption("Rata-rata nilai 0 terjadi tepat pada baris tanpa mata kuliah lulus, jadi nilainya tidak dianggap kosong.")

st.header("Proporsi dropout per atribut keuangan")
financial = summary["financial_dropout_rates"]
rates = pd.DataFrame(financial["rows"])
rates["Atribut"] = rates["attribute"].map(labels.name)
rates["Nilai"] = [labels.category(a, c) for a, c in zip(rates["attribute"], rates["category"])]
rates["Proporsi dropout (%)"] = (rates["dropout_rate"] * 100).round(1)
# Nama atribut panjang terpotong di sumbu, jadi nilai Ya/Tidak dibedakan dengan warna.
st.bar_chart(rates, x="Atribut", y="Proporsi dropout (%)", color="Nilai", horizontal=True, stack=False)
st.dataframe(
    rates[["Atribut", "Nilai", "n", "Dropout", "Proporsi dropout (%)"]].rename(
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
st.bar_chart(correlations, x="Atribut", y="r dengan dropout", color="Tersedia sejak", horizontal=True, sort=False)
st.dataframe(correlations[["Atribut", "Tersedia sejak", "r dengan dropout"]], hide_index=True)
