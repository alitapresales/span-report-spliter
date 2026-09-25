# Product Requirements Document

## LiPowerline Automated Span Report Splitter

**Version:** 1.0
**Product Type:** Local Desktop / Local Processing Application
**Primary Use Case:** Automated splitting of LiPowerline-generated Word reports into individual reports per span
**Primary Users:** Survey Engineer, LiDAR Engineer, Powerline Analyst, Project Engineer, Document Controller

---

# 1. Product Overview

LiPowerline digunakan untuk melakukan processing dan analysis terhadap data Drone LiDAR pada jaringan transmisi listrik.

Untuk satu project, hasil processing LiPowerline dapat menghasilkan beberapa jenis laporan Word.

Dalam satu project terdapat hingga **6 tipe report berbeda**.

Contoh input:

* `Report_Type_1.docx`
* `Report_Type_2.docx`
* `Report_Type_3.docx`
* `Report_Type_4.docx`
* `Report_Type_5.docx`
* `Report_Type_6.docx`

Setiap file report dapat memiliki:

* lebih dari 100 span;
* ukuran dokumen hingga sekitar 85 MB atau lebih;
* banyak gambar;
* banyak tabel;
* heading;
* caption;
* chart;
* hasil analisis teknis;
* embedded media.

Saat ini LiPowerline menghasilkan laporan dalam bentuk consolidated report.

Contoh:

**Report Type 1**

* Span 001
* Span 002
* Span 003
* ...
* Span 120

berada dalam satu file Word.

Kebutuhan bisnis adalah mengubah output tersebut menjadi laporan individual per span tanpa melakukan perubahan terhadap proses maupun aplikasi LiPowerline.

Aplikasi ini akan bertindak sebagai **post-processing layer** setelah LiPowerline.

---

# 2. Problem Statement

Saat ini satu laporan LiPowerline dapat berisi lebih dari 100 span.

Untuk kebutuhan delivery, engineering review, maintenance, archive, dan document management, setiap span perlu memiliki report tersendiri.

Jika proses pemisahan dilakukan secara manual menggunakan Microsoft Word, terdapat beberapa masalah:

* membutuhkan waktu sangat lama;
* rentan human error;
* sulit dilakukan untuk ratusan span;
* format dokumen dapat berubah;
* gambar atau tabel dapat terpotong;
* penamaan file tidak konsisten;
* sulit memastikan semua span sudah ter-generate;
* pengerjaan berulang untuk 6 tipe report;
* Microsoft Word dapat menjadi lambat pada file besar.

Sebagai contoh:

120 span × 6 tipe report = **720 individual Word reports**.

Melakukan pekerjaan tersebut secara manual tidak efisien.

---

# 3. Product Objective

Membangun aplikasi yang dapat secara otomatis:

1. menerima hingga 6 consolidated Word report;
2. mendeteksi tipe report;
3. mendeteksi seluruh span di dalam setiap report;
4. mengenali batas awal dan akhir setiap span;
5. memisahkan isi report berdasarkan span;
6. mempertahankan format asli report;
7. menggabungkan hasil berdasarkan Span ID;
8. menghasilkan satu folder untuk setiap span;
9. menyimpan 6 jenis report di dalam folder span yang sama;
10. menghasilkan processing log dan validation summary.

LiPowerline tidak perlu dimodifikasi.

---

# 4. High-Level Workflow

```text
Drone LiDAR Survey
        ↓
LiPowerline Processing
        ↓
LiPowerline Generates Reports
        ↓
6 Consolidated DOCX Reports
        ↓
Automated Span Report Splitter
        ↓
Report Type Detection
        ↓
Span Detection
        ↓
Document Segmentation
        ↓
Content Preservation
        ↓
Span Mapping
        ↓
Individual DOCX Generation
        ↓
Validation
        ↓
Output Folder per Span
```

---

# 5. Example Input

Satu project dapat mempunyai input seperti:

```text
Input/
├── Report_Type_1.docx
├── Report_Type_2.docx
├── Report_Type_3.docx
├── Report_Type_4.docx
├── Report_Type_5.docx
└── Report_Type_6.docx
```

Contoh:

`Report_Type_1.docx`

berisi:

```text
Cover
Table of Contents

Span Tower001 - Tower002
[Text]
[Image]
[Table]
[Analysis]

Span Tower002 - Tower003
[Text]
[Image]
[Table]
[Analysis]

...

Span Tower120 - Tower121
```

---

