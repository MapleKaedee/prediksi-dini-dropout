"""Halaman Model (APP-20 sampai APP-23). Semua angka dibaca dari artefak."""

import json

import core
import labels
import loaders
import pandas as pd
import streamlit as st

metrics = loaders.json_file("metrics.json")
by_id = {entry["model_id"]: entry for entry in metrics}
comparisons = pd.DataFrame(loaders.json_file("comparisons.json"))
shap_global = pd.DataFrame(loaders.json_file("shap_global.json"))
ALGORITHM_ORDER = list(labels.ALGORITHMS)
YES_NO = {True: "Ya", False: "Tidak"}


def three_decimals(columns):
    return {column: st.column_config.NumberColumn(format="%.3f") for column in columns}


def algorithm(model_id):
    return model_id.split("_")[2]


def comparison_table(frame, first="Perbandingan"):
    return pd.DataFrame(
        {
            first: [f"{left} − {right}" for left, right in zip(frame["left"], frame["right"])],
            "Selisih": frame["difference"],
            "IK 95% bawah": frame["ci_low"],
            "IK 95% atas": frame["ci_high"],
            "Bermakna": frame["meaningful"].map(YES_NO),
        }
    )


DIFFERENCE_COLUMNS = three_decimals(["Selisih", "IK 95% bawah", "IK 95% atas"])
reference = by_id["A_T1_rf"]
positives = reference["tp"] + reference["fn"]
resamples = int(comparisons.loc[comparisons["question"] != "D", "resamples"].iloc[0])

st.title("Model")
st.markdown(
    f"Semua metrik dihitung pada {reference['n_test']} mahasiswa data uji, setelah parameter ditetapkan dari data latih. "
    f"Mahasiswa ditandai jika skor risiko ≥ {core.THRESHOLD}. PR-AUC adalah metrik utama, dengan patokan terendah "
    f"{positives / reference['n_test']:.3f}, yaitu proporsi dropout data uji ({positives} dari {reference['n_test']}). "
    f"Selisih disebut bermakna jika interval kepercayaan 95% dari bootstrap berpasangan ({resamples} ulangan) "
    f"tidak memuat 0 dan nilai absolutnya minimal {core.MIN_DIFFERENCE}."
)

st.header("RM1: performa per tahap")
scenario_a = sorted(
    (entry for entry in metrics if entry["scenario"] == "A"),
    key=lambda entry: (entry["stage"], ALGORITHM_ORDER.index(entry["algorithm"])),
)
rm1 = pd.DataFrame(
    {
        "Tahap": [entry["stage"] for entry in scenario_a],
        "Algoritma": [labels.ALGORITHMS[entry["algorithm"]] for entry in scenario_a],
        "PR-AUC": [entry["pr_auc"] for entry in scenario_a],
        "Recall": [entry["recall"] for entry in scenario_a],
        "Presisi": [entry["precision"] for entry in scenario_a],
        "F1": [entry["f1"] for entry in scenario_a],
        "ROC-AUC": [entry["roc_auc"] for entry in scenario_a],
        "PR-AUC CV latih": [entry["cv_pr_auc"] for entry in scenario_a],
    }
)
st.dataframe(
    rm1,
    hide_index=True,
    column_config=three_decimals(["PR-AUC", "Recall", "Presisi", "F1", "ROC-AUC", "PR-AUC CV latih"]),
)
st.bar_chart(rm1, x="Tahap", y="PR-AUC", color="Algoritma", stack=False)
st.caption("Grafik memakai kolom PR-AUC pada tabel di atas. Skenario A memakai atribut keuangan.")

rm1_comparisons = comparisons[comparisons["question"] == "RM1"]
st.subheader("Random Forest dibanding algoritma lain")
st.dataframe(
    comparison_table(rm1_comparisons[~rm1_comparisons["stage"].str.contains("-")]),
    hide_index=True,
    column_config=DIFFERENCE_COLUMNS,
)
st.subheader("Tahap berikutnya dibanding tahap sebelumnya")
st.dataframe(
    comparison_table(rm1_comparisons[rm1_comparisons["stage"].str.contains("-")]),
    hide_index=True,
    column_config=DIFFERENCE_COLUMNS,
)

