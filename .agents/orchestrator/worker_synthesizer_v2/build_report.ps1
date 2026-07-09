$output = 'c:\project\uit\nlp\GLM-OCR\docs\bao_cao_do_an_MLLM_OCR_Tieng_Viet.md'
$drafts = 'c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts'

# ============================================================
# BƯỚC 1: TẠO FILE HEADER (title + mục lục + metadata)
# ============================================================
$header = @'
# Nghiên cứu và Finetune MLLM cho OCR Tiếng Việt — Trường hợp GLM-OCR

**Đồ án môn học** | Tác giả: [Họ tên sinh viên] | MSSV: [xxx] | Niên khóa: 2025-2026

---

## Mục lục

1. [Tóm tắt](#1-tóm-tắt)
2. [Giới thiệu](#2-giới-thiệu)
   - [2.1 Đặt vấn đề OCR tiếng Việt](#21-đặt-vấn-đề-ocr-tiếng-việt)
   - [2.2 Động lực](#22-động-lực)
   - [2.3 Đóng góp của đồ án](#23-đóng-góp-của-đồ-án)
   - [2.4 Cấu trúc báo cáo](#24-cấu-trúc-báo-cáo)
3. [Tổng quan nghiên cứu](#3-tổng-quan-nghiên-cứu)
4. [Phương pháp đề xuất](#4-phương-pháp-đề-xuất)
5. [Thực nghiệm](#5-thực-nghiệm)
6. [Kết quả và Đánh giá](#6-kết-quả-và-đánh-giá)
7. [Phân tích hạn chế](#7-phân-tích-hạn-chế)
8. [Demo](#8-demo)
9. [Kết luận và Hướng phát triển](#kết-luận-và-hướng-phát-triển)
10. [Tài liệu tham khảo](#tài-liệu-tham-khảo)

---

'@
Set-Content -Path $output -Value $header -Encoding UTF8
Write-Host ("[1/4] Header written: {0} bytes" -f (Get-Item $output).Length)

# ============================================================
# BƯỚC 2: CONCAT 4 DRAFTS + APPLY 6 FIXES INLINE
# ============================================================

# --- ch01_ch02.md + Fix 1 (line 61): "trong văn liệu" -> "trong tài liệu" ---
$ch12 = Get-Content "$drafts\ch01_ch02.md" -Raw -Encoding UTF8
$before = ([regex]::Matches($ch12, 'trong văn liệu')).Count
$ch12 = $ch12 -replace 'trong văn liệu', 'trong tài liệu'
$after = ([regex]::Matches($ch12, 'trong văn liệu')).Count
Write-Host ("[Fix 1] ch01_ch02 'trong văn liệu': {0} -> {1} occurrences" -f $before, $after)

# --- ch03_ch04.md + Fix 2 (line 247 S1 YAML) + Fix 3 (line 221 VNExpress) ---
$ch34 = Get-Content "$drafts\ch03_ch04.md" -Raw -Encoding UTF8

# Fix 3 first: "11 ... VNExpress" -> "10 ... VNExpress" (multiple phrasings)
$f3before = ([regex]::Matches($ch34, '11 (nguồn|chủ đề|RSS feeds|Nguồn)\s*VNExpress')).Count
$ch34 = $ch34 -replace '11 (nguồn|chủ đề|RSS feeds|Nguồn)\s*VNExpress', '10 $1 VNExpress'
$ch34 = $ch34 -replace '11 nguồn VNExpress', '10 nguồn VNExpress'
$f3after = ([regex]::Matches($ch34, '11 \w+ VNExpress')).Count
Write-Host ("[Fix 3] ch03_ch04 '11 ... VNExpress': {0} -> {1} remaining" -f $f3before, $f3after)

# Fix 2: S1 YAML num_train_epochs: 1 -> 3
# Strategy: split file at "### 4.6" boundary; the S1 YAML is in section before "Cấu hình Stage 2"
# S1 YAML block is between "### 4.6" and "**Cấu hình Stage 2"
# Simpler: S1 YAML `num_train_epochs: 1` appears once (line 247); S2 YAML `num_train_epochs: 1` (line 275) is CORRECT — keep.
# Use context: S1 block is the first yaml block (Stage 1). Split on "**Cấu hình Stage 2" marker.
$parts = $ch34 -split '(\*\*Cấu hình Stage 2)', 2
$s1part = $parts[0]
$s2part = $parts[1] + $parts[2]
$f2before = ([regex]::Matches($s1part, 'num_train_epochs:\s*1')).Count
$s1part = $s1part -replace 'num_train_epochs:\s*1', 'num_train_epochs: 3'
$f2after = ([regex]::Matches($s1part, 'num_train_epochs:\s*3')).Count
$ch34 = $s1part + $s2part
Write-Host ("[Fix 2] ch03_ch04 S1 num_train_epochs 1->3: {0} replaced, now {1} epoch=3 in S1" -f $f2before, $f2after)

# --- ch05_ch06.md + Fix 4 (line 186 S1 YAML) + Fix 5 (line 22) + Fix 6 (line 126) ---
$ch56 = Get-Content "$drafts\ch05_ch06.md" -Raw -Encoding UTF8

# Fix 5 & 6: "8-9 giờ" / "8–9 giờ" / "8 đến 9 giờ" Stage 1 -> "~25 phút"
$f56before = ([regex]::Matches($ch56, '8[–\-]9 giờ|8 đến 9 giờ')).Count
$ch56 = $ch56 -replace '8[–\-]9 giờ', '~25 phút'
$ch56 = $ch56 -replace '8 đến 9 giờ', '~25 phút'
$f56after = ([regex]::Matches($ch56, '8[–\-]9 giờ|8 đến 9 giờ')).Count
Write-Host ("[Fix 5+6] ch05_ch06 '8-9 giờ': {0} -> {1} remaining" -f $f56before, $f56after)

# Also fix the phrase "hoàn tất 20 000 mẫu trong vòng khoảng 8-9 giờ đồng hồ cho Stage 1" (line 22)
# After above replace it becomes "trong vòng khoảng ~25 phút đồng hồ cho Stage 1" — cleanup
$ch56 = $ch56 -replace 'trong vòng khoảng ~25 phút đồng hồ cho Stage 1', 'trong vòng khoảng ~25 phút cho Stage 1 (3 epoch × 312 steps × 1.6 s/step ≈ 1498 s ≈ 25 phút trên T4)'

# Fix "duy nhất 1 epoch" Stage 1 description (line 120): S1 now = 3 epoch
$ch56 = $ch56 -replace 'sử dụng duy nhất \*\*1 epoch\*\*', 'sử dụng **3 epoch**'
$ch56 = $ch56 -replace 'Với ~20 000 mẫu / 64 = 312 steps/epoch\.', 'Với ~20 000 mẫu / 64 = 312 steps/epoch, tổng cộng 936 steps (3 epoch × 312 steps).'

# Fix 4: S1 YAML `num_train_epochs: 1` (line 186, with comment) -> 3
# S1 YAML block is in "### 5.5.1" section, before "### 5.5.2"
$parts56 = $ch56 -split '(### 5\.5\.2)', 2
$s1yaml = $parts56[0]
$s2yaml = $parts56[1] + $parts56[2]
$f4before = ([regex]::Matches($s1yaml, 'num_train_epochs:\s*1')).Count
$s1yaml = $s1yaml -replace 'num_train_epochs:\s*1(\s*#\s*\*?\*?[^#\n]*)?', 'num_train_epochs: 3$1'
# Update the comment to reflect 3 epoch
$s1yaml = $s1yaml -replace 'num_train_epochs: 3\s*#\s*\*\s*1 epoch \(số liệu báo cáo\)', 'num_train_epochs: 3                   # ★ 3 epoch (312 steps/epoch × 3 = 936 steps)'
$f4after = ([regex]::Matches($s1yaml, 'num_train_epochs:\s*3')).Count
$s2yamlEpoch1 = ([regex]::Matches($s2yaml, 'num_train_epochs:\s*1')).Count  # should remain 1 (S2 correct)
$ch56 = $s1yaml + $s2yaml
Write-Host ("[Fix 4] ch05_ch06 S1 num_train_epochs 1->3: {0} replaced, now {1} epoch=3 in S1; S2 epoch=1 count={2} (must be 1)" -f $f4before, $f4after, $s2yamlEpoch1)

# --- ch07_ch08_conclusion.md (no fixes) ---
$ch78 = Get-Content "$drafts\ch07_ch08_conclusion.md" -Raw -Encoding UTF8

# Concat all with horizontal rules
$separator = "`n---`n`n"
$body = $ch12 + $separator + $ch34 + $separator + $ch56 + $separator + $ch78
Add-Content -Path $output -Value $body -Encoding UTF8
Write-Host ("[2/4] Body appended. File now: {0} bytes" -f (Get-Item $output).Length)

# ============================================================
# BƯỚC 3: APPEND BIBLIOGRAPHY
# ============================================================
$bib = @'

---

## Tài liệu tham khảo

[1] Smith, R. (2007). "An Overview of the Tesseract OCR Engine." Proceedings ICDAR.

[2] Shi, B., Bai, X., Yao, C. (2017). "An End-to-End Trainable Neural Network for Image-based Sequence Recognition and Its Application to Scene Text Recognition." IEEE PAMI.

[3] OpenAI (2023). "GPT-4V(ision) System Card."

[4] Google DeepMind (2024). "Gemini: A Family of Highly Capable Multimodal Models." Technical Report.

[5] Bai, J. et al. (2023). "Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond." arXiv:2308.12966.

[6] Hu, E. et al. (2022). "LoRA: Low-Rank Adaptation of Large Language Models." ICLR 2022.

[7] OmniDocBench V1.5 Leaderboard. OpenDataLab. https://opendatalab.com

[8] Kalajdzievski, A. (2023). "A Rank Stabilization Scaling Factor for Fine-Tuning with LORA." ICLR 2024.
'@
Add-Content -Path $output -Value $bib -Encoding UTF8
Write-Host ("[3/4] Bibliography appended. File now: {0} bytes" -f (Get-Item $output).Length)

# ============================================================
# BƯỚC 4: VERIFY FILE SIZE + STATS
# ============================================================
$file = Get-Item $output
$content = Get-Content $output -Raw -Encoding UTF8
$charCount = $content.Length
$wordCount = ($content -split '\s+').Count
$lineCount = ($content -split '\n').Count
$pagesEst = [math]::Round($charCount / 2500, 1)

Write-Host ""
Write-Host "========== FINAL VERIFICATION =========="
Write-Host ("File: {0}" -f $output)
Write-Host ("File size: {0} bytes ({1:N1} KB)" -f $file.Length, ($file.Length/1KB))
Write-Host ("Char count: {0:N0}" -f $charCount)
Write-Host ("Word count: {0:N0}" -f $wordCount)
Write-Host ("Line count: {0:N0}" -f $lineCount)
Write-Host ("Pages estimate (chars/2500): {0}" -f $pagesEst)
Write-Host ""

# Sanity checks
Write-Host "========== SANITY CHECKS =========="
$checks = @(
    @{Name="S1 CER 2.01%"; Pattern="2\.01"},
    @{Name="S1 DA 89.4%"; Pattern="89\.4"},
    @{Name="S2 CER 0.42%"; Pattern="0\.42"},
    @{Name="S2 DA 97.6%"; Pattern="97\.6"},
    @{Name="12 font"; Pattern="12 (phông|font|biến thể)"},
    @{Name="88 ENGLISH words"; Pattern="88 (từ )?tiếng Anh"},
    @{Name="15 feeds"; Pattern="15 (RSS )?(feeds|nguồn)"},
    @{Name="10 VNExpress"; Pattern="10 (chuyên mục|nguồn) VNExpress|10 ... VNExpress|VNExpress.*10"},
    @{Name="~1.1B params"; Pattern="1\.1 (tỉ|tỷ|B )|1\.1B"},
    @{Name="OmniDocBench 94.62"; Pattern="94\.62"},
    @{Name="num_train_epochs: 3 (S1)"; Pattern="num_train_epochs: 3"},
    @{Name="num_train_epochs: 1 (S2)"; Pattern="num_train_epochs: 1"},
    @{Name="LoRA formula"; Pattern="W_0 \+ B A"},
    @{Name="rsLoRA formula"; Pattern="sqrt"},
    @{Name="CER formula"; Pattern="edit"},
    @{Name="Mermaid arch"; Pattern="flowchart LR"},
    @{Name="Mermaid pipeline"; Pattern="flowchart TB"},
    @{Name="Mermaid bar chart"; Pattern="xychart-beta"},
    @{Name="Bibliography section"; Pattern="## Tài liệu tham khảo"},
    @{Name="NO 'trong văn liệu'"; Pattern="trong văn liệu"}
)
foreach ($c in $checks) {
    $m = ([regex]::Matches($content, $c.Pattern)).Count
    $status = if ($c.Name -like "NO*") { if ($m -eq 0) { "PASS" } else { "FAIL ($m found)" } } else { if ($m -ge 1) { "PASS ($m)" } else { "FAIL" } }
    Write-Host ("  {0,-30} {1}" -f $c.Name, $status)
}
Write-Host "========================================"