# 6. Expected Output

Aplikasi menghasilkan struktur:

```text
Output/
├── Span_Tower001-Tower002/
│   ├── Type_1.docx
│   ├── Type_2.docx
│   ├── Type_3.docx
│   ├── Type_4.docx
│   ├── Type_5.docx
│   └── Type_6.docx
│
├── Span_Tower002-Tower003/
│   ├── Type_1.docx
│   ├── Type_2.docx
│   ├── Type_3.docx
│   ├── Type_4.docx
│   ├── Type_5.docx
│   └── Type_6.docx
│
└── ...
```

Optional output:

```text
Output/
├── Span Reports/
├── processing_log.csv
├── validation_report.csv
└── project_summary.json
```

---

# 7. Core Concept

Aplikasi tidak melakukan perubahan terhadap:

* LiPowerline;
* workflow analysis;
* LiDAR data;
* engineering calculation.

Aplikasi hanya melakukan:

**Document Post Processing**

dengan fungsi utama:

```text
Parse
→ Detect
→ Split
→ Map
→ Generate
→ Validate
```

---

# 8. Functional Requirements

## FR-01 – Project Creation

User dapat membuat project baru.

Data minimum:

* Project Name
* Project Code
* Input Folder
* Output Folder

Contoh:

```text
Project Name:
PLN Transmission Line Survey

Project Code:
PLN-JBR-001
```

---

# 9. FR-02 – Input File Selection

Aplikasi harus mendukung:

* single file selection;
* multiple file selection;
* folder selection;
* drag and drop.

Supported initial format:

`.docx`

Jumlah input:

1–6 report utama.

Aplikasi harus tetap dapat berjalan apabila beberapa tipe report tidak tersedia.

Contoh:

```text
Type 1 ✓
Type 2 ✓
Type 3 ✓
Type 4 -
Type 5 ✓
Type 6 -
```

---

# 10. FR-03 – Report Type Detection

Aplikasi harus dapat menentukan tipe report.

Detection dapat menggunakan:

* filename;
* title;
* heading;
* keyword;
* document structure;
* configurable rule.

Contoh konfigurasi:

```text
TYPE_1:
Keyword: "Clearance Analysis"

TYPE_2:
Keyword: "Vegetation Analysis"

TYPE_3:
Keyword: "Sag Analysis"
```

Detection harus menggunakan rule-based configuration sehingga tidak hardcoded sepenuhnya.

---

# 11. FR-04 – Span Detection

Aplikasi harus mendeteksi Span ID.

Contoh format yang mungkin:

```text
Span 001
SPAN 001
Span No. 001

Tower 001 - Tower 002
T001-T002
T.001 – T.002
```

Span Detector harus mendukung:

* exact keyword;
* regex;
* heading detection;
* custom parsing rules.

Contoh Regex:

```text
Span\s*\d+
```

atau:

```text
Tower\s*(\d+)\s*[-–]\s*Tower\s*(\d+)
```

---

# 12. FR-05 – Span Boundary Detection

Setelah menemukan Span ID, aplikasi harus menentukan:

**Start Boundary**

dan

**End Boundary**

untuk setiap span.

Contoh:

```text
SPAN 001
↓
content
content
content
↓
SPAN 002
```

Maka konten:

```text
SPAN 001
sampai sebelum
SPAN 002
```

menjadi:

`Span_001.docx`

Span terakhir berakhir pada:

* end of document; atau
* section penutup tertentu.

---

# 13. FR-06 – Content Preservation

Output harus mempertahankan sebisa mungkin:

* text;
* font;
* font size;
* paragraph alignment;
* heading;
* bold;
* italic;
* numbering;
* bullet;
* table;
* image;
* image size;
* image position;
* caption;
* page break;
* section break;
* header;
* footer;
* page orientation;
* margins.

Target fidelity:

**≥95% visual similarity dengan source document.**

---

# 14. FR-07 – Embedded Media Handling

Dokumen besar dapat mempunyai ratusan gambar.

Aplikasi harus:

* mendeteksi image relationship;
* hanya membawa media yang digunakan oleh span tersebut;
* tidak menduplikasi semua image ke semua output;
* mempertahankan relationship ID yang benar.

Hal ini penting untuk mengurangi ukuran output.

---

# 15. FR-08 – Span Mapping

Setelah keenam report diproses, aplikasi harus mencocokkan hasil berdasarkan **Span Key**.

Contoh:

```text
T001-T002
```

harus menghubungkan:

