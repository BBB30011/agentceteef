# 🛡️ Panduan Kolaborasi Tim CTF & Operator (Human-in-the-Loop)

Dokumen ini menjelaskan strategi kolaborasi antar anggota tim manusia bersama **Agent CeTeEf (agentceteef)** selama kompetisi Capture The Flag berlangsung secara langsung (*live*).

---

## 👥 Pembagian Peran dalam Tim CTF

Untuk hasil maksimal dalam kompetisi, tim dapat dibagi menjadi beberapa peran operasional:

```text
                      +-----------------------------+
                      |    Platform Target CTFd     |
                      +--------------+--------------+
                                     ▲
                     Flag Submissions│ (Cooldown & Dedup)
                                     │
                 +-------------------+-------------------+
                 |                                       |
    +------------v-------------+            +------------v-------------+
    |   Operator 1 (AI Lead)   |            | Operator 2 & 3 (Manusia) |
    |   - Menjalankan agent    |            | - Analisis Manual        |
    |   - Monitor Swarm Logs   |            | - Ghidra / Burp / CyberChef
    +------------+-------------+            +------------+-------------+
                 │                                       │
                 │         Petunjuk & Solusi             │
                 └───────────────◄───────────────────────┘
                     (via CLI: uv run ctf-msg)
```

1. **Operator 1 (AI Coordinator Lead)**:
   - Menjalankan peluncur interaktif `./run.sh` atau `make run` di server/mesin dedicated.
   - Memantau alokasi model, kuota token, status aktif tantangan, dan log real-time.
2. **Operator 2 (Binary & Reverse Specialist)**:
   - Melakukan dekompilasi manual pada binary yang kompleks jika AI memerlukan arahan logika bisnis.
   - Mengirimkan temuan (misalnya: offset buffer overflow, konstanta kunci enkripsi) ke agent.
3. **Operator 3 (Web & Crypto Specialist)**:
   - Menguji endpoint web kompleks atau memverifikasi rumus matematis kriptografi.
   - Mengirimkan instruksi teknik serangan ke swarm model yang sedang aktif.

---

## 🚀 Memulai Sesi Kompetisi Tim

### Pilihan Cara Menjalankan Agen:
1. **Interactive Wizard (Paling Mudah)**:
   ```bash
   ./run.sh
   ```
2. **Mode Tanpa Token (Antigravity CLI / $0 Token)**:
   ```bash
   make tokenless
   ```
3. **Mode Cepat (Throughput Tinggi)**:
   ```bash
   make fast
   ```

---

## 💬 Berkomunikasi dengan Agent Berjalan via `ctf-msg`

Saat swarm AI sedang memecahkan soal, operator manusia dapat menyuntikkan petunjuk strategis secara real-time tanpa perlu menghentikan proses agen:

```bash
# Format:
uv run ctf-msg "<pesan petunjuk untuk coordinator>"

# Contoh 1: Mengarahkan jenis serangan kriptografi
uv run ctf-msg "Soal crypto-warmup menggunakan algoritma RSA dengan eksponen e=3 kecil, coba lakukan cube root attack atau Hastad attack."

# Contoh 2: Memberikan petunjuk reverse engineering
uv run ctf-msg "Fungsi verifikasi flag berada di alamat 0x4012A0 dan memerlukan input 32 karakter hex."

# Contoh 3: Memberikan format flag khusus kompetisi
uv run ctf-msg "Format flag kompetisi ini diawali dengan CTF_ID{...}"
```

Coordinator LLM akan menerima pesan tersebut melalui endpoint lokal (port `9400` secara default) dan menyebarkannya (*broadcast* / *bump*) ke solver yang sedang bekerja pada soal terkait.

---

## 🔄 Sinkronisasi State & Menghindari Duplikasi Submisi

1. **Pemeriksaan Status Solved Otomatis**:
   Database lokal `ctf_state.sqlite3` mencatat semua flag yang telah berhasil disubmit. Saat dilanjutkan dengan flag `--resume`, soal yang sudah berhasil dipecahkan akan otomatis dilewati.
2. **Flag Deduplication & Escalating Cooldown**:
   Agent memiliki mekanisme pencegahan pengiriman flag yang sama berulang kali dan jeda cooldown bertahap, sehingga tim tidak akan terkena penalti rate-limit atau ban dari platform CTFd.
3. **Mengecek Rekap Skor Tim & Laporan Visual**:
   Setiap anggota tim dapat memeriksa status pengerjaan kapan saja:
   ```bash
   # Ringkasan di terminal:
   make report

   # Hasilkan laporan visual Dark Mode HTML siap buka di browser:
   make report-html
   ```

---

## 🌿 Kolaborasi Script & Eksploit via Git

Setiap kali anggota tim menemukan eksploit atau script pemecah khusus (misalnya skrip pwntools `.py`):
1. Simpan script di direktori `challenges/<nama-soal>/workspace/solusi.py`.
2. Commit dan push ke branch tim:
   ```bash
   git checkout -b feat/solusi-<nama-soal>
   git add challenges/<nama-soal>/
   git commit -m "feat(exploit): skrip ROP chain untuk pwn-heap"
   git push origin feat/solusi-<nama-soal>
   ```
3. Rekan tim lain dapat langsung menguji script tersebut di dalam sandbox menggunakan:
   ```bash
   uv run ctf-solve --challenge challenges/<nama-soal> --sandbox-mode local
   ```
