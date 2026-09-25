# LiPowerline Report Splitter

Implementasi awal milestone CLI dalam [PRD](docs/PRD.md): satu consolidated DOCX → deteksi span → satu DOCX per span. Pemrosesan lokal tanpa Microsoft Word, upload, atau telemetry.

## Instalasi

Python 3.12+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
```

Untuk Windows PowerShell, ikuti panduan tanpa aktivasi di bawah.

## Cara menjalankan contoh report1 (Ubuntu)

Setelah instalasi, jalankan perintah berikut di terminal untuk memproses semua DOCX di `doc-source/report1`:

```bash
cd ~/span-report-spliter
source .venv/bin/activate

for file in doc-source/report1/*.docx; do
  name=$(basename "$file" .docx)
  python splitter.py \
    --input "$file" \
    --output "output/report1-complete/$name" \
    --resume
done
```

Buka folder hasil:

```bash
xdg-open output/report1-complete
```

Setiap jenis laporan memiliki folder sendiri. Hasil menyertakan cover/pembuka yang tersedia di sumber dan rekap yang disesuaikan per span atau menara. Tower Inclination dan Tower Nominal Height tetap menghasilkan satu file per menara.

`--resume` melewati output yang sudah valid dengan status `SKIPPED` dan memproses output yang belum ada. File sumber tidak diubah. Jika source atau konfigurasi berubah sejak pemrosesan sebelumnya, gunakan folder output baru.

## Windows PowerShell tanpa aktivasi

Buka PowerShell di folder proyek. Cara ini langsung menggunakan Python di `.venv`, sehingga tidak perlu menjalankan `Activate.ps1` atau mengubah execution policy ketika muncul error `running scripts is disabled on this system`.

**Setup pertama kali** (Python 3.12+ dengan perintah `py` tersedia):

```powershell
py -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Jika `.venv` Windows dan dependensinya sudah tersedia, lewati setup. Virtual environment dari Ubuntu tidak bisa dipakai langsung di Windows; buat `.venv` baru di Windows.

**Cek deteksi tanpa membuat output:**

```powershell
Get-ChildItem -Path "doc-source/report1/*.docx" -File | ForEach-Object {
    & .\.venv\Scripts\python.exe splitter.py --input $_.FullName --analyze
}
```

**Proses semua dokumen:**

```powershell
Get-ChildItem -Path "doc-source/report1/*.docx" -File | ForEach-Object {
    & .\.venv\Scripts\python.exe splitter.py --input $_.FullName --output "output/report1-complete/$($_.BaseName)" --resume
}
```

`--resume` melewati hasil yang sudah valid dengan status `SKIPPED` dan memproses output yang belum ada. Jika source atau konfigurasi berubah, gunakan folder output baru.

**Buka folder hasil:**

```powershell
explorer .\output\report1-complete
```

## Penggunaan

Analisis tanpa membuat output:

```bash
python splitter.py --input input.docx --analyze
```

Split ke direktori khusus untuk satu source:

```bash
python splitter.py --input input.docx --output ./output
```

Lanjutkan atau retry output yang belum ada:

```bash
python splitter.py --input input.docx --output ./output --resume
```

Bisa juga memakai `python -m app.main` atau `span-splitter` setelah instalasi. Progress dikirim ke stderr dan ringkasan JSON ke stdout. Exit code: `0` berhasil; `1` terdapat span gagal/duplikat atau tidak ada span saat analisis; `2` input, konfigurasi, atau job tidak dapat dijalankan.

Output:

```text
output/
├── T001-T002.docx
├── T002-T003.docx
├── processing_log.csv
├── validation_report.csv
├── project_summary.json
└── processing_state.json
```

`processing_log.csv` menyimpan riwayat setiap percobaan; validation dan summary menjelaskan percobaan terakhir. `passed = generated + skipped`. `SKIPPED` berarti output sebelumnya lolos pemeriksaan hash dan package saat resume. Semua kemunculan ID duplikat ditandai gagal; span lain tetap diproses.

Resume memeriksa hash source, konfigurasi, dan setiap output. Output yang sudah ada tidak ditimpa. Jika output rusak/diubah, pindahkan file tersebut secara manual sebelum retry. Jika proses mati setelah publikasi DOCX tetapi sebelum penyimpanan state, file itu juga perlu dipindahkan sebelum retry karena belum terverifikasi dalam state. Jika proses dihentikan paksa, hapus `.processing.lock` **hanya setelah memastikan proses lama sudah berhenti**.

## Konfigurasi deteksi

`app/core/profiles.yaml` memilih aturan berdasarkan nama enam tipe laporan LiPowerline yang sudah diuji. Jika tidak cocok, CLI menggunakan aturan generik. Gunakan `--config config/default.yaml` untuk memaksa aturan generik atau berikan YAML sendiri. `--analyze` menampilkan `profile` dan `entity_kind`.

Aturan yang dapat diubah tanpa mengubah kode:

- `start_after`: regex seluruh paragraf penanda awal bagian detail; tabel rekap sebelum penanda tidak dijadikan boundary.
- `table_column`: indeks kolom mulai dari 0; jika diisi, deteksi memakai sel pada baris kedua tabel detail, bukan paragraf. Seluruh tabel tetap disalin.
- `merge_consecutive`: menggabungkan detail berurutan dengan ID sama, misalnya beberapa fasa/titik bahaya. ID yang muncul lagi setelah ID lain tetap dianggap duplikat.
- `entity_kind`: `span` atau `tower`, untuk membedakan identitas pasangan tower dengan menara tunggal.
- `span_patterns`: regex case-insensitive yang mencocokkan seluruh paragraf atau sel terpilih. Gunakan named groups `start` dan `end` untuk pasangan tower, atau `id` untuk span tunggal; nilainya harus angka.
- `heading_only`: membatasi pencarian ke style ID yang terdaftar di `heading_styles`.
- `closing_patterns`: regex seluruh paragraf untuk menghentikan span terakhir sebelum appendix/penutup.
- `include_preamble`: menyertakan isi sebelum span pertama di setiap output; default generik `false`, profil enam laporan `true`.
- `personalize_preamble`: menyaring rekap, menghitung total Clearance, serta menyesuaikan identitas cover/header. Aktif pada enam profil bawaan. Memerlukan `include_preamble: true`; aturan personalisasi mengikuti struktur template yang sudah diuji.
- `number_width`: padding angka; default `3`.
- `output_template`: nama file aman, misalnya `ProjectA_{span_id}.docx`.

`Tower001-Tower002`, `T.001 – T.002`, dan `001-002` dinormalisasi menjadi `T001-T002`. `Span No. 001` menjadi `Span_001`; keduanya tidak dipetakan satu sama lain tanpa data pasangan tower. Paragraf style TOC dan field instruction diabaikan saat deteksi.

## Cara kerja dan batasan

Engine mempertahankan elemen OpenXML asli, termasuk tabel, drawing, paragraph formatting, styles, numbering, page setup, serta header/footer yang diwariskan antarseksi. Package output mengikuti graph relationship; gambar/header/footer/chart yang direferensikan langsung oleh span lain dibuang. Media disalin dengan buffer 1 MB; isi media tidak dimuat seluruhnya ke RAM. XML utama tetap dimuat dalam memori, dan satu output diproses setiap saat.

Output diperiksa menggunakan CRC ZIP, parsing XML, dan keberadaan target relationship internal sebelum dipublikasikan secara atomik tanpa overwrite. Validasi ini **bukan** pengganti pemeriksaan visual di Microsoft Word.

Batasan milestone ini:

- Satu input per proses/output directory. Enam report type, mapping lintas report, dan GUI PySide6 belum dibuat sesuai urutan milestone PRD.
- Boundary pada paragraf langsung di body atau tabel detail melalui profil. Text box, content control, serta pemisahan baris dalam satu tabel rekap besar belum didukung.
- Mendukung namespace WordprocessingML transitional; Strict OOXML belum didukung.
- Heading detection memakai style ID eksplisit, belum menelusuri pewarisan style atau outline level.
- Part global seperti numbering, comments, dan footnotes dipertahankan secara konservatif beserta dependensinya, sehingga media di part global dapat tetap terbawa walaupun tidak dipakai span tertentu.
- Field, TOC, nomor halaman, dan cross-reference tidak dihitung ulang. Jika preamble disertakan, TOC asli bisa menunjuk ke konten yang sudah dipisah.
- Posisi floating object dan pagination bergantung pada Word/font. Target kemiripan visual ≥95% dan kemampuan dibuka tanpa repair di Microsoft Word belum diverifikasi pada laporan LiPowerline asli.
- Source tidak ditulis oleh aplikasi. Hindari mengedit source dengan aplikasi lain selama pemrosesan.

## Pengujian

```bash
python -m pytest -q
SPAN_STRESS_TEST=1 python -m pytest -q tests/test_splitter.py::test_large_report
```

Uji default mencakup 120 span, normalisasi, gambar selektif, tabel, style, section layout, inherited header, duplikat, source protection, kegagalan satu span, dan resume. Stress test opt-in menghasilkan DOCX sintetis >85 MB berisi 150 span dengan gambar unik serta tabel; membutuhkan ruang disk sementara sekitar 200 MB atau lebih. Fixtures dibuat di direktori sementara pytest.

Validasi lanjutan membutuhkan sample LiPowerline asli: sesuaikan parser terhadap heading nyata, bandingkan output secara visual di Word, dan periksa chart, floating image, serta section kompleks sebelum dipakai untuk delivery.

## Struktur kode

- `app/core/config.py`: konfigurasi dan validasi aturan.
- `app/core/detection.py`: deteksi, normalisasi, dan batas span.
- `app/core/package.py`: parsing OPC/OpenXML, section, graph media, penulisan dan validasi package.
- `app/core/personalization.py`: personalisasi cover/informasi, penyaringan rekap termasuk sel gabungan, dan perhitungan total per entitas.
- `app/services/processing.py`: orkestrasi, log, summary, dan state resume.
- `app/main.py`: CLI.


## Contoh enam laporan di doc-source/report1

Jalankan tanpa `--config` agar profil laporan dipilih otomatis:

```bash
source .venv/bin/activate
for file in doc-source/report1/*.docx; do
  python splitter.py --input "$file" --analyze
done
```

Hasil deteksi pada contoh lokal:

| Profil | Unit | Jumlah |
| --- | --- | ---: |
| clearance | Span | 95 |
| sag | Span | 152 |
| phase_spacing | Span | 138 |
| sections | Span | 152 |
| tower_inclination | Menara | 156 |
| tower_height | Menara | 157 |

Jumlah berasal dari detail dokumen, bukan rentang angka dalam nama file. Laporan menara menghasilkan `Tower_001.docx`, sedangkan laporan span menghasilkan `T001-T002.docx`. Menara belum dipetakan ke kedua span yang bersebelahan. Profil enam laporan kini menyertakan bagian pembuka sumber, cover, informasi proyek, dan tabel rekap yang disaring khusus untuk span/menara terkait. Total Clearance dihitung ulang dari baris rekap terpilih. Identitas cover dan header disesuaikan. Informasi umum, legenda, serta referensi tetap dipertahankan. File Sections tidak memiliki cover/rekap di sumber sehingga hanya bagian pembuka yang tersedia yang disertakan.

Proses keenam laporan secara berurutan, dengan direktori terpisah:

```bash
for file in doc-source/report1/*.docx; do
  name=$(basename "$file" .docx)
  python splitter.py --input "$file" --output "output/report1-complete/$name" --resume
done
```

`--resume` juga dapat digunakan pada direktori baru. Jika direktori berisi run dengan konfigurasi versi lama, gunakan direktori baru. File hasil yang sudah diverifikasi akan dilewati. Profil ini mengikuti caption bahasa Indonesia pada contoh; template/bahasa lain mungkin membutuhkan penyesuaian YAML.


### Hasil laporan lengkap

Hasil terbaru untuk contoh lokal disimpan di `output/report1-complete`, terpisah dari hasil detail-only terdahulu di `output/report1`. Jalankan ulang dengan folder baru jika menggunakan hasil yang konfigurasi parsernya sudah berubah; `--resume` tidak mengganti output konfigurasi lama.

```bash
xdg-open output/report1-complete
```

Nomor record/caption asli dipertahankan agar tetap dapat ditelusuri ke sumber. Angka pengukuran tidak dihitung ulang; yang berubah adalah cakupan baris dan total rekap. Dua laporan menara tetap satu file per menara. Jika struktur rekap tidak dikenali atau jumlah baris rekap tidak cocok dengan detail, span ditandai gagal dan alasannya dicatat, bukan menghasilkan rekap yang tidak lengkap.
