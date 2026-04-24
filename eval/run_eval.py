import asyncio
import json
import sys
import time

from sqlalchemy import select

from app.database import async_session
from app.llm.factory import _make_provider
from app.models.document import Document
from app.pipeline.prompts import build_rag_prompt
from app.pipeline.retriever import search


def read_json():
    with open("eval/questions.json", "r", encoding="utf-8") as file:
        eval_texts = json.load(file)

    return eval_texts


def write_result(
    provider, avg_keyword, avg_chunk_found, avg_latency, avg_negative_passed
):
    with open(f"eval/results_{provider}.md", "w", encoding="utf-8") as file:
        file.write(f"# Результаты: {provider}\n\n")
        file.write("| Метрика | Значение |\n")
        file.write("|---------|----------|\n")
        file.write(f"| Keyword match | {avg_keyword:.1f}% |\n")
        file.write(f"| Precision@5 | {avg_chunk_found:.1f}% |\n")
        file.write(f"| Avg latency | {avg_latency:.2f}s |\n")
        file.write(f"| Negative passed | {avg_negative_passed:.1f}% |\n")


async def run_eval(provider: str):
    eval_texts = read_json()
    results = []
    negative_words = [
        "нет информации",
        "не содержится",
        "не найден",
        "не упоминается",
        "не могу",
        "не знаю",
        "не удалось",
        "отсутствует",
        "нет данных",
        "нет такой",
    ]

    async with async_session() as session:
        result = await session.execute(select(Document.id, Document.original_filename))
        doc_map = {row.id: row.original_filename for row in result.all()}

        for i, eval_text in enumerate(eval_texts, 1):
            print(f"[{i}/{len(eval_texts)}] {eval_text['question'][:50]}...")
            question = eval_text["question"]
            expected_keywords = eval_text["expected_keywords"]
            expected_source = eval_text["expected_source"]
            expected_chunk_index = eval_text["expected_chunk_index"]
            type_text = eval_text["type"]

            start_time = time.time()

            chunks = await search(query=question, session=session, top_k=5)
            prompt = build_rag_prompt(question=question, chunks=chunks)
            answer_llm = await _make_provider(provider).chat(
                messages=prompt, stream=False
            )

            end_time = time.time()
            latency = end_time - start_time

            keyword_match = 0
            for expected_keyword in expected_keywords:
                if expected_keyword.lower() in answer_llm.lower():
                    keyword_match += 1

            keyword_match_percent = None
            if len(expected_keywords) != 0:
                keyword_match_percent = (keyword_match / len(expected_keywords)) * 100

            chunk_found = None
            negative_passed = None
            if type_text == "negative":
                negative_passed = any(
                    negative_word in answer_llm.lower()
                    for negative_word in negative_words
                )

            else:
                chunk_found = any(
                    doc_map[chunk.document_id] == expected_source
                    and chunk.chunk_index == expected_chunk_index
                    for chunk in chunks
                )

            results.append(
                {
                    "question": question,
                    "keyword_match_percent": keyword_match_percent,
                    "chunk_found": chunk_found,
                    "negative_passed": negative_passed,
                    "latency": latency,
                    "type": type_text,
                }
            )

            if type_text == "negative":
                print(f"  [NEGATIVE] Ответ: {answer_llm[:200]}")

    factual_results = [r for r in results if r["type"] == "factual"]
    negative_results = [r for r in results if r["type"] == "negative"]

    avg_keyword = sum(r["keyword_match_percent"] for r in factual_results) / len(
        factual_results
    )
    avg_chunk_found = (
        sum(r["chunk_found"] for r in factual_results) / len(factual_results)
    ) * 100
    avg_latency = sum(r["latency"] for r in results) / len(results)
    avg_negative_passed = (
        sum(r["negative_passed"] for r in negative_results) / len(negative_results)
    ) * 100

    write_result(
        provider, avg_keyword, avg_chunk_found, avg_latency, avg_negative_passed
    )

    print("Сделано")


if __name__ == "__main__":
    provider = sys.argv[1] if len(sys.argv) > 1 else "gigachat"
    asyncio.run(run_eval(provider))
