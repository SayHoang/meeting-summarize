import sys
import json
import os
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = PROJECT_ROOT / "backend" / "core"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from backend.api import storage, paths
from utils import load_prompt, read_config_file, write_config_file


def _load_default_prompt() -> str:
    return load_prompt("prompts/summary_prompt.txt")

def _param_spec_path() -> Path:
    return CORE_DIR / "param.json"

@st.cache_data(show_spinner=False)
def _read_param_spec() -> dict:
    spec_path = _param_spec_path()
    if not spec_path.exists():
        return {}
    try:
        loaded = json.loads(spec_path.read_text())
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}

def _notes_path() -> Path:
    return PROJECT_ROOT / "config_notes.json"

def _read_notes() -> dict:
    notes_path = _notes_path()
    if not notes_path.exists():
        return {}
    try:
        return json.loads(notes_path.read_text())
    except Exception:
        return {}

def _write_notes(notes: dict) -> None:
    _notes_path().write_text(json.dumps(notes, indent=2, ensure_ascii=False) + "\n")

def _ui_options_path() -> Path:
    # Store user-editable UI options outside repo root (meeting_storage/)
    return paths.ensure_storage_root() / "ui_options.json"

def _default_ui_options() -> dict:
    spec = _read_param_spec()
    fw = (spec.get("faster_whisper") or {}) if isinstance(spec, dict) else {}

    def _opt(key: str, fallback: list[str]) -> list[str]:
        item = fw.get(key) or {}
        options = item.get("options") if isinstance(item, dict) else None
        return options if isinstance(options, list) and options else fallback

    return {
        "faster_whisper": {
            "models": _opt(
                "model_whisper",
                ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            ),
            "compute_types": _opt(
                "compute_type",
                ["int8", "int8_float16", "float16", "float32"],
            ),
            "devices": _opt("device", ["cpu", "cuda"]),
        }
    }

def _read_ui_options() -> dict:
    options_path = _ui_options_path()
    if not options_path.exists():
        return _default_ui_options()
    try:
        loaded = json.loads(options_path.read_text())
        if isinstance(loaded, dict):
            return {**_default_ui_options(), **loaded}
    except Exception:
        pass
    return _default_ui_options()

def _write_ui_options(ui_options: dict) -> None:
    _ui_options_path().write_text(
        json.dumps(ui_options, indent=2, ensure_ascii=False) + "\n"
    )

def _csv_to_list(value: str) -> list[str]:
    items = [item.strip() for item in (value or "").split(",")]
    return [item for item in items if item]

def _list_to_csv(items: list[str]) -> str:
    return ", ".join(items or [])

def _env_override_banner(config_key: str) -> None:
    env_key = f"KLTN_{config_key.upper()}"
    env_value = os.getenv(env_key)
    if env_value is not None:
        st.warning(f"`{config_key}` is overridden by env var `{env_key}` = `{env_value}`")

def _section_prompt() -> None:
    st.subheader("Prompt Settings")
    default_prompt = _load_default_prompt()
    saved_prompt = storage.get_prompt_override_text() or default_prompt

    prompt_text = st.text_area(
        "Summary prompt",
        value=saved_prompt,
        height=220,
        label_visibility="collapsed",
        placeholder="Enter your prompt here...",
    )

    if st.button("Save Prompt", type="primary"):
        storage.save_prompt_override_text(prompt_text)
        st.success("Prompt saved.")

