#!/usr/bin/env python3
"""
Script lọc từ không phải tiếng Việt từ file từ điển tiếng Việt.

Sử dụng 2 tiêu chí:
1. Kiểm tra ký tự: chỉ chấp nhận các ký tự trong bảng chữ cái tiếng Việt
2. Kiểm tra âm tiết: mỗi âm tiết phải tuân theo quy tắc âm vị học tiếng Việt
   (âm đầu + vần = âm chính + phụ âm cuối)

Cách dùng:
    python filter_vietnamese.py
    python filter_vietnamese.py input.txt output.txt removed.txt
"""

import os
import re
import sys
import unicodedata

# ============================================================
# Tập hợp tất cả ký tự tiếng Việt hợp lệ
# ============================================================
VIET_CHARS = set(
    # Chữ cái cơ bản (không dấu thanh)
    "abcdđeêghiklmnoôơpqrstuvxy"
    # Nguyên âm + dấu thanh
    "aáàảãạ"
    "ăắằẳẵặ"
    "âấầẩẫậ"
    "eéèẻẽẹ"
    "êếềểễệ"
    "iíìỉĩị"
    "oóòỏõọ"
    "ôốồổỗộ"
    "ơớờởỡợ"
    "uúùủũụ"
    "ưứừửữự"
    "yýỳỷỹỵ"
    # Dấu cách (cho từ ghép)
    " "
)

# Dấu thanh tiếng Việt (trong dạng NFD)
TONE_MARKS = {
    "\u0301",  # sắc (acute)
    "\u0300",  # huyền (grave)
    "\u0309",  # hỏi (hook above)
    "\u0303",  # ngã (tilde)
    "\u0323",  # nặng (dot below)
}

# ============================================================
# Danh sách các âm tiết ngoại lệ (hợp lệ trong tiếng Việt
# nhưng không khớp regex âm vị chuẩn)
# ============================================================
SPECIAL_SYLLABLES = {
    # Chữ cái đơn dùng làm từ (đặc biệt 'đ')
    "đ",
    # Từ có phụ âm cuối /o/ kép (oo) - kiểu Pháp mượn
    "choong",
    "choòng",
    "goong",
    "goòng",
    "coong",
    "coóng",
    "coong",
    "boong",
    "boóng",
    "boòng",
    "toong",
    "toòng",
    "toóng",
    "soong",
    "soóng",
    "pooc",
    "poóc",
    "mooc",
    "moóc",
    "roong",
    "roóng",
    "hooc",
    "hoóc",
    "cooc",
    "coóc",
    "xoong",
    "xoóng",
    "loong",
    "loóng",
    "boong",
    # Các từ có âm tiết đặc biệt
    "huơ",
    "khuơ",
    "thuở",
    "voọc",
    "voọc",
    "xamôva",
    # Từ mượn đã Việt hóa phổ biến (có dấu tiếng Việt)
    "ôtô",
    "ô tô",
    "ôxy",
    "oxy",
    "ôxít",
    "oxít",
    "ôxy",
    "oxy",
    "patê",
    "batê",
    "patinê",
    "batinê",
    "panô",
    "tarô",
    "nivô",
    "kêpi",
    "maníp",
    "pêđan",
    "pêđê",
    "ôsin",
    "ôboa",
    "pittông",
    "hôligân",
    "găngxtơ",
    "guđron",
    "moayơ",
    "tatăng",
    "tigôn",
    "maníp",
    "crêp",
    "crếp",
    "blốc",
    "blôc",
    "soóc",
    "plây",
}


def remove_tones(text: str) -> str:
    """
    Bỏ dấu thanh tiếng Việt, giữ nguyên chữ cái gốc.
    Ví dụ: 'ắ' → 'ă', 'ệ' → 'ê', 'ớ' → 'ơ'
    """
    result = []
    for char in text:
        nfd = unicodedata.normalize("NFD", char)
        filtered = "".join(c for c in nfd if c not in TONE_MARKS)
        result.append(unicodedata.normalize("NFC", filtered))
    return "".join(result)


