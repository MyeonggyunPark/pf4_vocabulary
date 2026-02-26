import os
import time
import json
import shutil
from pathlib import Path
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Literal
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("에러: .env 파일에 GOOGLE_API_KEY가 없습니다!")
    exit()

client = genai.Client(api_key=GOOGLE_API_KEY)

# ==========================================
# 설정 상수
# ==========================================
MASTER_FILE = Path("greenbook_data/greenbook_full_refined_final.json")
CHECKPOINT_FILE = Path("greenbook_data/word_cefr_map.json")
SPRACHNIVEAUS_DIR = Path("greenbook_data/Sprachniveaus")
WORTARTEN_DIR = Path("greenbook_data/Wortarten")
GREENBOOK_DATA_DIR = Path("greenbook_data")

BATCH_SIZE = 50
RETRY_WAIT = 10
POST_BATCH_WAIT = 3
MAX_RETRIES = 3

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# 기존 품사 파일 목록
WORTARTEN_FILES = [
    "Nomen.json",
    "Verb.json",
    "Verb+Präposition.json",
    "Adjektiv.json",
    "Adverb.json",
    "Präposition.json",
    "Sonstiges.json",
]

# ==========================================
# Pydantic 스키마
# ==========================================
class CefrWordEntry(BaseModel):
    word: str = Field(description="입력과 동일한 독일어 단어")
    cefr: Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class CefrBatch(BaseModel):
    classifications: list[CefrWordEntry]


# ==========================================
# 파이프라인 함수
# ==========================================
def load_master_data(path: Path) -> list[dict]:
    """마스터 JSON에서 모든 항목 로드."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[로드] '{path}'에서 {len(data)}개 항목 로드 완료.")
    return data


def build_unique_word_list(entries: list[dict]) -> list[str]:
    """중복 제거된 고유 단어 리스트 반환."""
    seen = set()
    unique = []
    for entry in entries:
        w = entry["word"]
        if w not in seen:
            seen.add(w)
            unique.append(w)
    print(f"[중복 제거] {len(entries)}개 항목 → {len(unique)}개 고유 단어")
    return unique


def load_checkpoint(path: Path) -> dict[str, str]:
    """기존 체크포인트 파일 로드 (없으면 빈 dict 반환)."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[체크포인트] '{path}'에서 {len(data)}개 기존 분류 로드.")
        return data
    print("[체크포인트] 없음. 새로 시작합니다.")
    return {}


def save_checkpoint(mapping: dict[str, str], path: Path):
    """체크포인트 파일 저장."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def format_batch_word_list(batch: list[str]) -> str:
    """프롬프트용 단어 목록 포매팅."""
    return "\n".join(f"- {w}" for w in batch)


def classify_batch(batch: list[str]) -> dict[str, str]:
    """GenAI 호출로 배치 단어들의 CEFR 레벨 분류. {word: cefr} 반환."""
    word_list_text = format_batch_word_list(batch)

    prompt = f"""
You are an expert German language educator specializing in CEFR level classification.
Classify each German word into its appropriate CEFR proficiency level (A1, A2, B1, B2, C1, C2).

CEFR Level Guidelines:
- A1: Basic everyday words — sein/haben, numbers, family, basic nouns (Haus, Kind), greetings
- A2: Common everyday situations — shopping, basic travel, common adjectives (groß, alt), basic verbs
- B1: Familiar topics — workplace, travel experiences, intermediate abstract nouns, B1 exam vocabulary
- B2: Complex communication — abstract topics, nuanced verbs, professional contexts, complex structures
- C1: Advanced register-specific vocabulary, low-frequency words, literary terms
- C2: Specialist, academic, or rare vocabulary

Classify each word based on when a learner would typically first encounter it in standard German curricula.

Words to classify:
{word_list_text}

