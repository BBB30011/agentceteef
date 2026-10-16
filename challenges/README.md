# 📁 Direktori Tantangan CTF (Challenges)

Direktori ini digunakan untuk menyimpan tantangan CTF lokal yang akan dipecahkan oleh **Agent CeTeEf (agentceteef)**.

---

## 📌 Struktur Folder Tantangan

Setiap tantangan disimpan dalam subdirektori terpisah dengan struktur berikut:

```text
challenges/
└── <nama_tantangan>/
    ├── metadata.yml         # Informasi metadata soal (wajib)
    └── distfiles/           # Berkas pendukung soal (biner, pcap, source code, ciphertext)
```

### Format `metadata.yml`:

```yaml
name: nama_tantangan
category: crypto            # pwn | rev | crypto | web | forensics | misc | osint
value: 100                  # Nilai poin soal
description: |
  Deskripsi soal atau narasi yang diberikan penyelenggara CTF.
  Bisa menyertakan instruksi remote netcat atau endpoint web:
  Contoh: nc 10.10.10.10 1337 atau http://target.ctf.id:8080
tags:
  - web
  - sql-injection
hints:
  - content: Petunjuk pertama jika disediakan oleh panitia.
```

---

## 🚀 Cara Menyerang Tantangan

### 1. Menyerang Satu Soal Secara Mandiri:
```bash
# Menyerang menggunakan preset tokenless ($0 token cost):
./run.sh --challenge challenges/crypto_cascade --profile tokenless --no-submit

# Atau menggunakan permodel tertentu:
./run.sh --challenge challenges/demo_sanity --no-submit
```

### 2. Memilih Tantangan Melalui Menu Interaktif:
```bash
./run.sh
# Pilih opsi '4. Pecahkan 1 Tantangan Spesifik'
```

---

## 📦 Contoh Tantangan Bawaan:
- **`demo_sanity/`**: Tantangan verifikasi dasar (*warm-up*) untuk memastikan sandbox dan pipeline ekstraksi flag bekerja normal.
- **`crypto_cascade/`**: Tantangan kriptografi multi-layer encoding untuk menguji fitur *cascade auto-decoder*.
