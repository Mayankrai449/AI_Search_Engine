import fitz
import re
import asyncio

async def extract_and_clean_text(pdf_path: str) -> list[tuple[int, str]]:
    loop = asyncio.get_event_loop()

    def extract_page_texts():
        with fitz.open(pdf_path) as doc:
            return [page.get_text("text") for page in doc]

    page_texts = await loop.run_in_executor(None, extract_page_texts)

    def clean_text(text):
        cleaned = re.sub(r'\{[^{}]*\}|\<[^\<>]*\>', ' ', text)
        cleaned = re.sub(r'```[\s\S]*?```', ' ', cleaned)
        cleaned = re.sub(r'`[^`]*`', ' ', cleaned)
        cleaned = re.sub(r'\b\d+\.\d+\.\d+[\w.-]*\b', ' ', cleaned)
        cleaned = re.sub(r'(\.?/)?[\w/-]+/[\w/-]+(\.[\w]+)?', ' ', cleaned)
        cleaned = re.sub(r'[^\w\s.,!?]', ' ', cleaned)
        cleaned = re.sub(r'[.,!?]{2,}', ' ', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'(\n\s*)+\n', '\n\n', cleaned)
        return cleaned.strip()

    cleaned_page_texts = [(page_num + 1, clean_text(text)) for page_num, text in enumerate(page_texts)]
    return cleaned_page_texts


def split_text_into_chunks(paragraphs_with_pages: list[tuple[int, str]], max_words: int = 400, overlap_words: int = 100) -> list[tuple[str, int]]:
    chunks = []
    current_chunk = []
    current_word_count = 0
    current_page = None

    for page_num, paragraph in paragraphs_with_pages:
        words = paragraph.split()
        if not words:
            continue

        if current_page is None:
            current_page = page_num

        if current_word_count + len(words) <= max_words:
            current_chunk.extend(words)
            current_word_count += len(words)
        else:
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append((chunk_text, current_page))

            if overlap_words > 0:
                overlap = current_chunk[-overlap_words:] if len(current_chunk) >= overlap_words else current_chunk
                current_chunk = list(overlap)
                current_word_count = len(current_chunk)
            else:
                current_chunk = []
                current_word_count = 0

            current_page = page_num
            current_chunk.extend(words)
            current_word_count += len(words)

    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append((chunk_text, current_page))
    

    return chunks