Return all {len(batch)} words with their CEFR levels.
"""

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=CefrBatch,
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

            batch_result = CefrBatch.model_validate_json(response.text)
            return {entry.word: entry.cefr for entry in batch_result.classifications}

        except Exception as e:
            print(f"   에러 발생: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                print("   최대 재시도 횟수 초과. 해당 배치를 건너뜁니다.")
                return {}
            else:
                print(f"   {RETRY_WAIT}초 대기 후 재시도합니다... (시도 {attempt + 2}/{MAX_RETRIES})")
                time.sleep(RETRY_WAIT)

    return {}


def run_classification_phase(unique_words: list[str], checkpoint: dict[str, str]) -> dict[str, str]:
    """전체 배치 분류 실행. 체크포인트에 있는 단어는 스킵."""
    # 아직 분류 안 된 단어만 추출
    remaining = [w for w in unique_words if w not in checkpoint]
    total_remaining = len(remaining)

    if total_remaining == 0:
        print("[분류] 모든 단어가 이미 분류되어 있습니다.")
        return checkpoint

    total_batches = (total_remaining + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"[분류] {total_remaining}개 단어를 {total_batches}개 배치로 분류합니다.")

    for i in range(0, total_remaining, BATCH_SIZE):
        batch = remaining[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1

        print(f"\n[배치 {batch_num}/{total_batches}] {len(batch)}개 단어 분류 중...")

        results = classify_batch(batch)

        if results:
            checkpoint.update(results)
            save_checkpoint(checkpoint, CHECKPOINT_FILE)
            classified_count = sum(1 for w in batch if w in results)
            print(f"   -> {classified_count}/{len(batch)}개 분류 완료. (누적: {len(checkpoint)}개)")
        else:
            print(f"   -> 배치 {batch_num} 실패. 건너뜁니다.")

        if i + BATCH_SIZE < total_remaining:
            time.sleep(POST_BATCH_WAIT)

    return checkpoint


def enrich_and_group_entries(
    entries: list[dict], word_cefr_map: dict[str, str]
) -> dict[str, list[dict]]:
    """각 항목에 cefr 필드 추가 후 레벨별 그룹화."""
    grouped: dict[str, list[dict]] = {level: [] for level in CEFR_LEVELS}
    unclassified = []

    for entry in entries:
        word = entry["word"]
        cefr = word_cefr_map.get(word)

        if cefr and cefr in CEFR_LEVELS:
            enriched = {**entry, "cefr": cefr}
            grouped[cefr].append(enriched)
        else:
            unclassified.append(word)

    if unclassified:
        print(f"\n[경고] {len(unclassified)}개 항목이 분류되지 않았습니다:")
        for w in unclassified[:20]:
            print(f"   - {w}")
        if len(unclassified) > 20:
            print(f"   ... 외 {len(unclassified) - 20}개")

    return grouped


def write_cefr_files(grouped: dict[str, list[dict]], output_dir: Path):
    """A1.json~C2.json 및 _summary.json 저장."""
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {"total": sum(len(v) for v in grouped.values())}

    for level in CEFR_LEVELS:
        entries = grouped[level]
        out_path = output_dir / f"{level}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=4)
        summary[level] = len(entries)
        print(f"   {level}.json: {len(entries)}개 항목")

    summary_path = output_dir / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)
    print(f"   _summary.json 저장 완료.")


def reorganize_wortarten(source_dir: Path, wortarten_dir: Path, entries: list[dict]):
    """Wortarten/ 생성 후 품사 파일 복사 및 _summary.json 생성."""
    wortarten_dir.mkdir(parents=True, exist_ok=True)

    # 기존 품사 파일 복사
    for filename in WORTARTEN_FILES:
        src = source_dir / filename
        dst = wortarten_dir / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"   복사: {filename}")
        else:
            print(f"   [경고] '{src}' 파일이 없습니다.")

    # _summary.json 생성
    # 기존 greenbook_data/_summary.json 내용을 기반으로
    src_summary = source_dir / "_summary.json"
    if src_summary.exists():
        with open(src_summary, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
        dst_summary = wortarten_dir / "_summary.json"
        with open(dst_summary, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=4)
        print(f"   _summary.json 복사 완료.")
    else:
        # 직접 생성
        type_map = {
            "명사": "Nomen",
            "동사": "Verb",
            "동사+전치사": "Verb+Präposition",
            "형용사": "Adjektiv",
            "부사": "Adverb",
            "전치사": "Präposition",
            "기타": "Sonstiges",
        }
        counts: dict[str, int] = {}
        for entry in entries:
            t = type_map.get(entry.get("type", ""), entry.get("type", "기타"))
            counts[t] = counts.get(t, 0) + 1

        summary = {"total": len(entries), **counts}
        dst_summary = wortarten_dir / "_summary.json"
        with open(dst_summary, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)
        print(f"   _summary.json 생성 완료.")


def verify_output(entries: list[dict], grouped: dict[str, list[dict]]):
    """분류 결과 통계 리포트 출력."""
    total_classified = sum(len(v) for v in grouped.values())
    total_entries = len(entries)

    print("\n" + "=" * 50)
    print("검증 리포트")
    print("=" * 50)
    print(f"총 항목 수:       {total_entries}")
    print(f"분류된 항목 수:   {total_classified}")
    print(f"미분류 항목 수:   {total_entries - total_classified}")
    print()
    print("레벨별 분포:")
    for level in CEFR_LEVELS:
        count = len(grouped[level])
        bar = "#" * (count // 20)
        print(f"  {level}: {count:5d}개  {bar}")
    print()

    # 샘플 점검
    sample_words = {
        "Kind": "A1",
        "sein": "A1",
        "gut": "A1 또는 A2",
        "bilden": "B1 또는 B2",
        "Zusammenarbeit": "B1 또는 B2",
    }
    print("샘플 단어 점검:")
    for entry in entries:
        if entry["word"] in sample_words and "cefr" in entry:
            expected = sample_words[entry["word"]]
            print(f"  {entry['word']}: {entry['cefr']} (예상: {expected})")

    print("=" * 50)


def main():
    print("=" * 50)
    print("CEFR 레벨 분류 파이프라인 시작")
    print("=" * 50)

    # 1. 마스터 데이터 로드
    entries = load_master_data(MASTER_FILE)

    # 2. 고유 단어 목록 추출
    unique_words = build_unique_word_list(entries)

    # 3. 체크포인트 로드
    checkpoint = load_checkpoint(CHECKPOINT_FILE)

    # 4. API 분류 실행
    print("\n[단계 1/4] CEFR 분류 중...")
    word_cefr_map = run_classification_phase(unique_words, checkpoint)

    # 5. 항목에 cefr 필드 추가 및 레벨별 그룹화
    print("\n[단계 2/4] 데이터 그룹화 중...")
    grouped = enrich_and_group_entries(entries, word_cefr_map)

    # 6. Sprachniveaus/ 파일 저장
    print(f"\n[단계 3/4] Sprachniveaus/ 파일 저장 중...")
    write_cefr_files(grouped, SPRACHNIVEAUS_DIR)

    # 7. Wortarten/ 구성
    print(f"\n[단계 4/4] Wortarten/ 구성 중...")
    reorganize_wortarten(GREENBOOK_DATA_DIR, WORTARTEN_DIR, entries)

    # 8. 검증 리포트
    # grouped 항목에 cefr 필드가 있으므로 검증용 enriched entries 재구성
    enriched_entries = []
    for level_entries in grouped.values():
        enriched_entries.extend(level_entries)
    verify_output(entries, grouped)

    print("\n완료! 생성된 폴더:")
    print(f"  {SPRACHNIVEAUS_DIR}/")
    print(f"  {WORTARTEN_DIR}/")


if __name__ == "__main__":
    main()