```text
Report Type 1
Report Type 2
Report Type 3
Report Type 4
Report Type 5
Report Type 6
```

menjadi:

```text
Span_T001-T002/
```

---

# 16. FR-09 – Span Normalization

Karena format nama span dapat berbeda antar report, sistem harus mempunyai normalization engine.

Contoh:

```text
TOWER 001 - TOWER 002
Tower001-Tower002
T001-T002
001-002
```

dapat dinormalisasi menjadi:

```text
T001-T002
```

---

# 17. FR-10 – Output File Naming

Format default:

```text
{ProjectCode}_{SpanID}_{ReportType}.docx
```

Contoh:

```text
PLN-JBR-001_T001-T002_Type01.docx
```

User dapat memilih format alternatif:

```text
Type01_T001-T002.docx
```

atau:

```text
T001-T002_ClearanceReport.docx
```

---

# 18. FR-11 – Output Folder Structure

Default:

```text
Project/
   Span/
      Reports
```

Contoh:

```text
PLN-JBR-001/
└── T001-T002/
    ├── Type01.docx
    ├── Type02.docx
    ├── Type03.docx
    ├── Type04.docx
    ├── Type05.docx
    └── Type06.docx
```

Alternative output mode:

```text
Project/
   Report Type/
      Span
```

Harus dapat dikonfigurasi.

---

# 19. FR-12 – Preview Before Processing

Sebelum melakukan split, aplikasi menampilkan:

```text
Project: PLN-JBR-001

Detected Reports:
6

Type 1
File Size: 84.8 MB
Detected Span: 127

Type 2
File Size: 71.2 MB
Detected Span: 127

Type 3
File Size: 69.5 MB
Detected Span: 127
```

Jika jumlah span tidak sama:

```text
WARNING

Type 1: 127
Type 2: 127
Type 3: 126
```

User harus dapat melihat span yang missing.

---

# 20. FR-13 – Batch Processing

Processing harus dilakukan dalam batch.

Untuk setiap file:

```text
Parse file
→ detect spans
→ split
→ generate
→ release memory
→ process next file
```

Jangan memuat seluruh 6 file besar secara bersamaan ke memory apabila tidak diperlukan.

---

# 21. FR-14 – Progress Monitoring

UI menampilkan:

```text
Processing Report Type 2

Span 43 of 127

34%

Current:
T043-T044
```

Status:

* Pending
* Processing
* Completed
* Warning
* Failed

---

# 22. FR-15 – Validation

Setelah processing, aplikasi melakukan validation.

Validation minimum:

### Input span count

vs

### output span count

Contoh:

```text
Type 1

Detected: 127
Generated: 127
Passed: 127
Failed: 0
```

---

# 23. FR-16 – Cross Report Validation

Sistem harus membandingkan Span ID antar tipe report.

Contoh:

| Span      | T1 | T2 | T3 | T4 | T5 | T6 |
| --------- | -- | -- | -- | -- | -- | -- |
| T001-T002 | ✓  | ✓  | ✓  | ✓  | ✓  | ✓  |
| T002-T003 | ✓  | ✓  | ✓  | ✓  | ✓  | ✓  |
| T003-T004 | ✓  | ✓  | ✗  | ✓  | ✓  | ✓  |

Missing report harus diberi warning.

Tidak boleh menghentikan seluruh processing.

---

# 24. FR-17 – Processing Log

Generate:

`processing_log.csv`

Contoh:

```text
timestamp
project
source_file
report_type
span_id
status
output_file
error_message
```

Contoh:

```text
2026-09-25 10:10
PLN-JBR-001
Type03.docx
TYPE03
T037-T038
SUCCESS
T037-T038/Type03.docx
-
```

---

# 25. FR-18 – Error Handling

Aplikasi tidak boleh berhenti seluruhnya jika satu span gagal.

Contoh:

```text
Span 001 PASS
Span 002 PASS
Span 003 FAILED
Span 004 PASS
```

Setelah processing selesai:

```text
126 Success
1 Failed
```

User dapat melakukan:

**Retry Failed Span**

tanpa memproses ulang semuanya.

---

# 26. FR-19 – Duplicate Span Handling

Jika source memiliki duplicate Span ID:

```text
T001-T002
T001-T002
```

aplikasi tidak boleh overwrite otomatis.

Berikan:

```text
Duplicate Span Detected
```

dan masukkan ke validation log.

---

# 27. FR-20 – Resume Processing

