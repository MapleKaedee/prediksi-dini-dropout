# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyek

Penelitian "Prediksi Dini Risiko Dropout Mahasiswa" untuk mata kuliah Penambangan Data, dengan tenggat 11 Januari 2027. Kualitas dan kejujuran evaluasi model lebih penting daripada tampilan, jadi antarmuka cukup berfungsi dengan benar.

Metode penelitian mengikuti `docs/Proposal_Penelitian_Dropout_Mahasiswa.docx`, dan rincian implementasi mengikuti `PRD.md`. Baca bagian PRD yang relevan sebelum menulis kode. ID seperti `NB-07` dan `APP-33` merujuk ke persyaratan di PRD. `docs/Context.md` berisi petunjuk tugas dari dosen. `docs/` dan `PRD.md` masuk `.gitignore`, jadi keduanya hanya ada di laptop pemilik dan tidak ada di clone.

Saat file ini dibuat, folder proyek baru berisi `CLAUDE.md`, `LICENSE`, `.gitignore`, `PRD.md`, dan `docs/`. Cek file yang benar-benar ada sebelum menjalankan perintah. File flake dibuat dari PRD Lampiran A.

Balas pemilik dalam bahasa Indonesia dengan sapaan aku/kamu.

## Git dan GitHub

Pemilik sendiri yang mengurus commit, push, dan repo. Jangan menjalankan `git init`, `git commit`, `git push`, `git remote`, `gh repo create`, atau `gh release create`. Perintah semacam itu di PRD DEV-11 dan DEV-12 ditujukan untuk pemilik.

Repo ini dan notebook Kaggle bersifat publik. Jangan menaruh nama, NIM, token, atau path lokal di file yang masuk Git, termasuk keluaran notebook, dan jangan memakai `git add -f` untuk `docs/` atau `PRD.md`.

`git status`, `git diff`, `git log`, dan `git add` boleh dipakai. `git add` diperlukan karena flake hanya melihat file yang dikenali Git, jadi file baru harus di-stage sebelum perintah Nix. Jika folder belum menjadi repo Git, minta pemilik menjalankan `git init -b main`.

Setelah pekerjaan selesai, sebutkan file yang berubah dan usulkan satu pesan commit.

## Perintah

Jalankan di shell Nix, dengan `nix develop -c <perintah>` atau langsung jika direnv aktif. Jangan memakai `pip install` atau `venv` di laptop. Paket baru ditambahkan di `flake.nix`.

| Perintah                                        | Fungsi                                                         |
| ----------------------------------------------- | -------------------------------------------------------------- |
| `fmt`                                           | Memformat dan memperbaiki lint (nixfmt, ruff, Prettier, shfmt) |
| `treefmt --fail-on-change`                      | Memeriksa format tanpa mengubah file                           |
| `check`                                         | `nix flake check`, tanpa pytest dan tanpa notebook             |
| `run-tests`                                     | Semua tes pytest                                               |
| `run-tests -k nama_tes`                         | Satu tes menurut nama                                          |
| `python -m pytest tests/test_core.py::nama_tes` | Satu tes menurut path                                          |
| `doctor`                                        | Versi Python dan pustaka                                       |
| `pins`                                          | Baris `%pip install` untuk sel pertama notebook di Kaggle      |
| `lab`                                           | JupyterLab di `127.0.0.1`                                      |
| `run-notebook`                                  | Menjalankan notebook tanpa antarmuka dan menimpa keluarannya   |
| `app`                                           | Aplikasi Streamlit di `127.0.0.1`                              |

## Arsitektur

Alurnya satu arah: `data/data.csv` diproses `notebooks/dropout_experiments.ipynb` menjadi `artifacts/`, lalu dibaca `app/`.