st.subheader("Target G2 dan tahap paling dini")
statuses = [core.target_status(metrics, scenario) for scenario in "AB"]
official = statuses[0]
st.markdown(
    f"Random Forest skenario A: target G2 **{'tercapai' if official['g2'] else 'tidak tercapai'}**. "
    f"Tahap paling dini yang memenuhi target: **{official['earliest']}**."
)
st.dataframe(
    pd.DataFrame(
        {
            "Skenario": [status["scenario"] for status in statuses],
            "PR-AUC T1": [status["t1_pr_auc"] for status in statuses],
            f"Target T1 (PR-AUC ≥ {core.G2_T1_PR_AUC:.2f})": [YES_NO[status["t1_met"]] for status in statuses],
            "PR-AUC T2": [status["t2_pr_auc"] for status in statuses],
            "Recall T2": [status["t2_recall"] for status in statuses],
            f"Target T2 (PR-AUC ≥ {core.G2_T2_PR_AUC:.2f}, recall ≥ {core.G2_T2_RECALL:.2f})": [
                YES_NO[status["t2_met"]] for status in statuses
            ],
            "G2 tercapai": [YES_NO[status["g2"]] for status in statuses],
            "Tahap paling dini": [status["earliest"] for status in statuses],
        }
    ),
    hide_index=True,
    column_config=three_decimals(["PR-AUC T1", "PR-AUC T2", "Recall T2"]),
)
st.caption(
    "Status G2 dinilai pada skenario A, dan skenario B hanya pembanding. Proposal tidak menyebut skenarionya, "
    "dan penetapan ini dilakukan setelah hasil data uji terlihat, sehingga dicatat di laporan."
)

st.header("RM2: ketergantungan pada atribut keuangan")
rm2 = comparisons[(comparisons["question"] == "RM2") & comparisons["right"].str.startswith("B_")].copy()
rm2["order"] = [(ALGORITHM_ORDER.index(algorithm(left)), stage) for left, stage in zip(rm2["left"], rm2["stage"])]
rm2 = rm2.sort_values("order")
rm2_table = pd.DataFrame(
    {
        "Algoritma": [labels.ALGORITHMS[algorithm(left)] for left in rm2["left"]],
        "Tahap": rm2["stage"].to_list(),
        "PR-AUC dengan keuangan (A)": [by_id[left]["pr_auc"] for left in rm2["left"]],
        "PR-AUC tanpa keuangan (B)": [by_id[right]["pr_auc"] for right in rm2["right"]],
    }
)
rm2_table = pd.concat([rm2_table, comparison_table(rm2).drop(columns="Perbandingan").reset_index(drop=True)], axis=1)
st.dataframe(
    rm2_table,
    hide_index=True,
    column_config=DIFFERENCE_COLUMNS | three_decimals(["PR-AUC dengan keuangan (A)", "PR-AUC tanpa keuangan (B)"]),
)
st.caption("Selisih adalah A dikurangi B. Selisih positif berarti PR-AUC turun saat atribut keuangan dihapus.")

st.subheader("Rincian T1: menghapus satu atribut keuangan (skenario C)")
scenario_c = comparisons[comparisons["right"].str.startswith("C_")]
c_table = pd.DataFrame(
    {
        "Atribut yang dihapus": [labels.name(by_id[right]["removed"]) for right in scenario_c["right"]],
        "PR-AUC": [by_id[right]["pr_auc"] for right in scenario_c["right"]],
    }
)
c_table = pd.concat([c_table, comparison_table(scenario_c).drop(columns="Perbandingan").reset_index(drop=True)], axis=1)
st.dataframe(c_table, hide_index=True, column_config=DIFFERENCE_COLUMNS | three_decimals(["PR-AUC"]))
st.caption(
    f"Selisih adalah PR-AUC A_T1_rf ({by_id['A_T1_rf']['pr_auc']:.3f}) dikurangi PR-AUC model tanpa atribut itu."
)

