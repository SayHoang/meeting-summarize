import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from backend.meeting_pipeline import storage
from utils import load_prompt


def _load_default_prompt() -> str:
    return load_prompt("prompts/summary_prompt.txt")


def main() -> None:
    st.set_page_config(page_title="Meeting Settings", layout="wide")
    st.title("Settings")

    default_prompt = _load_default_prompt()
    saved_prompt = storage.get_prompt_override_text() or default_prompt

    prompt_text = st.text_area(
        "Summary prompt",
        value=saved_prompt,
        height=220,
    )

    if st.button("Save Prompt", type="primary"):
        storage.save_prompt_override_text(prompt_text)
        st.success("Prompt saved.")


if __name__ == "__main__":
    main()
