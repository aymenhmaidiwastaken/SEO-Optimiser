def make_fix(fix_type: str, description: str, suggested: str, page_url: str | None = None, original: str | None = None) -> dict:
    return {
        "fix_type": fix_type,
        "description": description,
        "suggested": suggested,
        "page_url": page_url,
        "original": original,
    }
