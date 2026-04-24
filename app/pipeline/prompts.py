from app.models.chunk import Chunk


def build_rag_prompt(question: str, chunks: list[Chunk]) -> list[dict]:
    context = (
        "Ты отвечаешь на вопрос пользователя, опираясь ТОЛЬКО на приведённый контекст."
        'Если ответа в контексте нет — честно скажи "Не знаю, в документах нет такой информации".'
        "Не придумывай факты. В конце ответа укажи номера использованных фрагментов в квадратных скобках, например [1][3].\n\n"
    )
    for key, val in enumerate(chunks):
        context += f"[{key + 1}] {val.content}\n"

    return [
        {"role": "system", "content": context},
        {"role": "user", "content": f"Вопрос: {question}"},
    ]
