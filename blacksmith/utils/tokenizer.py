import tiktoken


def get_encodings(model: str, token: str) -> list[int]:
    enc = tiktoken.encoding_for_model(model)
    return enc.encode(token)
