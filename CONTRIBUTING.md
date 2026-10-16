# 🤝 Panduan Kontribusi & Kolaborasi Git (CONTRIBUTING)

Terima kasih telah tertarik untuk berkontribusi pada proyek **Agent CeTeEf (agentceteef)**! Dokumen ini berisi panduan standar alur kerja Git, konvensi penulisan kode, dan tata cara kolaborasi tim.

---

## 📌 Alur Kerja Kolaborasi Git (Git Workflow)

Kami menggunakan alur kerja berbasis branch (*Feature Branch Workflow*) dengan cabang utama `main`:

```text
main (stabil)
   │
   ├── feat/tambah-provider-groq ──────┐ (Pull Request & Review)
   │                                   ▼
   ├────────────────────────────> merge ke main
   │
   └── fix/loop-detect-threshold ──────┐ (Pull Request & Review)
                                       ▼
   └────────────────────────────> merge ke main
```

### 1. Persiapan Branch
Jangan pernah melakukan commit langsung ke branch `main` untuk fitur baru atau refaktorisasi besar. Selalu buat branch baru dari `main` terbaru:

```bash
# Pastikan branch main terbaru
git checkout main
git pull origin main

# Buat branch baru dengan nama yang deskriptif
git checkout -b feat/nama-fitur-baru
# Contoh lain:
# git checkout -b fix/perbaikan-bug-sandbox
# git checkout -b solver/integrasi-deepseek-r1
```

### 2. Standar Penamaan Branch
Gunakan awalan berikut untuk mempermudah identifikasi:
- `feat/` : Penambahan fitur baru (misal: `feat/universal-coordinator`).
- `fix/` : Perbaikan bug atau kegagalan eksekusi (misal: `fix/docker-timeout-kill`).
- `solver/`: Penambahan atau penyesuaian agent solver model (misal: `solver/antigravity-streaming`).
- `tool/` : Penambahan tool analisis CTF baru (misal: `tool/angr-symexec`).
- `docs/` : Perubahan dokumentasi atau panduan (misal: `docs/panduan-kolaborasi`).
- `test/` : Penambahan unit test atau fixture (misal: `test/sandbox-concurrency`).

---

## 📝 Konvensi Pesan Commit (Conventional Commits)

Gunakan format pesan commit terstruktur dalam bahasa Indonesia atau Inggris standar:

```text
<tipe>: <deskripsi singkat perubahan>

[deskripsi tambahan jika diperlukan]
```

### Daftar Tipe Commit:
- **`feat:`** Fitur atau kemampuan baru bagi pengguna.
- **`fix:`** Perbaikan bug pada sistem atau tool.
- **`docs:`** Pembaruan dokumentasi (README, panduan kontribusi, komentar kode).
- **`refactor:`** Perubahan struktur kode tanpa mengubah fungsionalitas eksternal.
- **`test:`** Menambahkan atau memperbaiki unit test.
- **`chore:`** Pemeliharaan dependensi, Makefile, skrip CI/CD, atau konfigurasi repo.

*Contoh Commit yang Baik:*
```bash
git commit -m "feat(solver): tambahkan streaming output dan early exit pada AntigravitySolver"
git commit -m "fix(sandbox): tangani error saat Docker daemon tidak merespons"
git commit -m "test(helpers): tambahkan pengujian decode otomatis dan entropy"
```

---

## 🧪 Pengujian & Kualitas Kode Sebelum Commit

Sebelum membuat Pull Request atau meminta review, pastikan:

1. **Jalankan Seluruh Test Suite**:
   ```bash
   make test
   # atau: uv run pytest -v
   ```
   *Seluruh pengujian harus berstatus **PASSED** (100%).*

2. **Pastikan Format & Lint Bersih**:
   ```bash
   make lint
   # atau: uv run ruff check backend tests
   ```

3. **Tambahkan Pengujian Baru**:
   Jika Anda menambahkan modul atau fungsi baru, wajib menyertakan unit test terkait di folder [`tests/`](tests/).

---

## 🚀 Mengajukan Pull Request (PR)

1. Push branch Anda ke remote repository:
   ```bash
   git push origin feat/nama-fitur-baru
   ```
2. Buka repository [BBB30011/agentceteef](https://github.com/BBB30011/agentceteef) di GitHub dan klik **Compare & pull request**.
3. Isi deskripsi PR menggunakan template yang disediakan di [`.github/pull_request_template.md`](.github/pull_request_template.md).
4. Minta review dari rekan tim (minimal 1 approval sebelum merge ke `main`).

---

## 💡 Panduan Arsitektur & Ekstensi Kode

### Menambahkan Model Provider Baru di [`backend/models.py`](backend/models.py)
1. Daftarkan spesifikasi provider di fungsi `resolve_model(spec, settings)`.
2. Tentukan ukuran konteks di `CONTEXT_WINDOWS` dan kemampuan gambar di `VISION_MODELS`.
3. Tambahkan pendeteksian kunci API di fungsi `auto_detect_default_models(settings)`.

### Menambahkan Solver Baru di [`backend/agents/`](backend/agents/)
1. Implementasikan kelas solver yang mengadopsi `SolverProtocol` (`start`, `bump`, `run_until_done_or_gave_up`, `stop`).
2. Hubungkan solver ke pabrik solver di [`backend/agents/swarm.py`](backend/agents/swarm.py).

### Menambahkan Helper Tool Baru di [`backend/tools/ctf_helpers.py`](backend/tools/ctf_helpers.py)
1. Tulis fungsi async murni yang menerima argumen `sandbox` dan parameter analisis.
2. Daftarkan wrapper Pydantic AI di [`backend/tools/sandbox.py`](backend/tools/sandbox.py).
3. Sertakan tool tersebut di `_build_toolset` pada [`backend/agents/solver.py`](backend/agents/solver.py).
