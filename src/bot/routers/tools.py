def id_extracter(code: str) -> int:
    if code.startswith("get-memory-"):
        return int(code.split("-")[-1])
    elif code.startswith("delete-memory-"):
        return int(code.split("-")[-1])
    else:
        raise ValueError("Неправильный формат кода")
