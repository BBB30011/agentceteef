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

## ⚡ Panduan Cepat 3 Langkah (Quick Start Tanpa Bingung)

Anda hanya butuh **3 perintah** di terminal untuk memulai:

```bash
# Langkah 1: Masuk ke folder proyek
cd CTFPROJECT

# Langkah 2: Jalankan skrip setup (otomatis menyiapkan dependensi & diagnostik sistem)
./setup.sh

# Langkah 3: Uji pemecahan tantangan demo pertama Anda!
./run.sh demo
```
*Selesai! Anda akan langsung melihat AI swarm menganalisis soal demo dan merebut flag dalam hitungan detik!* 🎉

---

## 📋 Lembar Sontekan Perintah (`./run.sh` Cheat Sheet)

Semua operasi harian dapat dijalankan melalui perintah `./run.sh` yang mudah diingat:

| Perintah | Fungsi | Kapan Harus Digunakan? |
|---|---|---|
| **`./run.sh`** | **Interactive Wizard Menu** | 🌟 **Rekomendasi bagi pemula** yang ingin dipandu menu visual langkah demi langkah. |
| **`./run.sh demo`** | **Uji Soal Bawaan** | Untuk memastikan seluruh sistem, sandbox, dan solver bekerja normal. |
| **`./run.sh tokenless`** | **Mode Gratis ($0 Token)** | Jika Anda ingin solver berjalan offline menggunakan Antigravity CLI tanpa API key berbayar. |
| **`./run.sh fast`** | **Swarm Kecepatan Tinggi** | Menggunakan model latensi rendah (Gemini Flash + Groq Llama 3.3) untuk berburu *First Blood*. |
| **`./run.sh smart`** | **Swarm Penalaran Cerdas** | Menggunakan model reasoning kuat (Gemini 2.5 Pro + GPT-4o + Claude) untuk soal logika/kripto rumit. |
| **`./run.sh report-html`** | **Ekspor Laporan Dark Mode** | Menghasilkan file visual `ctf_report.html` yang bisa dibuka langsung di browser web. |
| **`./run.sh test`** | **Uji 26 Test Otomatis** | Menjalankan seluruh pengujian unit & integrasi untuk memverifikasi keutuhan kode. |
| **`./run.sh lint`** | **Pemeriksaan Kode Ruff** | Memastikan tidak ada kesalahan sintaksis atau standar gaya kode. |

---

## 🎯 3 Skenario Penggunaan Nyata (Paling Sering Digunakan)

### 1. Skenario A: "Saya ingin pakai yang 100% GRATIS tanpa beli token API"
Cukup jalankan satu perintah ini:
```bash
./run.sh tokenless
```
> **Penjelasan:** Mode ini otomatis memakai Antigravity CLI (`agy`) dan toolchain lokal Linux (Kali Linux). Tidak ada kuota token yang terpakai ($0.00).

---

### 2. Skenario B: "Saya punya soal CTF sendiri, bagaimana cara menyuruh AI menyelesaikannya?"
Hanya perlu 2 langkah mudah:
1. Buat folder baru di dalam folder `challenges/`, misalnya: `challenges/soal_kripto/`
2. Masukkan file soal ke dalam subfolder `distfiles/` dan buat file `metadata.yml`.
3. Jalankan solver terhadap folder tersebut:
```bash
./run.sh --challenge challenges/soal_kripto --no-submit
```
*(Flag `--no-submit` memastikan AI hanya mencari flag tanpa mencoba mengunggahnya ke server online).*

---

### 3. Skenario C: "Saya sedang tanding di lomba online (CTFd), bagaimana cara menghubungkannya?"
1. Salin template konfigurasi jika belum ada:
   ```bash
   cp .env.example .env
   ```
2. Buka file `.env` dan masukkan URL lomba serta token akses Anda:
   ```env
   CTFD_URL=https://ctf.penyelenggara.com
   CTFD_TOKEN=ctfd_token_rahasia_anda_disini
   ```