Untuk dataset besar, aplikasi harus mendukung resume.

Jika aplikasi berhenti saat:

```text
Span 76 / 130
```

user dapat menjalankan kembali project dan melanjutkan dari output yang belum selesai.

Output yang sudah valid tidak perlu dibuat ulang.

---

# 28. Functional Modules

Aplikasi mempunyai module berikut:

```text
Project Manager
      ↓
File Manager
      ↓
Report Type Detector
      ↓
DOCX Parser
      ↓
Span Detector
      ↓
Span Normalizer
      ↓
Span Boundary Engine
      ↓
Document Splitter
      ↓
Media Relationship Manager
      ↓
DOCX Generator
      ↓
Span Mapper
      ↓
Validation Engine
      ↓
Logging Engine
```

---

# 29. Technical Architecture

Recommended initial architecture:

```text
Desktop UI
   ↓
Application Controller
   ↓
Processing Engine
   ├── Report Detector
   ├── Span Detector
   ├── DOCX Parser
   ├── OpenXML Manipulator
   ├── Media Manager
   └── DOCX Generator
   ↓
Local File System
```

Tidak memerlukan server untuk MVP.

---

# 30. Recommended Technology Stack

## Language

Python 3.12+

## Desktop GUI

Preferred:

```text
PySide6
```

Alternative:

```text
Tkinter
```

PySide6 lebih disarankan untuk UI production.

---

# 31. DOCX Processing Strategy

DOCX pada dasarnya merupakan ZIP package berisi:

```text
word/
    document.xml
    styles.xml
    numbering.xml
    media/
    _rels/
```

Untuk dokumen besar, gunakan kombinasi:

```text
zipfile
lxml
OpenXML structure manipulation
```

Library:

```text
lxml
python-docx
```

`python-docx` dapat digunakan sebagai helper tetapi core splitting disarankan bekerja pada OpenXML.

---

# 32. Important Development Rule

JANGAN melakukan teknik:

```text
Open source Word
Copy
Paste into new Word
Save
```

melalui Microsoft Word automation.

Core engine harus dapat bekerja tanpa membuka Microsoft Word.

---

# 33. Performance Requirement

Minimum target:

### Input

* DOCX hingga 100 MB;
* 150+ spans;
* 6 report types;
* ratusan hingga ribuan gambar.

### Target behavior

* aplikasi tidak freeze;
* memory usage terkendali;
* processing berjalan sequential;
* UI tetap responsive;
* progress dapat dilihat.

---

# 34. Memory Management

File besar tidak boleh semuanya disimpan penuh di RAM secara bersamaan.

Gunakan:

* sequential processing;
* temporary working directory;
* selective media extraction;
* cleanup setelah file selesai diproses.

Contoh:

```text
Process Type 1
release
Process Type 2
release
...
```

---

# 35. Threading

Processing harus berjalan di worker thread.

UI thread hanya menangani interface.

Contoh:

```text
Main Thread
    UI

Worker Thread
    DOCX processing
```

User interface tidak boleh menjadi `Not Responding`.

---

# 36. Configuration-Driven Parser

Karena terdapat 6 report type, parser tidak boleh sepenuhnya hardcoded.

Gunakan file konfigurasi:

```text
config/
    report_type_1.yaml
    report_type_2.yaml
    report_type_3.yaml
    report_type_4.yaml
    report_type_5.yaml
    report_type_6.yaml
```

Contoh:

```yaml
report_type: TYPE_1

detection:
  keywords:
    - "Clearance Report"

span_detection:
  regex:
    - "Tower\\s*(\\d+)\\s*-\\s*Tower\\s*(\\d+)"

output_name:
  template: "{span_id}_Type01.docx"
```

Dengan konsep ini perubahan template LiPowerline tidak selalu membutuhkan perubahan source code.

---

# 37. Suggested Repository Structure

```text
lipowerline-report-splitter/

├── app/
│   ├── main.py
│   │
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── project_view.py
│   │   └── progress_view.py
│   │
│   ├── core/
│   │   ├── report_detector.py
│   │   ├── docx_parser.py
│   │   ├── span_detector.py
│   │   ├── span_normalizer.py
│   │   ├── span_splitter.py
│   │   ├── media_manager.py
│   │   ├── docx_generator.py
│   │   ├── span_mapper.py
│   │   └── validator.py
│   │
│   ├── models/
│   │   ├── project.py
│   │   ├── report.py
│   │   └── span.py
│   │
│   ├── services/
│   │   ├── processing_service.py
│   │   └── logging_service.py
│   │
│   └── utils/
│
├── config/
│   ├── type01.yaml
│   ├── type02.yaml
│   ├── type03.yaml
│   ├── type04.yaml
│   ├── type05.yaml
│   └── type06.yaml
│
├── tests/
│
├── samples/
│
├── requirements.txt
├── README.md
└── pyproject.toml
```

