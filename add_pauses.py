import re
from typing import List, Tuple

PAUSE_SECONDS_RE = re.compile(r"\[PAUSE:(\d+)s\]", flags=re.IGNORECASE)
PAUSE_TAGS_RE = re.compile(r"\[PAUSE:\d+s\]", flags=re.IGNORECASE)

def parse_script(script: str) -> List[Tuple[str, int]]:
    """
    Returns [(spoken_text, pause_after_seconds), ...]
    where the *final* chunk always has pause 0.
    """
    # Grab all pauses as integers.
    pauses = [int(sec) for sec in PAUSE_SECONDS_RE.findall(script)]
    # Split into chunks & srip whitespace.
    chunks = [c.strip() for c in PAUSE_TAGS_RE.split(script) if c.strip()]

    # We expect exactly one more chunk than pauses. Final chunk has no pause
    if len(chunks) != len(pauses) + 1:
        raise ValueError(
            "The script ends with a [PAUSE] tag or has consecutive pauses."
        )

    result = []
    for i, chunk in enumerate(chunks):
        pause_after = pauses[i] if i < len(pauses) else 0
        result.append((chunk, pause_after))
    return result


# ── Quick sanity checks ────────────────────────────────────────────────────────
if __name__ == "__main__":
    s1 = "Inhala profundo. [PAUSE:4s] Exhala lento… [PAUSE:6s] Buen trabajo."
    print(parse_script(s1))
    # [('Inhala profundo.', 4), ('Exhala lento…', 6), ('Buen trabajo.', 0)]

    s2 = "Relájate. [PAUSE:10s][PAUSE:2s] Suelta."  # consecutive pauses
    try:
        parse_script(s2)
    except ValueError as e:
        print("Caught:", e)

    s3 = "Final tag issue. [PAUSE:3s]"  # trailing pause
    try:
        parse_script(s3)
    except ValueError as e:
        print("Caught:", e)