3. Tambahkan API key model yang Anda miliki (misal: `GEMINI_API_KEY`, `OPENAI_API_KEY`, atau `GROQ_API_KEY`).
4. Jalankan agen:
   ```bash
   ./run.sh
   ```
   *Agent CeTeEf akan otomatis memindai soal-soal di platform, mengunduh file, membagi tugas ke swarm, dan mengirimkan flag yang valid dengan jeda anti-spam (cooldown).*

---

## 📊 Melihat Rekap Skor & Laporan Visual

Ingin melihat ringkasan flag apa saja yang sudah berhasil didapatkan tim?
```bash
# 1. Ringkasan teks di terminal:
./run.sh report

# 2. Hasilkan laporan halaman web Dark Mode:
./run.sh report-html
```
Buka file `ctf_report.html` di browser Anda (Google Chrome / Firefox) untuk melihat tabel interaktif lengkap dengan durasi waktu per soal, model pemenang, dan flag yang didapatkan!

---

## 🛠️ Peralatan CTF Bawaan (Built-in Security Tools)

Swarm AI dilengkapi dengan beragam tool analisis otomatis yang bekerja di latar belakang:
- 🧩 **`auto_decode`**: Dekode otomatis kaskade berlapis (*multi-layer*: Base64 ➔ ROT13, Hex ➔ Base32, URL decode, dll).
- 🔑 **`single_byte_xor`**: Mencoba 256 kombinasi kunci XOR secara instan untuk membongkar ciphertext klasik.
- 🏷️ **`identify_hash`**: Mengenali jenis hash (MD5, SHA1, SHA256, bcrypt, NTLM) serta menyarankan parameter Hashcat/John.
- 🔎 **`file_info`**: Memeriksa *magic bytes* sejati untuk mendeteksi file yang disamarkan ekstensinya.
- 📜 **`strings_search`**: Mengekstrak teks dari biner dengan filter kata kunci dan pemindaian regex flag otomatis.
- 🛡️ **`checksec`**: Mengecek proteksi biner ELF (RELRO, Stack Canary, NX, PIE).
- ⚙️ **`decompile`**: Membaca disassembly fungsi simbolis via Radare2 / Objdump.
- 📈 **`calculate_entropy`**: Menghitung Shannon entropy untuk mendeteksi payload terenkripsi/terkompresi.

---

## ❓ Pertanyaan yang Sering Ditanyakan (FAQ)

<details>
<summary><b>1. Apakah saya wajib menginstal Docker?</b></summary>

**Tidak wajib.** Secara default, sistem menggunakan mode `auto`. Jika Docker tidak aktif atau tidak terinstal, Agent CeTeEf otomatis beralih ke mode **Local Sandbox** (isolasi lokal di Kali Linux) dengan pembatasan proses dan timeout yang aman.
</details>

<details>
<summary><b>2. Apakah saya harus punya API key OpenAI atau Gemini?</b></summary>

**Tidak.** Anda bisa menggunakan **Mode Tanpa Token (`./run.sh tokenless`)** yang memanfaatkan Antigravity CLI lokal secara gratis ($0 cost). API key hanya diperlukan jika Anda ingin memanfaatkan model komputasi awan seperti GPT-4o, Claude 3.7, atau Gemini Pro.
</details>

<details>
<summary><b>3. Di mana file tantangan disimpan?</b></summary>

Semua tantangan disimpan di direktori [`challenges/`](challenges/). Repositori ini sudah menyertakan 4 contoh soal bawaan:
- `demo_sanity`: Uji coba dasar.
- `crypto_cascade`: Latihan kriptografi multi-lapis.
- `forensics_disguise`: Latihan forensik berkas terselubung.
- `rev_vault`: Latihan reverse engineering logika Python.
Panduan lengkap ada di [`challenges/README.md`](challenges/README.md).
</details>

<details>
<summary><b>4. Bagaimana cara menghentikan proses agen jika sedang berjalan?</b></summary>

Cukup tekan tombol **`Ctrl + C`** pada terminal. State pengerjaan akan tersimpan di database lokal SQLite (`ctf_state.sqlite3`), sehingga jika Anda menjalankan `./run.sh --resume`, soal yang sudah berhasil dipecahkan tidak akan dikerjakan ulang.
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
