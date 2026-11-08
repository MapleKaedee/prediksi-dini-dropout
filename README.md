# Prediksi Dini Risiko Dropout Mahasiswa

Penelitian mata kuliah Penambangan Data tentang prediksi risiko dropout pada tiga tahap studi: saat masuk (T1), akhir semester 1 (T2), dan akhir semester 2 (T3). Random Forest menjadi algoritma utama, dengan Regresi Logistik dan XGBoost sebagai pembanding. Penelitian ini juga mengukur seberapa jauh prediksi bergantung pada atribut keuangan.

Hasilnya menunjukkan pola prediktif, bukan hubungan sebab akibat. Data berasal dari satu institusi di Portugal, jadi hasilnya belum divalidasi untuk kampus lain.

## Status

`notebooks/dropout_experiments.ipynb` mencakup pemeriksaan data, pengeluaran `Course` 171, pembagian data, eksplorasi pada data latih, encoder, 24 model skenario A, B, C, dan D beserta metriknya pada data uji, bootstrap berpasangan, SHAP, jawaban rumusan masalah, dan ekspor artefak. Artefak final dari jalan di Kaggle tersedia di GitHub Release `artifacts-v1`.

Aplikasi Streamlit di `app/` membaca artefak itu dan memiliki empat halaman: Dataset, Model, Prediksi, dan Daftar Prioritas. Aplikasi tidak melatih model, dan hanya halaman Prediksi yang menghitung skor secara langsung.

## Menjalankan dari clone bersih

Langkah ini membutuhkan Nix dengan fitur `nix-command` dan `flakes`. Rincian lingkungan ada di [env.md](env.md).

```sh
git clone https://github.com/MapleKaedee/prediksi-dini-dropout.git
cd prediksi-dini-dropout
nix develop
curl -L -o artifacts.zip https://github.com/MapleKaedee/prediksi-dini-dropout/releases/download/artifacts-v1/artifacts.zip
unzip -q artifacts.zip -d artifacts
run-tests
app
```

`app` membuka aplikasi di `http://127.0.0.1:8501`, hanya dari laptop sendiri. Aplikasi menolak berjalan jika artefak tidak lengkap, atau jika versi `scikit-learn` berbeda dari versi saat model dibuat, jadi jalankan dari shell Nix proyek.

## Menjalankan ulang eksperimen

`data/` hanya dibutuhkan untuk menjalankan ulang notebook.

```sh
mkdir -p data
curl -L -o data/uci.zip 'https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip'
unzip -p data/uci.zip data.csv > data/data.csv
run-notebook
```

`run-notebook` menimpa keluaran notebook, lalu menulis hasilnya ke `artifacts/` dan `artifacts.zip`, dalam waktu sekitar 9 menit pada laptop 16 thread. Notebook berhenti dengan pesan jelas jika hash `data.csv` berbeda. Artefak hasil laptop dapat berbeda sedikit dari Release pada model XGBoost, jadi angka di laporan mengikuti Release.

## Dataset

Realinho, V., Vieira Martins, M., Machado, J., & Baptista, L. (2021). _Predict students' dropout and academic success_ [Data set]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5MC89>

Dataset ini berlisensi [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Data tidak disimpan di repo ini.

## Lisensi

Kode berlisensi [Apache-2.0](LICENSE). Lisensi ini hanya berlaku untuk kode, dan data tetap mengikuti lisensi CC BY 4.0 milik pembuatnya.
