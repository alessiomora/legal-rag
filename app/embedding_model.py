from app.config import get_settings


def resolve_embedding_device() -> str:
    settings = get_settings()
    requested_device = settings.embedding_device.lower()
    if requested_device != "auto":
        return requested_device

    try:
        import torch
    except ModuleNotFoundError:
        return "cpu"

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_embedding_model():
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    device = resolve_embedding_device()
    print(f"Loading embedding model {settings.embedding_model} on device: {device}")
    return SentenceTransformer(settings.embedding_model, device=device)
