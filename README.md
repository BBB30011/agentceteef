# ⚡ Agent CeTeEf (agentceteef)

> **Autonomous CTF Multi-Model Solver Swarm & Real-Time Security Reasoning Engine**  
> 🔗 GitHub Repository: [BBB30011/agentceteef](https://github.com/BBB30011/agentceteef)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](pyproject.toml)
[![Tests: Passing](https://img.shields.io/badge/Tests-26%20passed-brightgreen.svg)](tests/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](pyproject.toml)
[![CI: Automated](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF.svg)](.github/workflows/ci.yml)

**Agent CeTeEf** adalah asisten kecerdasan buatan (*AI Swarm*) otonom untuk kompetisi *Capture The Flag* (CTF). Sistem ini menggabungkan berbagai model AI terkemuka untuk menganalisis tantangan keamanan siber, membongkar proteksi biner, mendekripsi ciphertext, dan merebut bendera (*flag*) secara otomatis, paralel, dan real-time.

---

## ⚡ Panduan Kilat 3 Menit (Quick Start)

Bagi Anda yang ingin langsung mencoba tanpa berbelit-belit:

```bash
# 1. Clone repositori dari GitHub
git clone https://github.com/BBB30011/agentceteef.git
cd agentceteef

# 2. Jalankan skrip setup otomatis
./setup.sh

# 3. Jalankan pengujian soal demo bawaan
./run.sh demo
```
*Selesai! AI Swarm akan langsung menganalisis soal demo dan merebut flag dalam hitungan detik!* 🎉

---

## 📖 Panduan Lengkap: Dari Clone Git Sampai Mahir Menggunakan

Panduan langkah demi langkah dari nol bagi Anda yang baru pertama kali menggunakan Agent CeTeEf:

### 📥 Langkah 1: Mengambil Proyek dari Git (Clone Repository)

Buka terminal Linux Anda (direkomendasikan Kali Linux, Ubuntu, Debian, atau WSL2) dan ketik:

```bash
git clone https://github.com/BBB30011/agentceteef.git
cd agentceteef
```

Jika diminta memasukkan Personal Access Token (PAT) GitHub untuk repositori privat:
```text
Username: BBB30011
Password: <token_github_pat_anda>
```

---

### ⚙️ Langkah 2: Menyiapkan Lingkungan Sistem (`./setup.sh`)

Jalankan skrip inisialisasi lingkungan:
```bash
./setup.sh
```

**Apa yang dilakukan oleh skrip ini secara otomatis?**
1. Memeriksa ketersediaan Python (minimal Python 3.13).
2. Memeriksa atau menginstal package manager ultra-cepat **Astral uv**.
3. Mengunduh dan menyinkronkan seluruh dependensi proyek (`pydantic-ai`, `rich`, `click`, dll).
4. Membuat file konfigurasi `.env` dari template bawaan `.env.example`.
5. Menjalankan **Diagnostik Toolchain CTF** untuk mendeteksi ketersediaan:
   - `checksec` (analisis proteksi biner ELF)
   - `r2` / `radare2` (dekompilasi dan disassembler)
   - `strings` & `file` (inspeksi tipe berkas dan ekstraksi string)
   - `agy` (Antigravity CLI untuk mode tanpa token)

---

### 🚀 Langkah 3: Menjalankan Solver Pertama Kali

Ada 2 cara paling mudah untuk menjalankan Agent CeTeEf:

#### Cara A: Menggunakan Menu Interaktif (Paling Ramah Pemula)
Cukup jalankan:
```bash
./run.sh
```
Akan muncul menu pilihan interaktif di terminal Anda:
```text
Silakan pilih mode operasi yang Anda inginkan:
  1. 🚀 Mode Tanpa Token (Antigravity CLI / Local) — $0 token cost, offline-ready
  2. ⚡ Swarm Cepat (Fast Swarm) — Latensi rendah & throughput tinggi
  3. 🧠 Swarm Cerdas (Smart / Deep Swarm) — Gemini 2.5 Pro / GPT-4o / Claude
  4. 🎯 Pecahkan 1 Tantangan Spesifik — Pilih tantangan tertentu
  5. 📊 Lihat Laporan & Ekspor HTML — Statistik kompetisi
  0. 🚪 Keluar
```
Ketik angka pilihan Anda (misalnya: `1` untuk mode gratis atau `4` untuk memilih soal) lalu tekan **Enter**.

#### Cara B: Menguji Tantangan Demo Bawaan
```bash
./run.sh demo
```
Perintah ini akan menyerang soal uji coba `challenges/demo_sanity/`, mengekstrak flag, dan menampilkan banner perayaan kemenangan `🎉 FLAG CAPTURED & CONFIRMED!` dengan biaya **$0.00**.

---

### 🆓 Langkah 4: Menggunakan Mode 100% Gratis Tanpa Token API ($0 Cost)

Jika Anda **tidak memiliki API Key berbayar** (seperti OpenAI atau Anthropic), Anda tetap bisa menggunakan Agent CeTeEf secara maksimal menggunakan **Mode Tanpa Token**:

```bash
./run.sh tokenless
```
Mode ini memanfaatkan toolchain host lokal dan Antigravity CLI (`agy`) untuk menganalisis dan memecahkan soal secara lokal tanpa internet dan tanpa kuota token.

---

### 📂 Langkah 5: Memecahkan Soal CTF Milik Anda Sendiri

Ingin menyuruh AI menyelesaikan soal CTF yang Anda miliki? Sangat mudah:

1. **Buat folder soal baru** di dalam direktori `challenges/`, misalnya:
   ```bash
   mkdir -p challenges/soal_kripto/distfiles
   ```
2. **Salin berkas soal** (biner, ciphertext, script, gambar, pcap) ke dalam folder `challenges/soal_kripto/distfiles/`.
3. **Buat file `challenges/soal_kripto/metadata.yml`**:
   ```yaml
   name: soal_kripto
   category: crypto          # pwn | rev | crypto | web | forensics | misc
   value: 100
   description: |
     Dekripsikan pesan rahasia yang ada di distfiles/pesan.txt.
   ```
4. **Jalankan solver ke folder tersebut**:
   ```bash
   # Mode gratis / offline:
   ./run.sh --challenge challenges/soal_kripto --profile tokenless --no-submit

   # Atau mode swarm cepat:
   ./run.sh --challenge challenges/soal_kripto --profile fast --no-submit
   ```
   *(Flag `--no-submit` memastikan agen hanya mencari flag tanpa mencoba mengunggahnya ke server online).*

---

### 🌐 Langkah 6: Menghubungkan ke Kompetisi Online (Platform CTFd)

Saat Anda mengikuti lomba CTF resmi berbasis platform CTFd:

1. **Edit file `.env`**:
   ```env
   # Kredensial Platform Lomba
   CTFD_URL=https://ctf.penyelenggara.com
   CTFD_TOKEN=ctfd_token_api_anda_dari_profil_akun

   # Kunci API Model AI (isi yang Anda miliki)
   GEMINI_API_KEY=AIzaSy...
   OPENAI_API_KEY=sk-proj-...
   GROQ_API_KEY=gsk_...
   ```
2. **Jalankan Agent CeTeEf**:
   ```bash
   ./run.sh
   # Pilih opsi 2 (Fast Swarm) atau opsi 3 (Smart Swarm)
   ```
   Agen akan:
   - Memindai seluruh soal aktif di scoreboard CTFd.
   - Mengunduh berkas lampiran secara otomatis ke folder workspace lokal.
   - Mempekerjakan swarm AI secara paralel untuk memecahkan soal.
   - Mengirimkan flag ke server CTFd secara otomatis dengan jeda aman (*cooldown & anti-spam*).

---

### 💬 Langkah 7: Memberikan Petunjuk kepada AI yang Sedang Berjalan (Human-in-the-Loop)

Jika Anda melihat AI sedang berusaha memecahkan soal dan Anda (sebagai manusia) menemukan petunjuk tambahan melalui Ghidra/CyberChef, Anda bisa **menyuntikkan petunjuk secara langsung** tanpa mematikan agen:

Buka jendela terminal baru di folder yang sama, lalu ketik:
```bash
uv run ctf-msg "Fungsi verifikasi flag menggunakan algoritma XOR dengan kunci byte 0x5A"
```
Coordinator AI akan menerima pesan Anda dan langsung meneruskannya ke solver yang sedang bekerja pada soal terkait!

---

### 📊 Langkah 8: Memeriksa Hasil & Mengekspor Laporan Skor

Kapan saja selama atau setelah kompetisi, Anda dapat melihat statistik pencapaian:

```bash
# 1. Tampilkan rekap tabel di terminal:
./run.sh report

# 2. Hasilkan laporan visual Dark Mode HTML:
./run.sh report-html
```
File **`ctf_report.html`** akan dibuat. Buka file tersebut dengan peramban web (Chrome, Firefox, Edge) untuk melihat:
- Total soal yang berhasil diselesaikan (*Total Solved*).
- Total poin yang diperoleh.
- Tabel rincian per soal: Kategori badge, flag yang ditemukan, model pemenang, dan durasi pengerjaan.
- Riwayat submisi lengkap.

---

## 📋 Tabel Perintah Penting (Cheat Sheet)

Rangkuman seluruh perintah operasional yang sering digunakan:

| Perintah | Keterangan Singkat |
|---|---|
| `./run.sh` | Membuka interactive menu wizard utama. |
| `./run.sh demo` | Menguji pemecahan soal demo sanity check. |
| `./run.sh tokenless` | Menjalankan solver tanpa biaya API token ($0 Cost). |
| `./run.sh fast` | Menjalankan swarm kecepatan tinggi (Gemini Flash + Groq Llama 3.3). |
| `./run.sh smart` | Menjalankan swarm penalaran cerdas (Gemini 2.5 Pro + GPT-4o + Claude). |
| `./run.sh report` | Menampilkan rekap ringkasan skor di terminal. |
| `./run.sh report-html` | Mengekspor laporan kompetisi ke file `ctf_report.html`. |
| `./run.sh test` | Menjalankan 26 unit & integration tests otomatis. |
| `./run.sh lint` | Memeriksa format dan standar kode dengan Ruff. |
| `make clean` | Membersihkan cache dan file temporary. |

---

## 🛠️ Peralatan CTF Bawaan (Built-in Security Tools)

Swarm AI dilengkapi peralatan analisis otomatis berkecepatan tinggi:
- 🧩 **`auto_decode`**: Dekode kaskade berlapis (*multi-layer*: Base64 ➔ ROT13, Hex ➔ Base32, URL decode, dll).
- 🔑 **`single_byte_xor`**: Mencoba 256 kombinasi kunci XOR secara instan untuk membongkar ciphertext klasik.
- 🏷️ **`identify_hash`**: Mengenali jenis hash (MD5, SHA1, SHA256, bcrypt, NTLM) serta menyarankan parameter Hashcat/John.
- 🔎 **`file_info`**: Memeriksa *magic bytes* sejati untuk mendeteksi file yang disamarkan ekstensinya.
- 📜 **`strings_search`**: Mengekstrak teks dari biner dengan filter kata kunci dan pemindaian regex flag otomatis.
- 🛡️ **`checksec`**: Mengecek proteksi biner ELF (RELRO, Stack Canary, NX, PIE).
- ⚙️ **`decompile`**: Membaca disassembly fungsi simbolis via Radare2 / Objdump.
- 📈 **`calculate_entropy`**: Menghitung Shannon entropy untuk mendeteksi payload terenkripsi/terkompresi.

---

## ❓ Tanya Jawab & Pemecahan Masalah (FAQ)

<details>
<summary><b>1. Apakah saya wajib menginstal Docker?</b></summary>

**Tidak wajib.** Secara default, sistem menggunakan mode `auto`. Jika Docker tidak aktif atau tidak terinstal, Agent CeTeEf otomatis beralih ke mode **Local Sandbox** (isolasi lokal di Kali Linux) dengan pembatasan proses dan timeout yang aman.
</details>

<details>
<summary><b>2. Apakah saya harus punya saldo / API key OpenAI atau Gemini?</b></summary>

**Tidak.** Anda bisa menggunakan **Mode Tanpa Token (`./run.sh tokenless`)** yang memanfaatkan Antigravity CLI lokal secara gratis ($0 cost). API key hanya diperlukan jika Anda ingin memanfaatkan model komputasi awan seperti GPT-4o, Claude 3.7, atau Gemini Pro.
</details>

<details>
<summary><b>3. Di mana saya bisa melihat contoh-contoh soal bawaan?</b></summary>

Semua contoh soal tersimpan di folder [`challenges/`](challenges/):
- **`demo_sanity/`**: Soal pemanasan untuk memastikan sandbox dan pipeline bekerja normal.
- **`crypto_cascade/`**: Soal kriptografi multi-lapis (`ROT13 + Base64`).
- **`forensics_disguise/`**: Soal forensik file terselubung (`avatar.png` yang merupakan file teks berisi flag).
- **`rev_vault/`**: Soal reverse engineering algoritma verifikasi Python (`vault.py`).
</details>

<details>
<summary><b>4. Bagaimana cara menghentikan proses agen yang sedang berjalan?</b></summary>

Cukup tekan tombol **`Ctrl + C`** pada terminal. State pengerjaan akan tersimpan di database lokal SQLite (`ctf_state.sqlite3`). Jika Anda ingin melanjutkan kembali, jalankan perintah dengan menambahkan flag `--resume` (misal: `./run.sh --resume`), sehingga soal yang sudah berhasil dipecahkan tidak akan dikerjakan ulang.
</details>

<details>
<summary><b>5. Bagaimana cara mereset riwayat pengerjaan dari awal?</b></summary>

Jika Anda ingin mengulang dari nol, cukup hapus database state lokal:
```bash
rm -f ctf_state.sqlite3
```
</details>

---

## 📁 Struktur Direktori Repositori

```text
agentceteef/
├── .github/                         # GitHub Actions CI workflow & Issue Templates
│   ├── workflows/ci.yml             # Otomatisasi pengujian & linting CI
│   ├── ISSUE_TEMPLATE/              # Template Bug Report & Usulan Fitur
│   └── pull_request_template.md     # Template Pull Request terstruktur
├── backend/                         # Inti Autonomous Agent
│   ├── agents/                      # Swarm, Solvers (Agy, Claude, Codex, Pydantic AI)
│   ├── tools/                       # CTF Tools (Checksec, Disasm, Auto-Decode, XOR, HashID, Entropy, FileInfo)
│   ├── ui/                          # Terminal Dashboard, Menu Wizard, HTML Exporter
│   ├── config.py / models.py        # Multi-provider routing & settings
│   ├── sandbox.py / ctfd.py         # Dual Sandbox & CTFd client
│   └── state.py / cli.py            # SQLite state & Rich CLI Dashboard
├── challenges/                      # Direktori tantangan CTF
│   ├── README.md                    # Panduan format & penambahan tantangan
│   ├── demo_sanity/                 # Contoh challenge verifikasi bawaan
│   ├── crypto_cascade/              # Contoh challenge kriptografi multi-layer
│   ├── forensics_disguise/          # Contoh challenge file forensics & magic bytes
│   └── rev_vault/                   # Contoh challenge reverse engineering logika
├── logs/                            # Direktori jejak log & audit (.gitkeep)
├── tests/                           # 26 Unit & Integration tests (100% passing)
│   └── fixtures/demo_sanity/        # Fixture pengujian otomatis
├── .env.example                     # Template konfigurasi kredensial
├── .gitignore                       # Aturan pengabaian file terlindungi
├── CODE_OF_CONDUCT.md               # Kode etik komunitas tim CTF
├── CONTRIBUTING.md                  # Panduan kontribusi & alur kerja Git
├── LICENSE                          # Lisensi proyek MIT
├── Makefile                         # Shortcut perintah operasional
├── PANDUAN_KOLABORASI.md            # Panduan operasional live CTF tim manusia
├── pyproject.toml                   # Konfigurasi dependensi & paket
├── README.md                        # Dokumentasi utama proyek
├── run.sh                           # Universal CLI Launcher (Interactive & Shortcuts)
├── setup.sh                         # Skrip setup otomatis environment & diagnostic
└── uv.lock                          # Dependency lockfile deterministik
```

---

## 🤝 Dokumentasi Tim & Kolaborasi (Bahasa Indonesia)

- 📖 **[CONTRIBUTING.md](CONTRIBUTING.md)**: Panduan alur kerja branch Git, konvensi pesan commit, dan tata cara pembuatan Pull Request.
- 🛡️ **[PANDUAN_KOLABORASI.md](PANDUAN_KOLABORASI.md)**: Panduan strategi operasional tim manusia bersama AI selama kompetisi live berlangsung menggunakan `ctf-msg`.
- 📜 **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**: Kode etik kolaborasi dan etika keamanan siber.
- 📋 **[.github/](.github/)**: Template Pull Request dan Issue Tracker terstruktur untuk GitHub.

---

## ⚖️ Lisensi & Hak Cipta

Proyek ini dilisensikan di bawah [Lisensi MIT](LICENSE). Dibuat untuk tujuan riset keamanan siber defensif, kompetisi CTF resmi, dan edukasi keamanan informasi.
