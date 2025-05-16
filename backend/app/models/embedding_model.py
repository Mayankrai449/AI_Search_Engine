from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, AutoProcessor, AutoModel
import asyncio
import torch
from torch.amp.autocast_mode import autocast

async def load_siglip_model(model_name="google/siglip-so400m-patch14-384"):
    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        dtype = torch.float16 if device.type == 'cuda' else torch.float32
        loop = asyncio.get_event_loop()

        processor = await loop.run_in_executor(
            None,
            lambda: AutoProcessor.from_pretrained(model_name)
        )
        model = await loop.run_in_executor(
            None,
            lambda: AutoModel.from_pretrained(
                model_name,
                torch_dtype=dtype,
                device_map="auto"
            )
        )
        model.to(device)
        return model, processor
    except Exception as e:
        raise RuntimeError(f"Failed to load SigLIP model: {e}")

async def load_llm_model():
    try:
        loop = asyncio.get_event_loop()
        
        llm_tokenizer = await loop.run_in_executor(
            None,
            lambda: AutoTokenizer.from_pretrained('Qwen/Qwen2-1.5B-Instruct')
        )

        if llm_tokenizer.pad_token is None:
            llm_tokenizer.pad_token = "<pad>"
        llm_tokenizer.padding_side = "left"

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        
        llm_model = await loop.run_in_executor(
            None,
            lambda: AutoModelForCausalLM.from_pretrained(
                'Qwen/Qwen2-1.5B-Instruct',
                quantization_config=quantization_config,
                device_map="auto"
            )
        )
        return llm_model, llm_tokenizer
    except Exception as e:
        raise RuntimeError(f"Failed to load LLM model: {e}")

def encode_with_siglip(model, processor, texts=None, images=None, batch_size=64):
    device = next(model.parameters()).device
    with autocast(device_type='cuda' if device.type == 'cuda' else 'cpu'):
        if texts:
            inputs = processor(text=texts, return_tensors="pt", padding=True, truncation=True).to(device)
            with torch.no_grad():
                embeddings = model.get_text_features(**inputs).cpu().numpy()
        elif images:
            inputs = processor(images=images, return_tensors="pt").to(device)
            with torch.no_grad():
                embeddings = model.get_image_features(**inputs).cpu().numpy()
        else:
            raise ValueError("Either texts or images must be provided")
        torch.cuda.empty_cache()
        return embeddings

async def generate_tailored_response(llm_model, llm_tokenizer, query: str, chunks: list[str], max_length: int = 200):
    context = " [SEP] ".join(chunks[:3]) if len(chunks) > 1 else chunks[0] if chunks else ""
    system_message = "Answer briefly according to context."
    user_message = f"Context: {context}\n\nQuestion: {query}"
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    text = llm_tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    device = next(llm_model.parameters()).device
    model_inputs = llm_tokenizer(
        [text],
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=2048,
        return_attention_mask=True
    ).to(device)
    
    loop = asyncio.get_event_loop()
    def run_llm():
        generated_ids = llm_model.generate(
            input_ids=model_inputs.input_ids,
            attention_mask=model_inputs.attention_mask,
            max_new_tokens=128,
            num_beams=1,
            top_p=0.7,
            temperature=0.3,
            use_cache=True,
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = llm_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response
    
    response = await loop.run_in_executor(None, run_llm)

    sentences = [s.strip() for s in response.split('.') if s.strip()]
    if sentences:
        if not response.strip().endswith(('.', '!', '?')):
            sentences = sentences[:-1]
            response = ' '.join(sentences) + '.' if sentences else ''
    
    return response.strip()