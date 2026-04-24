import os
import re

import pdfplumber
from docx import Document


def clean_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\xa0", " ", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def extract_text(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")

    extension = os.path.splitext(file_path)[-1].lower()
    text = ""

    try:
        if extension == ".txt":
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()

        elif extension == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages])

        elif extension == ".docx":
            document = Document(file_path)
            text = "\n".join([p.text for p in document.paragraphs])

        else:
            raise ValueError(f"Unsupported file type: {extension}")

        return clean_text(text)

    except Exception as e:
        raise ValueError(f"Failed to parse {file_path}: {e}") from e
