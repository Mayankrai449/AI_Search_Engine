import fitz
import re
import asyncio

async def extract_and_clean_text(pdf_path: str) -> str:
    loop = asyncio.get_event_loop()

    def read_pdf():
        all_text = []
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                all_text.append(text)
        return "\n".join(all_text)

    raw_text = await loop.run_in_executor(None, read_pdf)

    cleaned_text = re.sub(r'\{[^{}]*\}|\<[^\<>]*\>', ' ', raw_text)
    cleaned_text = re.sub(r'```[\s\S]*?```', ' ', cleaned_text)
    cleaned_text = re.sub(r'`[^`]*`', ' ', cleaned_text)
    cleaned_text = re.sub(r'\b\d+\.\d+\.\d+[\w.-]*\b', ' ', cleaned_text)
    cleaned_text = re.sub(r'(\.?/)?[\w/-]+/[\w/-]+(\.[\w]+)?', ' ', cleaned_text)
    cleaned_text = re.sub(r'[^\w\s.,!?]', ' ', cleaned_text)
    cleaned_text = re.sub(r'[.,!?]{2,}', ' ', cleaned_text)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
    cleaned_text = re.sub(r'(\n\s*)+\n', '\n\n', cleaned_text)
    
    cleaned_text = cleaned_text.strip()

    return cleaned_text

def split_text_into_chunks(text: str, max_words: int = 400, overlap_words: int = 100) -> list[str]:
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = []
    current_word_count = 0

    for paragraph in paragraphs:
        words = paragraph.strip().split()
        if not words:
            continue

        if current_word_count + len(words) <= max_words:
            current_chunk.extend(words)
            current_word_count += len(words)
        else:
            if current_chunk:
                chunks.append(' '.join(current_chunk))

            if overlap_words > 0:
                overlap = current_chunk[-overlap_words:] if len(current_chunk) >= overlap_words else current_chunk
                current_chunk = list(overlap)
                current_word_count = len(current_chunk)
            else:
                current_chunk = []
                current_word_count = 0

            current_chunk.extend(words)
            current_word_count += len(words)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks