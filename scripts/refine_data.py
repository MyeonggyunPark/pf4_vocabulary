import os
import time
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("에러: .env 파일에 GOOGLE_API_KEY가 없습니다!")
    exit()

client = genai.Client(api_key=GOOGLE_API_KEY)


# ==========================================
# 1. Pydantic 스키마 (다형성 및 고유명사 필터링 적용)
# ==========================================
class VerbForms(BaseModel):
    praesens_er: Optional[str] = Field(
        None, description="현재형 3인칭 단수 (예: er isst)"
    )
    praeteritum: Optional[str] = Field(
        None, description="과거형 3인칭 단수 (예: er aß)"
    )
    perfekt: Optional[str] = Field(None, description="현재완료형 (예: er hat gegessen)")
    partizip_2_form: str = Field(description="과거분사 형태 (예: gegessen). 필수값.")

class AdjectivalUsageInfo(BaseModel):
    is_usable: bool = Field(description="형용사로 사용 가능한지 여부 (True/False)")
    form: Optional[str] = Field(None, description="형용사 형태")
    korean: Optional[str] = Field(None, description="형용사로 쓰일 때의 뜻")

class AdjectivalUsage(BaseModel):
    partizip_1: AdjectivalUsageInfo
    partizip_2: AdjectivalUsageInfo

# 명사 전용 스키마
class NounEntry(BaseModel):
    is_valid_word: bool
    is_proper_noun: bool = Field(
        description="사람 이름, 지명, 국가, 브랜드 등 고유명사인지 여부 (True/False)"
    )
    type: Literal["명사"]
    word: str
    korean: str
    gender: Optional[Literal["der", "die", "das", "der/die", "das/die", "der/das"]] = (
        None
    )
    plural: Optional[str] = Field(
        None, description="복수형. 없으면 절대 '-' 쓰지 말고 null로 비워둘 것."
    )

# 일반 동사 전용 스키마
class VerbEntry(BaseModel):
    is_valid_word: bool
    is_proper_noun: bool = Field(
        description="사람 이름, 지명, 국가, 브랜드 등 고유명사인지 여부 (True/False)"
    )
    type: Literal["동사"]
    word: str
    korean: str
    verb_forms: VerbForms
    adjectival_usage: AdjectivalUsage


# 고정 전치사 동사 전용 스키마
class VerbPrepEntry(BaseModel):
    is_valid_word: bool
    is_proper_noun: bool = Field(
        description="사람 이름, 지명, 국가, 브랜드 등 고유명사인지 여부 (True/False)"
    )
    type: Literal["동사+전치사"]
    word: str
    korean: str
    fixed_preposition: str = Field(
        description="반드시 문법적인 고정 전치사만 기입 (예: auf (Akkusativ))"
    )
    verb_forms: VerbForms
    adjectival_usage: AdjectivalUsage


# 형용사/부사 등 기타 품사 전용 스키마
class OtherEntry(BaseModel):
    is_valid_word: bool
    is_proper_noun: bool = Field(
        description="사람 이름, 지명, 국가, 브랜드 등 고유명사인지 여부 (True/False)"
    )
    type: Literal["형용사", "부사", "전치사", "기타"]
    word: str
    korean: str


# Union을 통해 LLM이 품사에 맞는 스키마를 강제로 선택하게 만듦
class VocabularyList(BaseModel):
    entries: list[Union[NounEntry, VerbEntry, VerbPrepEntry, OtherEntry]]