def build_syllable_regex() -> re.Pattern:
    """
    Xây dựng regex kiểm tra âm tiết tiếng Việt hợp lệ.

    Âm tiết tiếng Việt = Âm đầu (onset) + Vần (rhyme)
    Vần = Âm chính (nucleus) + Phụ âm cuối (coda) [tuỳ chọn]

    Regex này khớp âm tiết sau khi đã bỏ dấu thanh.
    """
    # ---- Âm đầu (onset) ----
    # Sắp xếp theo độ dài giảm dần để regex ưu tiên khớp cái dài trước
    onset = r"(?:ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|b|c|d|đ|g|h|k|l|m|n|p|r|s|t|v|x)?"

    # ---- Âm chính (nucleus) ----
    # Ba âm (triphthongs) - khớp trước (dài hơn)
    triphthongs = "|".join(
        sorted(
            [
                "iêu",
                "ươu",
                "ương",
                "uyên",
                "uôn",
                "uôi",
                "ươi",
                "oai",
                "oao",
                "oay",
                "uây",
                "uya",
            ],
            key=len,
            reverse=True,
        )
    )

    # Hai âm (diphthongs)
    diphthongs = "|".join(
        sorted(
            [
                "ia",
                "iê",  # i-based
                "ua",
                "uâ",
                "uê",
                "uô",
                "uyê",  # u-based
                "ươ",
                "ưi",
                "ưu",
                "ưa",  # ư-based
                "ai",
                "ao",
                "au",
                "âu",
                "ây",
                "ay",  # a-based
                "eo",
                "êu",  # e-based
                "iu",  # i/u
                "oi",
                "ôi",
                "ơi",  # o-based
                "ui",  # u/i
                "uy",  # u/y
                "ya",
                "yê",
                "ye",
                "yi",  # y-based
                "oa",
                "oă",
                "oe",  # o-based glide
            ],
            key=len,
            reverse=True,
        )
    )

    # Một âm (single vowels)
    single_vowels = "|".join(
        ["a", "ă", "â", "e", "ê", "i", "o", "ô", "ơ", "u", "ư", "y"]
    )

    nucleus = rf"(?:{triphthongs}|{diphthongs}|{single_vowels})"

    # ---- Phụ âm cuối (coda) ----
    coda = r"(?:ng|nh|ch|c|m|n|p|t|u|i|o|y)?"

    # ---- Kết hợp ----
    pattern = "^" + onset + nucleus + coda + "$"
    return re.compile(pattern)


def is_vietnamese_word(word: str, syllable_re: re.Pattern) -> bool:
    """
    Kiểm tra một từ có phải là từ tiếng Việt hợp lệ không.

    Tiêu chí:
    1. Tất cả ký tự phải thuộc bảng chữ cái tiếng Việt
    2. Mỗi âm tiết (phân tách bằng dấu cách) phải tuân theo
       quy tắc âm vị học tiếng Việt
    3. Hoặc thuộc danh sách âm tiết ngoại lệ
    """
    word_lower = word.strip().lower()
    if not word_lower:
        return False

    # 0. Kiểm tra whitelist
    if word_lower in SPECIAL_SYLLABLES:
        return True

    # 1. Kiểm tra ký tự
    for char in word_lower:
        if char not in VIET_CHARS:
            return False

    # 2. Tách âm tiết và kiểm tra từng cái
    syllables = word_lower.split()
    if not syllables:
        return False

    for syl in syllables:
        # Kiểm tra whitelist cho từng âm tiết
        if syl in SPECIAL_SYLLABLES:
            continue

        # Bỏ dấu thanh để kiểm tra cấu trúc âm tiết
        base = remove_tones(syl)

        # Kiểm tra whitelist cho base (không dấu)
        if base in SPECIAL_SYLLABLES:
            continue

        if not syllable_re.match(base):
            return False

    return True


def main():
    # ---- Đường dẫn file ----
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "vietnamese_words.txt")
    output_file = os.path.join(script_dir, "vietnamese_words_clean.txt")
    removed_file = os.path.join(script_dir, "removed_words.txt")

    # Cho phép truyền đường dẫn qua command line
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    if len(sys.argv) >= 4:
        removed_file = sys.argv[3]

    # ---- Xây dựng regex ----
    syllable_re = build_syllable_regex()

    # ---- Đọc và lọc ----
    viet_words = []
    non_viet_words = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if not word:
                continue
            if is_vietnamese_word(word, syllable_re):
                viet_words.append(word)
            else:
                non_viet_words.append(word)

    # ---- Ghi file kết quả ----
    with open(output_file, "w", encoding="utf-8") as f:
        for word in viet_words:
            f.write(word + "\n")

    # ---- Ghi file từ đã xoá (để kiểm tra) ----
    with open(removed_file, "w", encoding="utf-8") as f:
        f.write(f"# Đã xoá {len(non_viet_words)} từ không phải tiếng Việt\n")
        f.write(f"# (Có thể khôi phục nếu cần)\n\n")
        for word in non_viet_words:
            f.write(word + "\n")

    # ---- In thống kê ----
    total = len(viet_words) + len(non_viet_words)
    print(f"╔══════════════════════════════════════════╗")
    print(f"║     KẾT QUẢ LỌC TỪ TIẾNG VIỆT           ║")
    print(f"╠══════════════════════════════════════════╣")
    print(f"║  Tổng số từ:          {total:>8}            ║")
    print(f"║  Từ tiếng Việt:       {len(viet_words):>8}  (giữ lại)  ║")
    print(f"║  Từ không phải VN:    {len(non_viet_words):>8}  (xoá)      ║")
    print(f"╚══════════════════════════════════════════╝")
    print()
    print(f"File kết quả: {output_file}")
    print(f"File đã xoá:  {removed_file}")
    print()

    # Hiển thị một số ví dụ từ bị xoá
    if non_viet_words:
        print("--- Ví dụ từ bị xoá (30 từ đầu tiên) ---")
        for word in non_viet_words[:30]:
            print(f"  {word}")
        if len(non_viet_words) > 30:
            print(f"  ... và {len(non_viet_words) - 30} từ khác")


if __name__ == "__main__":
    main()
