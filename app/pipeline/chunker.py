import re


def _merge_pieces(
    pieces: list[str], chunk_size: int, overlap: int, separator: str
) -> list[str]:
    chunks = []
    current_chunk = ""

    for piece in pieces:
        if len(current_chunk) + len(piece) <= chunk_size:
            if current_chunk:
                current_chunk += separator + piece
            else:
                current_chunk = piece

        else:
            chunks.append(current_chunk)
            current_chunk = current_chunk[-overlap:] + separator + piece

    if current_chunk.strip():
        chunks.append(current_chunk)

    return chunks


def split_into_chunks(
    text: str, chunk_size: int = 2000, overlap: int = 200
) -> list[str]:
    paragraphs = text.split("\n\n")
    pieces = []

    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            pieces.append(paragraph)

        else:
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)

            safe_sentences = []
            for sentence in sentences:
                if len(sentence) <= chunk_size:
                    safe_sentences.append(sentence)

                else:
                    for i in range(0, len(sentence), chunk_size):
                        safe_sentences.append(sentence[i : i + chunk_size])

            sub_chunks = _merge_pieces(
                safe_sentences, chunk_size, overlap, separator=" "
            )

            pieces.extend(sub_chunks)

    return _merge_pieces(pieces, chunk_size, overlap, separator="\n\n")
