from sentence_transformers import SentenceTransformer
import asyncio
import torch

model = None

async def load_model():
    global model
    if model is None:
        try:
            device = 'cuda'
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer('all-mpnet-base-v2', device=device)
            )
            if device == 'cuda':
                torch.backends.cudnn.enabled = True
                torch.backends.cudnn.benchmark = True
                torch.cuda.empty_cache()
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    return model