# ==========================================
# 2. 정제 파이프라인 함수
# ==========================================
def batch_refine_vocabulary(csv_filename, chunk_size=50):
    print(f"[{csv_filename}] 파일 읽는 중...")

    with open(csv_filename, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]

    total_lines = len(lines)
    print(
        f"총 {total_lines}줄의 데이터를 찾았습니다. {chunk_size}개씩 AI에게 보냅니다."
    )

    all_refined_data = {}
    output_file = "greenbook_full_refined_final.json"

    for i in range(0, total_lines, chunk_size):
        chunk = lines[i : i + chunk_size]
        chunk_text = "".join(chunk)
        batch_num = (i // chunk_size) + 1
        total_batches = (total_lines // chunk_size) + 1

        prompt = f"""
        You are an expert German linguist and a rigorous editor for a B1-B2 level German grammar textbook.
        너는 독일어 B1~B2 수준의 문법 교재를 집필하는 최고 수준의 원어민 편집자야.

        Analyze the provided CSV data and extract the information.

        [CRITICAL RULES FOR RESCUING WORDS - 절대 지우지 말고 살려낼 것]
        1. PoS Correction (품사 자동 교정): 
            If the CSV provides the WRONG part of speech (e.g., "Sofort" is labeled as '명사', or "teuer" as '명사'), DO NOT delete it! Change its `type` to the correct one (e.g., "부사", "형용사") and keep it.
            (CSV에 품사가 잘못 적혀있다고 쓰레기 취급해서 지우지 마. 네가 올바른 품사로 고쳐서 살려내.)

        2. Lemmatization of Conjugations (변형된 단어 원형 복구):
            If you see a conjugated verb (e.g., "Hast", "Iss", "Sieh") or a declined adjective, DO NOT mark it as invalid. Restore it to its base infinitive ("haben", "essen", "sehen") and keep it.
            (동사나 형용사가 변형되어 들어와도 지우지 말고, 무조건 사전형(기본 원형)으로 고쳐서 살려내.)

        3. Garbage Flagging (진짜 쓰레기만 삭제): 
            ONLY set `is_valid_word` to false if the word is an unrecoverable OCR error or merged gibberish (e.g., "Erenscenecnsnes", "Türundall", "Bkinderleisesem", "Radiound"). Valid German words MUST be set to true.
            (해독 불가능한 완벽한 오타나, 여러 단어가 뭉쳐진 쓰레기 데이터만 false로 처리해. 멀쩡한 독일어는 무조건 true야.)

        [STRICT RULES - MUST FOLLOW]
        4. NO HYPHENS FOR NULLS: If a Noun does not have a plural form, leave `plural` as null. NEVER use "-" or "–".
            (명사의 복수형이 없으면 절대 "-" 기호를 쓰지 말고 null로 비워둬.)

        5. VERB+PREPOSITION HALLUCINATION PREVENTION: 
            ONLY classify as "동사+전치사" if it is a genuine "Verben mit fester Präposition" (e.g., warten auf, sich erinnern an). 
            (진짜 고정 전치사 동사만 "동사+전치사"로 분류해.)

        6. Verb Adjectival Usage Logic:
            Evaluate if a Partizip can logically/grammatically be used as an attributive adjective before a noun. If not, set `is_usable` to false.

        7. PROPER NOUNS FILTERING (고유명사 필터링):
            If a word is a specific proper noun like a person's name (e.g., Eva, Paul), a city/country (e.g., Münster, Panama), or a brand (e.g., Acer), set `is_proper_noun` to true. 
            (사람 이름, 지명, 국가, 브랜드 등만 true로 설정해라.)

        [DATA]
        {chunk_text}
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(
                    f"\n[배치 {batch_num}/{total_batches}] 데이터 추출중... (시도 {attempt+1})"
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=VocabularyList,
                        safety_settings=[
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                        ],
                    ),
                )

                batch_result = VocabularyList.model_validate_json(response.text)

                valid_entries = []
                for entry in batch_result.entries:
                    if not entry.is_valid_word:
                        print(f"   [삭제됨 - 쓰레기 데이터]: {entry.word}")
                    elif entry.is_proper_noun:
                        print(f"   [삭제됨 - 고유명사 필터링]: {entry.word}")
                    else:
                        valid_entries.append(entry)

                for item in valid_entries:
                    item_dict = item.model_dump()

                    item_dict.pop("is_valid_word", None)
                    item_dict.pop("is_proper_noun", None)

                    unique_key = f"{item_dict['word']}_{item_dict['type']}"
                    all_refined_data[unique_key] = item_dict

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        list(all_refined_data.values()), f, ensure_ascii=False, indent=4
                    )

                print(
                    f" -> {len(valid_entries)}개 단어 추출 및 저장 완료! (현재 누적: {len(all_refined_data)}개)"
                )
                time.sleep(3)
                break

            except Exception as e:
                print(f"에러 발생: {str(e)}")
                if attempt == max_retries - 1:
                    print("최대 재시도 횟수 초과. 해당 배치를 건너뜁니다.")
                else:
                    print("10초 대기 후 재시도합니다...")
                    time.sleep(10)

    print(
        f"\n🎉 [최종 성공] 고유명사 필터링 완벽 적용! 총 {len(all_refined_data)}개의 무결점 데이터가 '{output_file}'에 준비되었습니다."
    )


if __name__ == "__main__":
    batch_refine_vocabulary("greenbook_ocr_vocab.csv")
