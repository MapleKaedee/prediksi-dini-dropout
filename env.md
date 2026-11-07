# Lingkungan Pengembangan

Lingkungan laptop untuk notebook eksperimen dan aplikasi demo. Python dan seluruh pustaka disediakan Nix, dan versinya mengikuti `flake.lock`. Jangan memakai `pip install` atau `venv` di laptop. Paket baru ditambahkan di `flake.nix`.

## Prasyarat

- Linux `x86_64` dengan Nix, fitur `nix-command` dan `flakes` aktif.
- Git. Folder proyek harus berupa repo Git. Tanpa Git, flake menyalin seluruh folder ke Nix store, termasuk data dan artefak, dan hook tidak terpasang.
- direnv dan nix-direnv **3.2.0 atau lebih baru**, hanya jika ingin aktivasi otomatis.
- Browser modern untuk JupyterLab dan aplikasi.

## Mulai

```sh
nix develop
mkdir -p data
curl -L -o data/uci.zip 'https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip'
unzip -p data/uci.zip data.csv > data/data.csv
sha256sum data/data.csv
doctor
run-notebook
```

Hash `data.csv` harus sama dengan nilai berikut:

```text
3ef126de5cefff26eb11fbb4237f1a1401cb64b488e2f1d598c23cedeb4c45ae
```

Pembangunan pertama mengunduh sekitar 372 MiB, atau 1,5 GiB setelah dibuka. Untuk tetap memakai shell lain secara interaktif, jalankan misalnya `nix develop --command fish`.

## Aktivasi otomatis dengan direnv

Jika direnv dan nix-direnv sudah terpasang dan hook shell sudah aktif, cukup jalankan:

```sh
direnv allow
```

Jika belum, pasang direnv melalui pengelola paket host dan nix-direnv melalui Nix:

```sh
nix profile add nixpkgs#nix-direnv
```

Tambahkan baris berikut ke `~/.config/direnv/direnvrc`:

```sh
source "$HOME/.nix-profile/share/nix-direnv/direnvrc"
```

Aktifkan hook sesuai [petunjuk direnv](https://direnv.net/docs/hook.html), misalnya `eval "$(direnv hook bash)"` di `~/.bashrc`. Jangan menggandakan konfigurasi yang sudah ada.

`.envrc` memeriksa versi nix-direnv, memantau modul di `nix/`, lalu memuat `use flake`. Setelah mengubah `.envrc`, jalankan `direnv allow` lagi. `nix develop` tetap dapat dipakai tanpa direnv.

## Perintah harian

| Perintah       | Fungsi                                                       |
| -------------- | ------------------------------------------------------------ |
| `menu`         | Menampilkan daftar perintah                                  |
| `fmt`          | Memformat file dengan treefmt                                |
| `check`        | Menjalankan `nix flake check`                                |
| `run-tests`    | Menjalankan pytest pada `tests/`                             |
| `doctor`       | Menampilkan versi Python dan pustaka                         |
| `pins`         | Mencetak baris `%pip install` untuk sel pertama notebook     |
| `lab`          | Membuka JupyterLab di `127.0.0.1`                            |
| `run-notebook` | Menjalankan notebook tanpa antarmuka dan menimpa keluarannya |
| `app`          | Menjalankan aplikasi Streamlit di `127.0.0.1`                |

`run-tests` dan `app` baru dapat dipakai setelah `tests/` dan `app/` tersedia.

`run-notebook` dapat mencetak `Kernel is running over TCP without encryption`. Kernel Jupyter di sini hanya mendengarkan `127.0.0.1`, jadi peringatan ini tidak menghentikan notebook.

## Formatter dan hook

`nix/treefmt.nix` menjadi satu-satunya sumber konfigurasi format: nixfmt untuk Nix, ruff untuk Python, Prettier untuk Markdown, YAML, dan JSON, serta shfmt untuk skrip shell dan `.envrc`. `docs/`, `notebooks/`, `data/`, `artifacts/`, dan `flake.lock` dikecualikan.

`nix/hooks.nix` mengaktifkan treefmt dan pemeriksaan konflik merge. Hook dipasang saat lingkungan dimuat di repo Git melalui `nix develop` atau direnv. `.pre-commit-config.yaml` dihasilkan otomatis dan tidak masuk Git.

Jika formatter memperbaiki file saat commit, tinjau hasilnya, stage ulang, lalu ulangi commit. Untuk memeriksa format tanpa mengubah file:

```sh
treefmt --fail-on-change
```

`nix flake check` hanya menjalankan pemeriksaan yang dapat berjalan di sandbox, jadi notebook dan pytest dijalankan terpisah.

Flake dalam repo Git hanya melihat file yang dikenali Git. File baru harus di-stage sebelum perintah Nix:

```sh
git add <file>
check
```

## Pembaruan versi

Jangan memperbarui `flake.lock` setelah artefak final dibuat, karena model yang tersimpan terikat pada versi `scikit-learn`.

```sh
nix flake update
fmt
check
run-tests
pins
```

Jalankan ulang notebook jika versi `scikit-learn` berubah, dan perbarui baris `%pip` serta `SKLEARN_PIN` di notebook sesuai keluaran `pins`.

## Keselarasan dengan Kaggle

Kaggle adalah tempat jalan utama, dan laptop adalah cadangan. Sumber versi adalah `flake.lock`, dan `pins` mencetak baris instalasi untuk sel pertama notebook. Notebook berhenti lebih awal jika versi `scikit-learn` tidak sama. Jika instalasi gagal di Kaggle, jalankan notebook di laptop dengan `run-notebook`.

Notebook mengunduh data sendiri, jadi internet harus aktif di pengaturan notebook Kaggle.

## Referensi

- [devshell](https://github.com/numtide/devshell)
- [nix-direnv](https://github.com/nix-community/nix-direnv)
- [treefmt-nix](https://github.com/numtide/treefmt-nix)
- [git-hooks.nix](https://github.com/cachix/git-hooks.nix)
