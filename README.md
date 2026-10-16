# ⚡ Agent CeTeEf (agentceteef)

> **Autonomous CTF Multi-Model Solver Swarm & Real-Time Security Reasoning Engine**  
> 🔗 GitHub Repository: [BBB30011/agentceteef](https://github.com/BBB30011/agentceteef)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python: 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](pyproject.toml)
[![Tests: Passing](https://img.shields.io/badge/Tests-24%20passed-brightgreen.svg)](tests/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](pyproject.toml)

**Agent CeTeEf** adalah framework otonom untuk kompetisi *Capture The Flag* (CTF) yang memadukan kekuatan berbagai model kecerdasan buatan (*multi-model swarm*) untuk menemukan kerentanan, merancang eksploitasi, dan merebut bendera (*flag*) secara paralel dan real-time.

Awalnya dirancang oleh [Veria Labs](https://verialabs.com) (anggota tim *smiley*, peringkat #1 tim CTF AS di CTFTime) dan menjuarai **BSidesSF 2026 CTF (52/52 tantangan solved, Juara 1)**.

Kini telah direfaktor dan diperkuat dalam repositori **Agent CeTeEf** dengan arsitektur modern, performa tinggi, dan kemudahan penggunaan:
- 🚀 **Mode Tanpa Token (Antigravity CLI / `agy`)**: Dukungan eksekusi lokal tanpa biaya token API ($0 cost), offline-ready memanfaatkan toolchain host Kali Linux.
- ⚡ **Multi-Model Parallel Swarms**: Integrasi langsung dengan Google Gemini, OpenAI (GPT-4o, o3-mini), Anthropic (Claude 3.7 Sonnet), DeepSeek, Groq (Llama 3.3 70B), OpenRouter, Ollama/Local LLMs, AWS Bedrock, dan Azure OpenAI.
- ⚡ **Streaming Output & Real-Time Early Exit**: Output terminal dibaca secara asinkron baris demi baris. Begitu pola flag ditemukan oleh regex, proses solver langsung dihentikan dan diverifikasi dalam hitungan detik tanpa perlu menunggu timeout.
- 🧠 **Universal Coordinator**: Agen pengatur strategi otonom berbasis `pydantic-ai` yang memantau perkembangan tantangan, memberikan petunjuk teknis (*bump*), serta membagikan temuan kunci (*broadcast*) ke seluruh agent yang bekerja.
- 🛠️ **Peralatan Khusus Analisis CTF Lengkap**:
  - `checksec`: Analisis mitigasi proteksi biner ELF (RELRO, Stack Canary, NX, PIE).
  - `decompile`: Dekompilasi & disassembli fungsi simbolis via Radare2 / Objdump.
  - `auto_decode`: Dekode kaskade otomatis berlapis (*multi-layer cascade*: Base64, Hex, Base32, Rot13, URL, Binary).
  - `single_byte_xor`: Brute force XOR 1-byte otomatis (0..255) untuk memecahkan ciphertext XOR klasik.
  - `identify_hash`: Identifikasi format hash (MD5, SHA1, SHA256, bcrypt, NTLM) dan saran mode Hashcat/John.
  - `calculate_entropy`: Analisis Shannon entropy untuk mendeteksi payload terenkripsi/terkompresi.
  - `find_flags`: Pemindaian pola regex otomatis di seluruh file workspace.
- 🖥️ **UI/UX Interaktif & Visual Memukau**:
  - Peluncur satu-klik `./run.sh` dengan panduan terminal wizard interaktif dan shortcut perintah instan (`demo`, `tokenless`, `fast`, `smart`, `report-html`).
  - Banner perayaan penemuan bendera (*Flag Captured*) berwarna kontras dengan detail waktu dan model pemenang.
  - Ekspor laporan analitik kompetisi berformat **Dark Mode HTML** mandiri (`make report-html` atau `./run.sh report-html`).
- 🛡️ **Dual Execution Sandbox**: Berjalan aman di dalam kontainer Docker terisolasi atau di host lokal (Kali Linux) dengan process group isolation dan timeout otomatis.
- 💾 **State Persistence SQLite**: Melacak seluruh tantangan, flag, riwayat submisi, dan durasi solve dengan dukungan `--resume` (melewati soal yang telah selesai) dan `--report`.

---

## 🏛️ Arsitektur Sistem

```
                         +-----------------------------+
                         |     Platform Target CTFd    |
                         +--------------+--------------+
                                        ▲
                        Submit Flag (Dedup & Cooldown)
                                        │
                         +--------------+--------------+
                         |     Live Poller Event Loop  |
                         +--------------+--------------+
                                        │
                         +--------------v--------------+
                         |   Universal Coordinator     |
                         |  (Gemini / GPT / Claude)    |
                         +--------------+--------------+
                                        │
             +--------------------------+--------------------------+
             │                          │                          │
    +--------v--------+        +--------v--------+        +--------v--------+
    | Swarm: Pwn      |        | Swarm: Crypto   |        | Swarm: Web/Rev  |
    |                 |        |                 |        |                 |
    | Antigravity agy |        | Gemini 2.5 Pro  |        | GPT-4o          |
    | Groq Llama 3.3  |        | Claude 3.7      |        | DeepSeek Chat   |
    +--------+--------+        +--------+--------+        +--------+--------+
             │                          │                          │
             +--------------------------+--------------------------+
                                        │
                         +--------------v--------------+
                         |       Sandbox Engine        |
                         |   (Docker / Local Host)     |
                         |                             |
                         | pwntools, r2, gdb, checksec,|
                         | python, curl, auto_decode   |
                         +-----------------------------+
```

---

## 🚀 Panduan Penggunaan Cepat (Quick Start)

### 1. One-Click Interactive Launcher (Rekomendasi)
Cukup jalankan satu perintah ini, wizard interaktif akan memandu Anda:
```bash
./run.sh
```
Atau menggunakan Make:
```bash
make run
```

### 2. Preset Profil Cepat (Tanpa Ribet Mengatur Flag)
- **Mode Tanpa Token (Antigravity CLI / $0 Token)**:
  ```bash
  make tokenless
  # atau: uv run ctf-solve --profile tokenless
  ```
- **Mode Cepat (Throughput & Latensi Rendah)**:
  ```bash
  make fast
  # atau: uv run ctf-solve --profile fast
  ```
- **Mode Smart / Deep Reasoning (Gemini 2.5 Pro / GPT-4o / Claude 3.7)**:
  ```bash
  uv run ctf-solve --profile smart
  ```

### 3. Memecahkan Satu Tantangan Tertentu
```bash
# Menyerang folder tantangan bawaan dalam mode dry-run:
uv run ctf-solve --challenge ./challenges/demo_sanity --no-submit
```

### 4. Laporan Kompetisi & Ekspor Visual (Dark Mode HTML)
```bash
# Cetak ringkasan teks di terminal:
make report

# Ekspor ke file HTML siap buka di browser:
make report-html
# File 'ctf_report.html' akan dibuat otomatis!
```

---

## ⚙️ Konfigurasi Kredensial (`.env`)

Salin file contoh dan masukkan API key atau kredensial CTFd Anda:
```bash
cp .env.example .env
```
Isi konfigurasi pada file `.env`:
```env
# Konfigurasi CTFd
CTFD_URL=https://ctf.example.com
CTFD_TOKEN=ctfd_your_api_token_here
CTFD_USER=admin
CTFD_PASS=admin

# AI Model Keys (konfigurasi salah satu atau beberapa)
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=

# Local / Ollama Endpoints
OLLAMA_BASE_URL=http://localhost:11434/v1
```

---

## 🛡️ Mode Eksekusi Sandbox

Mode sandbox dapat diatur melalui flag `--sandbox-mode`:

| Mode | Deskripsi |
|------|-----------|
| `auto` (Default) | Otomatis mendeteksi Docker; jika Docker tidak aktif, otomatis beralih ke isolasi lokal tanpa gangguan. |
| `docker` | Menjalankan seluruh tool dan exploit di dalam kontainer Docker terisolasi `ctf-sandbox`. |
| `local` | Menjalankan langsung di Kali Linux dengan direktori sementara terisolasi dan pembatasan timeout grup proses. |

Untuk membangun image Docker sandbox:
```bash
make build-sandbox
```

---

## 🧪 Pengujian Otomatis (Testing)

Jalankan seluruh test suite unit dan integrasi:
```bash
make test
```
Jalankan linter kode:
```bash
make lint
```

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
│   ├── tools/                       # CTF Tools (Checksec, Disasm, Auto-Decode, XOR, HashID, Entropy)
│   ├── ui/                          # Terminal Dashboard, Menu Wizard, HTML Exporter
│   ├── config.py / models.py        # Multi-provider routing & settings
│   ├── sandbox.py / ctfd.py         # Dual Sandbox & CTFd client
│   └── state.py / cli.py            # SQLite state & Rich CLI Dashboard
├── challenges/                      # Direktori tantangan CTF
│   ├── README.md                    # Panduan format & penambahan tantangan
│   ├── demo_sanity/                 # Contoh challenge verifikasi bawaan
│   └── crypto_cascade/              # Contoh challenge kriptografi multi-layer
├── logs/                            # Direktori jejak log & audit (.gitkeep)
├── tests/                           # 24 Unit & Integration tests (100% passing)
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

Proyek ini telah dilengkapi dengan dokumentasi standar tim dan open-source dalam Bahasa Indonesia:
- 📖 **[CONTRIBUTING.md](CONTRIBUTING.md)**: Panduan alur kerja branch Git, konvensi pesan commit, dan tata cara pembuatan Pull Request.
- 🛡️ **[PANDUAN_KOLABORASI.md](PANDUAN_KOLABORASI.md)**: Panduan strategi operasional tim manusia bersama AI selama kompetisi live berlangsung menggunakan `ctf-msg`.
- 📜 **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**: Kode etik kolaborasi dan etika keamanan siber.
- 📋 **[.github/](.github/)**: Template Pull Request dan Issue Tracker terstruktur untuk GitHub.

---

## ⚖️ Lisensi & Hak Cipta

Proyek ini dilisensikan di bawah [Lisensi MIT](LICENSE). Dibuat untuk tujuan riset keamanan siber defensif, kompetisi CTF resmi, dan edukasi keamanan informasi.
