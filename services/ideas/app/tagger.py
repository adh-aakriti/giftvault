def parse_tags(raw):
    if not raw:
        return []
    seen = []
    for part in raw.split(","):
        name = part.strip().lower()
        if name and name not in seen:
            seen.append(name)
    return seen