- **Notebook** berdiri sendiri, karena Kaggle tidak dapat mengimpor modul proyek. Kaggle adalah tempat jalan utama dan laptop adalah cadangan. Notebook melatih 24 model dan mengekspor artefak.
- **Artefak** (PRD bagian 8) adalah satu-satunya penghubung notebook dan aplikasi. Perubahan skema harus mengubah notebook, aplikasi, dan tes bersama-sama, serta menaikkan `schema_version`.
- **Aplikasi** tidak pernah melatih model. Preprocessing tersimpan di dalam `Pipeline`, jadi aplikasi tidak menulis ulang logikanya. Hanya halaman Prediksi yang menghitung langsung, memakai enam Random Forest (`A_*_rf` dan `B_*_rf`). Halaman lain membaca artefak.
- **`app/core.py`** berisi logika tanpa Streamlit agar dapat diuji, sedangkan `app/views/` hanya berisi tampilan.
- **Versi** `scikit-learn` di notebook harus sama dengan di shell Nix, karena pickle terikat pada versinya. `pins` menyelaraskan Kaggle dengan `flake.lock`, dan aplikasi menolak versi yang berbeda (APP-02). Jangan memperbarui `flake.lock` setelah artefak final dibuat.

## Aturan Penelitian

- Target, pengeluaran `Course` 171, pembagian data, seed 42, ruang pencarian, ambang 0,5, skenario, dan metrik mengikuti proposal. Jangan mengubahnya tanpa persetujuan pemilik, dan perubahan apa pun harus dicatat di laporan.
- Data uji tidak boleh memengaruhi parameter, ambang, atau atribut model. Jika target G2 tidak tercapai, laporkan sebagai temuan negatif.
- Angka di aplikasi dan laporan harus berasal dari artefak. Angka pada proposal Tabel 14 dan PRD Lampiran B adalah uji kelayakan, bukan hasil penelitian.
- Mahasiswa ditandai jika `risk >= 0.5`. Hitung metrik ambang dari aturan itu, bukan dari `.predict()`.
- Nilai SHAP kolom one-hot dijumlahkan ke atribut asalnya per baris, baru kemudian dirata-ratakan.
- Hasil penelitian ini menunjukkan pola prediktif, bukan hubungan sebab akibat.

## Aturan Aplikasi

- Keluaran memakai "skor risiko", "Perlu ditinjau", dan "Tidak ditandai". Model memakai bobot kelas, jadi skornya bukan peluang terkalibrasi, dan aplikasi tidak boleh menulis "akan dropout".
- Pakai tema dan grafik bawaan Streamlit, tanpa pustaka grafik tambahan.
- AI Studio, latih ulang dari antarmuka, unggah file, dan hosting publik berada di luar lingkup (PRD bagian 3). Tanpa AI Studio dan demo hanya lokal adalah keputusan final pemilik.
- `joblib.load` dapat menjalankan kode, jadi hanya dipakai untuk `artifacts/models/` hasil notebook sendiri.

## Jebakan yang Sudah Ditemukan

- `data.csv` memakai pemisah `;` dan akhir baris CRLF, dan nama kolom ke-5 diakhiri tab, jadi nama kolom harus di-`strip`.
- Path pada `AppTest.from_file` dihitung dari file pemanggil, jadi pakai path absolut berbasis `Path(__file__)`.
- Perintah devshell tidak boleh bernama `test`, karena kalah dengan builtin shell.
- `ruff` tidak tersedia langsung di shell, dan hanya berjalan melalui `fmt`.

## File yang Perlu Hati-Hati

- `docs/Context.md` adalah petunjuk dari dosen dan tidak boleh diubah. `docs/` dikecualikan dari formatter.
- `docs/Proposal_Penelitian_Dropout_Mahasiswa.docx` sudah diedit pemilik dan memuat nama serta NIM. Jika diminta mengubahnya, edit file itu langsung dan jangan membuatnya ulang.
- `docs/`, `PRD.md`, `data/`, `artifacts/`, dan `artifacts.zip` tidak masuk Git.
- `LICENSE` (Apache-2.0) hanya berlaku untuk kode. Data tetap CC BY 4.0 milik Realinho dkk., jadi atribusinya wajib ada di `README.md` dan catatan Release.
- Laporan akhir ditulis dalam format Word di `docs/`. Jika perlu PDF, pemilik mengekspornya sendiri.
