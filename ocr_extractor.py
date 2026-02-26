import os
from pdf2image import convert_from_path
import pytesseract
import spacy
import csv
import re
from collections import defaultdict

print("🇩🇪 독일어 NLP 모델(spaCy) 로딩 중...")
nlp = spacy.load("de_core_news_sm")

def extract_text_via_ocr(pdf_path, max_pages=None):
    print(f"\n[{pdf_path}] 파일을 이미지로 변환 중...")
    if max_pages:
        print(f"안전을 위해 처음 {max_pages}페이지까지만 변환합니다.")
        pages = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=max_pages)
    else:
        print("책 전체를 변환합니다. (컴퓨터 사양에 따라 시간이 소요될 수 있습니다!)")
        pages = convert_from_path(pdf_path, dpi=300)

    full_ocr_text = ""
    total_pages = len(pages)

    print("\n본격적인 OCR 글자 인식 시작...")
    for i, page in enumerate(pages):
        print(f"   -> OCR 처리 중: [ {i+1} / {total_pages} ] 페이지")
        text = pytesseract.image_to_string(page, lang="deu")
        full_ocr_text += text + "\n"

    return full_ocr_text


def process_german_text_advanced(text):
    print("\nAI가 문장 구조를 분석하여 모든 품사의 단어를 추출 중입니다...")

    nlp.max_length = len(text) + 100000
    doc = nlp(text)

    extracted_data = {
        "NOUN": defaultdict(int),
        "VERB": defaultdict(int),
        "ADJ": defaultdict(int),
        "ADV": defaultdict(int),
        "ADP": defaultdict(int),
        "VERB_PREP": defaultdict(int),
    }

    for token in doc:
        if not re.match(r"^[a-zA-ZäöüÄÖÜß]+$", token.text):
            continue

        lemma = token.lemma_.lower()
        pos = token.pos_

        if pos == "NOUN":
            if len(lemma) > 2:
                extracted_data["NOUN"][lemma.capitalize()] += 1

        elif pos in ["VERB", "ADJ", "ADV", "ADP"]:
            if len(lemma) > 1:
                extracted_data[pos][lemma] += 1

        if pos == "ADP" and token.head.pos_ == "VERB":
            head_verb = token.head.lemma_.lower()
            preposition = token.lower_
            verb_prep_combo = f"{head_verb} {preposition}"
            extracted_data["VERB_PREP"][verb_prep_combo] += 1

    return extracted_data


pdf_file = "greenbook.pdf"

try:
    if not os.path.exists(pdf_file):
        print(f"에러: '{pdf_file}' 파일이 폴더에 없습니다.")
    else:
        raw_text = extract_text_via_ocr(pdf_file)

        all_data = process_german_text_advanced(raw_text)

        csv_filename = "greenbook_ocr_vocab.csv"
        print(f"\n데이터 추출 완료! [{csv_filename}] 파일로 저장합니다...")

        with open(csv_filename, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Type", "Word", "Frequency"])

            for category, words_dict in all_data.items():
                for word, count in sorted(
                    words_dict.items(), key=lambda x: x[1], reverse=True
                ):

                    cat_name = {
                        "NOUN": "명사",
                        "VERB": "동사",
                        "ADJ": "형용사",
                        "ADV": "부사",
                        "ADP": "전치사",
                        "VERB_PREP": "동사+전치사",
                    }.get(category, category)

                    writer.writerow([cat_name, word, count])

        print(f"\n[성공] 모든 데이터가 완벽하게 '{csv_filename}'에 저장되었습니다!")

except Exception as e:
    print(f"\n실행 중 치명적 에러 발생: {e}")