---

# 38. User Interface

Main page:

```text
--------------------------------------------------

LiPowerline Report Splitter

Project Name:
[_______________________________]

Input Reports:

Type 1    [Select File] ✓
Type 2    [Select File] ✓
Type 3    [Select File] ✓
Type 4    [Select File] ✓
Type 5    [Select File] ✓
Type 6    [Select File] ✓

Output Folder:
[_______________________________]

          [ ANALYZE REPORTS ]

--------------------------------------------------
```

---

# 39. Analysis Screen

Setelah Analyze:

```text
PROJECT ANALYSIS

Report Type     Size       Span
-----------------------------------
Type 1          85 MB      127
Type 2          82 MB      127
Type 3          64 MB      127
Type 4          71 MB      127
Type 5          55 MB      127
Type 6          68 MB      127

Total Span:
127

Expected Files:
762

Status:
READY

              [PROCESS]
```

---

# 40. Processing Screen

```text
Processing...

Report Type 3 / 6

Span:
T057-T058

57 / 127

██████████░░░░░░░░

Elapsed:
...

Success:
56

Failed:
0
```

---

# 41. Completion Screen

```text
PROCESS COMPLETED

Project:
PLN-JBR-001

Spans:
127

Expected:
762 reports

Generated:
760

Missing:
2

Failed:
0

[OPEN OUTPUT FOLDER]

[VIEW VALIDATION]

[EXPORT LOG]
```

---

# 42. MVP Scope

MVP harus fokus pada:

1. select DOCX;
2. detect span menggunakan configurable regex;
3. split document;
4. preserve image and table;
5. output DOCX per span;
6. support 6 report types;
7. map berdasarkan Span ID;
8. generate folder per span;
9. generate CSV validation;
10. progress UI;
11. error logging.

---

# 43. Out of Scope for MVP

Belum diperlukan:

* user management;
* cloud upload;
* database server;
* mobile app;
* LiPowerline API integration;
* direct Drone LiDAR processing;
* AI analysis;
* document OCR;
* PDF splitting;
* collaboration feature;
* web portal.

---

# 44. Phase 2 Features

Setelah MVP stabil:

### PDF Export

DOCX per span dapat otomatis diubah menjadi PDF.

---

### ZIP Export

Satu span:

```text
T001-T002.zip
```

berisi 6 report.

---

### Multi Project Batch

Process beberapa project sekaligus.

---

### Template Management

User dapat membuat parser rule dari UI.

---

### Automatic Report Recognition

Aplikasi mengenali report type tanpa user memilih.

---

### Dashboard

Contoh:

```text
Projects processed: 15
Reports generated: 12,430
Failed: 5
```

---

# 45. Future Architecture

Jika digunakan banyak engineer:

```text
Web Frontend
      ↓
API
      ↓
Job Queue
      ↓
Document Processing Workers
      ↓
Shared Storage
```

Possible stack:

```text
FastAPI
Celery / RQ
Redis
PostgreSQL
Object Storage
```

Tetapi bukan bagian MVP.

---

# 46. Security Requirement

Karena file dapat berisi data engineering infrastructure:

* seluruh processing MVP dilakukan secara local;
* tidak ada file dikirim ke internet;
* tidak ada telemetry file content;
* temporary files harus dihapus setelah selesai;
* original report tidak boleh dimodifikasi.

---

# 47. Data Integrity Requirement

Aplikasi harus mempertahankan source file.

Rule:

```text
READ ONLY INPUT
```

Tidak boleh:

* overwrite;
* rename;
* delete;
* modify;

source LiPowerline report.

---

# 48. Acceptance Criteria

MVP dianggap berhasil jika:

### AC-01

File DOCX 80+ MB dapat diproses tanpa crash.

### AC-02

Dokumen dengan minimum 100 span dapat dideteksi.

### AC-03

Setiap detected span menghasilkan individual DOCX.

### AC-04

Text, image, dan table utama tetap tersedia.

### AC-05

Aplikasi mendukung minimum 6 report type.

### AC-06