st.header("RM3: atribut paling berpengaruh")
st.markdown(
    "Lima atribut dengan rata-rata nilai absolut SHAP terbesar pada data uji, untuk Random Forest. "
    "Nilai kolom one-hot dijumlahkan ke atribut asalnya per mahasiswa sebelum dirata-ratakan."
)
for stage in core.STAGES:
    tops = {
        financial: shap_global[
            (shap_global["model_id"] == core.model_id(stage, financial)) & (shap_global["rank"] <= 5)
        ]
        .sort_values("rank")
        .reset_index(drop=True)
        for financial in (True, False)
    }
    st.markdown(f"**{labels.STAGES[stage]}**")
    st.dataframe(
        pd.DataFrame(
            {
                "Peringkat": tops[True]["rank"],
                "Dengan keuangan (A)": tops[True]["attribute"].map(labels.name),
                "Rata-rata |SHAP| A": tops[True]["mean_abs_shap"],
                "Tanpa keuangan (B)": tops[False]["attribute"].map(labels.name),
                "Rata-rata |SHAP| B": tops[False]["mean_abs_shap"],
            }
        ),
        hide_index=True,
        column_config=three_decimals(["Rata-rata |SHAP| A", "Rata-rata |SHAP| B"]),
    )

st.header("Pembanding tanpa Enrolled (skenario D)")
scenario_d = comparisons[comparisons["question"] == "D"]
d_reference = by_id[scenario_d["left"].iloc[0]]
st.dataframe(
    pd.DataFrame(
        {
            "Tahap": scenario_d["stage"],
            "ROC-AUC D": [by_id[left]["roc_auc"] for left in scenario_d["left"]],
            "ROC-AUC A": [by_id[right]["roc_auc"] for right in scenario_d["right"]],
            "Selisih D − A": scenario_d["difference"],
        }
    ),
    hide_index=True,
    column_config=three_decimals(["ROC-AUC D", "ROC-AUC A", "Selisih D − A"]),
)
st.caption(
    f"Skenario D membuang mahasiswa Enrolled dari data latih dan uji ({d_reference['n_test']} baris uji, "
    f"{(d_reference['tp'] + d_reference['fn']) / d_reference['n_test'] * 100:.1f}% dropout), seperti banyak penelitian "
    "terdahulu. Baris ujinya berbeda dari skenario A, jadi selisih ini tidak di-bootstrap dan hanya menjadi pembanding "
    "dengan literatur."
)

with st.expander(f"Parameter terbaik tiap model ({len(metrics)} model)"):
    st.dataframe(
        pd.DataFrame(
            {
                "Model": [entry["model_id"] for entry in metrics],
                "PR-AUC CV latih": [entry["cv_pr_auc"] for entry in metrics],
                "Parameter terbaik": [json.dumps(entry["best_params"]) for entry in metrics],
            }
        ),
        hide_index=True,
        column_config=three_decimals(["PR-AUC CV latih"]),
    )
    st.caption("Parameter dipilih dengan RandomizedSearchCV dan validasi silang 5 lipatan pada data latih saja.")

st.header("Keterbatasan")
st.markdown(
    """
- **Satu institusi.** Data berasal dari satu politeknik di Portugal, sehingga hasilnya belum tentu berlaku di Indonesia.
- **Tanpa penanda waktu.** Waktu pencatatan atribut keuangan tidak dirinci. Jika sebagian dicatat setelah kuliah
  berjalan, skor T1 yang memakainya terlalu optimistis. Skenario B memberi batas bawahnya.
- **T3 mungkin terlalu optimistis.** Martins dkk. (2023) membuang mahasiswa yang sudah keluar pada tahap ini, sedangkan
  file publik tidak memiliki tanggal keluar. Karena itu, fokus utama ada pada T1 dan T2.
- **Definisi target.** Mahasiswa Enrolled masih mungkin keluar setelah masa studi normal.
- **Program yang dikeluarkan.** Hasil tidak mencakup `Course` 171.
- **Satu pembagian data.** Interval kepercayaan bootstrap menggambarkan ketidakpastian data uji, tetapi bukan variasi
  antarpembagian data.
- **Pola prediktif.** Hasil menunjukkan pola prediktif, bukan hubungan sebab akibat. Model memakai bobot kelas, jadi
  skornya bukan peluang terkalibrasi.
"""
)
