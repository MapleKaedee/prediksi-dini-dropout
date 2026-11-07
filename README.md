# Prediksi Dini Risiko Dropout Mahasiswa

Penelitian mata kuliah Penambangan Data tentang prediksi risiko dropout pada tiga tahap studi: saat masuk (T1), akhir semester 1 (T2), dan akhir semester 2 (T3). Random Forest menjadi algoritma utama, dengan Regresi Logistik dan XGBoost sebagai pembanding. Penelitian ini juga mengukur seberapa jauh prediksi bergantung pada atribut keuangan.

Hasilnya menunjukkan pola prediktif, bukan hubungan sebab akibat. Data berasal dari satu institusi di Portugal, jadi hasilnya belum divalidasi untuk kampus lain.

## Status

`notebooks/dropout_experiments.ipynb` saat ini mencakup pemeriksaan data, pengeluaran `Course` 171, pembagian data, eksplorasi pada data latih, encoder, baseline Regresi Logistik, serta 24 model skenario A, B, C, dan D beserta metriknya pada data uji. Bootstrap, SHAP, artefak final, dan aplikasi Streamlit menyusul. Langkah mengunduh artefak dan menjalankan aplikasi akan ditambahkan di sini setelah keduanya tersedia.

## Menjalankan dari clone bersih

Langkah ini membutuhkan Nix dengan fitur `nix-command` dan `flakes`. Rincian lingkungan ada di [env.md](env.md).

```sh
git clone https://github.com/MapleKaedee/prediksi-dini-dropout.git
cd prediksi-dini-dropout
nix develop
mkdir -p data
curl -L -o data/uci.zip 'https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip'
unzip -p data/uci.zip data.csv > data/data.csv
run-notebook
```

`run-notebook` menimpa keluaran notebook dan menulis hasilnya ke `artifacts/`. Notebook berhenti dengan pesan jelas jika hash `data.csv` berbeda.

## Dataset

Realinho, V., Vieira Martins, M., Machado, J., & Baptista, L. (2021). _Predict students' dropout and academic success_ [Data set]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5MC89>

Dataset ini berlisensi [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Data tidak disimpan di repo ini.

## Lisensi

Kode berlisensi [Apache-2.0](LICENSE). Lisensi ini hanya berlaku untuk kode, dan data tetap mengikuti lisensi CC BY 4.0 milik pembuatnya.
