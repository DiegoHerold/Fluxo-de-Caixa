import re
import unicodedata


def repair_mojibake(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    if any(marker in text for marker in ("Ã", "Â", "â€", "â€¢")):
        for encoding in ("cp1252", "latin1"):
            try:
                fixed = text.encode(encoding).decode("utf-8")
                if fixed.count("�") <= text.count("�"):
                    return fixed
            except UnicodeError:
                continue
    return text


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = repair_mojibake(value)
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^\w\s@./:-]", "", normalized)
    return normalized.strip()