def _section_faster_whisper() -> None:
    st.subheader("Transcribe Settings")
    config = read_config_file()
    notes = _read_notes()
    ui_options = _read_ui_options()
    spec = _read_param_spec()

    fw_options = ui_options.get("faster_whisper") or {}
    whisper_models = fw_options.get("models") or []
    compute_types = fw_options.get("compute_types") or []
    devices = fw_options.get("devices") or []

    # Ensure the currently active config values are always selectable
    current_model = config.get("model_whisper")
    if current_model and current_model not in whisper_models:
        whisper_models = [current_model, *whisper_models]
    current_compute_type = config.get("compute_type")
    if current_compute_type and current_compute_type not in compute_types:
        compute_types = [current_compute_type, *compute_types]
    current_device = config.get("device")
    if current_device and current_device not in devices:
        devices = [current_device, *devices]

    fw_spec = spec.get("faster_whisper") if isinstance(spec, dict) else None
    beam_spec = (fw_spec.get("beam_size") if isinstance(fw_spec, dict) else None) or {}
    beam_min = int(beam_spec.get("min") or 1)
    beam_max = int(beam_spec.get("max") or 20)
    beam_step = int(beam_spec.get("step") or 1)

    with st.form("faster_whisper_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            _env_override_banner("model_whisper")
            model_whisper = st.selectbox(
                "Model Name",
                options=whisper_models,
                index=whisper_models.index(config.get("model_whisper"))
                if config.get("model_whisper") in whisper_models
                else 0,
                help=notes.get("model_whisper") or "Model name for faster-whisper.",
            )

        
            _env_override_banner("compute_type")
            compute_type = st.selectbox(
                "Compute Type",
                options=compute_types,
                index=compute_types.index(config.get("compute_type"))
                if config.get("compute_type") in compute_types
                else 0,
                help=notes.get("compute_type") or "Compute type (speed/VRAM trade-off).",
            )

            _env_override_banner("vad_filter")
            vad_filter = st.checkbox(
                "VAD Filter",
                value=bool(config.get("vad_filter")),
                help=notes.get("vad_filter") or "Enable VAD to filter silence.",
            )

        with col_right:
            _env_override_banner("device")
            device = st.radio(
                "Device",
                options=devices,
                index=devices.index(config.get("device"))
                if config.get("device") in devices
                else 0,
                help=notes.get("device") or "cpu or cuda.",
            )

            _env_override_banner("beam_size")
            beam_size = st.slider(
                "Beam Size",
                min_value=beam_min,
                max_value=beam_max,
                value=int(config.get("beam_size") or 5),
                step=beam_step,
                help=notes.get("beam_size") or "Beam size for decoding.",
            )

        is_saved = st.form_submit_button("Save", type="primary")
        if is_saved:
            config["model_whisper"] = model_whisper
            config["device"] = device
            config["compute_type"] = compute_type
            config["beam_size"] = int(beam_size)
            config["vad_filter"] = bool(vad_filter)
            write_config_file(config)
            st.success("Saved to config.json")
            st.rerun()

def _section_summarize() -> None:
    st.subheader("Summarize Settings")
    config = read_config_file()
    notes = _read_notes()
    spec = _read_param_spec()

    summarize_spec = spec.get("summarize") if isinstance(spec, dict) else None
    if not isinstance(summarize_spec, dict):
        summarize_spec = {}

    temp_spec = summarize_spec.get("temperature_summary") or {}
    top_p_spec = summarize_spec.get("top_p_summary") or {}

    temperature_min = float(temp_spec.get("min") or 0.0)
    temperature_max = float(temp_spec.get("max") or 2.0)
    temperature_step = float(temp_spec.get("step") or 0.05)

    top_p_min = float(top_p_spec.get("min") or 0.0)
    top_p_max = float(top_p_spec.get("max") or 1.0)
    top_p_step = float(top_p_spec.get("step") or 0.05)

    with st.form("summarize_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            _env_override_banner("temperature_summary")
            temperature_summary = st.slider(
                "Temperature",
                min_value=temperature_min,
                max_value=temperature_max,
                value=float(config.get("temperature_summary") or temperature_min),
                step=temperature_step,
                help=notes.get("temperature_summary")
                or "Sampling temperature (higher = more random).",
            )

        with col_right:
            _env_override_banner("top_p_summary")
            top_p_summary = st.slider(
                "Top P",
                min_value=top_p_min,
                max_value=top_p_max,
                value=float(config.get("top_p_summary") or top_p_min),
                step=top_p_step,
                help=notes.get("top_p_summary") or "Nucleus sampling top-p.",
            )

        is_saved = st.form_submit_button("Save", type="primary")
        if is_saved:
            config["model_summary"] = model_summary
            config["temperature_summary"] = float(temperature_summary)
            config["top_p_summary"] = float(top_p_summary)
            write_config_file(config)
            st.success("Saved to config.json")
            st.rerun()

def main() -> None:
    st.set_page_config(page_title="Meeting Settings", layout="wide")
    st.title("Settings")

    st.divider()

    # Prompt settings
    _section_prompt()

    # Faster-Whisper settings
    _section_faster_whisper()

    # Summarize settings
    _section_summarize()


if __name__ == "__main__":
    main()