Span dari keenam report dapat dipetakan ke folder yang sama.

### AC-07

Aplikasi menghasilkan validation summary.

### AC-08

Jika satu span gagal, keseluruhan job tetap dilanjutkan.

### AC-09

Source Word tidak berubah.

### AC-10

User dapat mengetahui report/span mana yang gagal.

---

# 49. Testing Scenario

## Test 1

```text
1 report
10 span
5 MB
```

Expected:

```text
10 files generated
```

---

## Test 2

```text
6 reports
10 span
```

Expected:

```text
10 folders
60 DOCX
```

---

## Test 3

```text
6 reports
120 span
```

Expected:

```text
120 folders
720 DOCX
```

---

## Test 4

```text
Type 1 = 120 span
Type 2 = 119 span
```

Expected:

System identifies missing span.

---

## Test 5

Large file:

```text
85 MB
150 spans
```

Expected:

No crash.

---

## Test 6

Duplicate Span ID.

Expected:

Warning and no accidental overwrite.

---

# 50. Development Priority

## Priority 1 – Proof of Concept

Build CLI first.

Input:

```bash
python splitter.py \
  --input sample.docx \
  --output ./output
```

Result:

individual span DOCX.

Target utama tahap ini adalah membuktikan bahwa document splitting dapat mempertahankan:

* images;
* tables;
* styles;
* formatting.

---

## Priority 2 – Multi Report

Tambahkan:

* 6 report types;
* normalization;
* mapping;
* validation.

---

## Priority 3 – Desktop UI

Tambahkan:

* PySide6;
* progress;
* project selection;
* processing result.

---

## Priority 4 – Production Hardening

Tambahkan:

* resume;
* logging;
* retry;
* large file optimization;
* corrupted DOCX handling.

---

# 51. Important Engineering Principle

Jangan mulai development dari UI.

Urutan development:

```text
DOCX Parsing
      ↓
Span Detection
      ↓
Span Splitting
      ↓
DOCX Preservation
      ↓
Validation
      ↓
Multi Report Mapping
      ↓
CLI
      ↓
Desktop UI
```

Core technical risk berada pada **DOCX preservation**, bukan pada user interface.

---

# 52. Codex Initial Build Instruction

Gunakan requirement berikut sebagai starting instruction untuk development:

Build a local Python application called `LiPowerline Report Splitter`.

The primary purpose of the application is to process large Microsoft Word `.docx` reports generated by LiPowerline.

Each input document may be between 50–100 MB and may contain more than 100 transmission-line spans.

There can be up to six different report types for the same project.

Each consolidated report contains multiple spans.

The system must identify span boundaries using configurable regex and document heading rules, split each consolidated report into individual `.docx` files for every span, preserve text, tables, images, formatting, headers, footers, page layout, styles, and embedded media as accurately as possible, and organize reports from all report types into folders grouped by normalized Span ID.

Do not use Microsoft Word COM automation as the primary processing mechanism.

Use Python 3.12+, `zipfile`, `lxml`, OpenXML manipulation, and optionally `python-docx` as a helper.

Architecture must separate:

* DOCX parsing;
* span detection;
* span normalization;
* document splitting;
* media relationship handling;
* report type detection;
* output generation;
* validation;
* logging.

Start by building a CLI-based proof of concept before developing the PySide6 desktop interface.

The application must:

* never modify original files;
* support configurable parsing rules;
* process large files sequentially;
* avoid loading unnecessary files simultaneously into memory;
* continue processing when a single span fails;
* provide processing logs;
* validate detected span count against generated span count;
* support resume and retry architecture.

Use clean modular Python architecture, type hints, structured logging, pytest unit tests, and configuration files using YAML.

The first milestone is:

`input.docx → detect all spans → generate one valid DOCX per span`.

Do not build the GUI until this milestone works reliably.

---

# 53. Definition of Done for First Codex Milestone

Codex milestone pertama dianggap selesai apabila:

```text
Input:
1 consolidated LiPowerline DOCX
100+ spans
large images and tables

Output:
100+ DOCX files
```

dengan kondisi:

* jumlah span benar;
* seluruh output dapat dibuka di Microsoft Word;
* gambar tetap tersedia;
* tabel tetap tersedia;
* styles tidak rusak secara signifikan;
* source tidak berubah;
* terdapat processing log;
* failed spans dapat diketahui.

Setelah milestone tersebut berhasil, baru lanjut ke support 6 report types dan folder mapping per span.
