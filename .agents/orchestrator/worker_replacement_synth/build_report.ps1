# build_report.ps1 — Synthesize 4 drafts into final Vietnamese report
# Avoids single >100KB write by concatenating drafts with Add-Content

$ErrorActionPreference = 'Stop'

$DraftsDir = 'c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts'
$OutFile   = 'c:\project\uit\nlp\GLM-OCR\docs\bao_cao_do_an_MLLM_OCR_Tieng_Viet.md'

# ── Bước 1: Header (title + TOC + separator) ──
$Header = @'
# Nghiên cứu và Finetune MLLM cho OCR tiếng Việt — Trường hợp GLM-OCR

**Đồ án môn học** | Tác giả: [Họ tên sinh viên] | MSSV: [xxx] | Ngày: 2026

## Mục lục

1. [Tóm tắt](#1-tóm-tắt)
2. [Giới thiệu](#2-giới-thiệu)
3. [Tổng quan nghiên cứu](#3-tổng-quan-nghiên-cứu)
4. [Phương pháp đề xuất](#4-phương-pháp-đề-xuất)
5. [Thực nghiệm](#chương-5-thực-nghiệm)
6. [Kết quả và Đánh giá](#chương-6-kết-quả-và-đánh-giá)
7. [Phân tích hạn chế](#7-phân-tích-hạn-chế)
8. [Demo](#8-demo)
9. [Kết luận và Hướng phát triển](#kết-luận-và-hướng-phát-triển)
10. [Tài liệu tham khảo](#tài-liệu-tham-khảo)

---

'@

# UTF-8 with BOM to ensure proper Vietnamese rendering
$Utf8NoBom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($OutFile, $Header, $Utf8NoBom)
Write-Host "[1/6] Header written"

# ── Bước 2: Append ch01_ch02 (strip lines 1-3 which are title/blank/separator) ──
$ch1 = Get-Content -Path "$DraftsDir\ch01_ch02.md" -Encoding UTF8
# Skip first 3 lines (title, blank, ---), keep from line 4 onwards
$ch1Body = ($ch1 | Select-Object -Skip 3) -join "`r`n"
[System.IO.File]::AppendAllText($OutFile, $ch1Body + "`r`n`r`n---`r`n`r`n", $Utf8NoBom)
Write-Host "[2/6] ch01_ch02 appended"

# ── Bước 3: Append ch03_ch04 ──
$ch2 = Get-Content -Path "$DraftsDir\ch03_ch04.md" -Encoding UTF8 -Raw
[System.IO.File]::AppendAllText($OutFile, $ch2 + "`r`n---`r`n`r`n", $Utf8NoBom)
Write-Host "[3/6] ch03_ch04 appended"

# ── Bước 4: Append ch05_ch06 ──
$ch3 = Get-Content -Path "$DraftsDir\ch05_ch06.md" -Encoding UTF8 -Raw
[System.IO.File]::AppendAllText($OutFile, $ch3 + "`r`n---`r`n`r`n", $Utf8NoBom)
Write-Host "[4/6] ch05_ch06 appended"

# ── Bước 5: Append ch07_ch08_conclusion ──
$ch4 = Get-Content -Path "$DraftsDir\ch07_ch08_conclusion.md" -Encoding UTF8 -Raw
[System.IO.File]::AppendAllText($OutFile, $ch4 + "`r`n---`r`n`r`n", $Utf8NoBom)
Write-Host "[5/6] ch07_ch08_conclusion appended"

# ── Bước 6: Bibliography ──
$Bib = @'

## Tài liệu tham khảo

[1] Smith, R. (2007). "An Overview of the Tesseract OCR Engine." *ICCUV*.
[2] Shi, B., Bai, X., & Yao, C. (2017). "An End-to-End Trainable Neural Network for Image-based Sequence Recognition and Its Application to Scene Text Recognition." *IEEE Transactions on Pattern Analysis and Machine Intelligence (PAMI)*, 39(11).
[3] OpenAI (2023). "GPT-4V(ision) System Card."
[4] Google (2024). "Gemini: A Family of Highly Capable Multimodal Models." *Technical Report*.
[5] Bai, J., Bai, S., et al. (2023). "Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond." *arXiv:2308.12966*.
[6] Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., & Chen, W. (2022). "LoRA: Low-Rank Adaptation of Large Language Models." *ICLR 2022*.
[7] OmniDocBench V1.5 leaderboard. https://opendatalab.com
[8] Kalajdzievski, A. (2023). "A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA." *ICLR 2024*.

*Hết tài liệu tham khảo.*
'@
[System.IO.File]::AppendAllText($OutFile, $Bib, $Utf8NoBom)
Write-Host "[6/6] Bibliography appended"

# ── Char count summary ──
$content = Get-Content -Path $OutFile -Encoding UTF8 -Raw
$charCount = $content.Length
Write-Host ""
Write-Host "Final char count: $charCount"
Write-Host "Final file: $OutFile"
