import sys
import shutil
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = PROJECT_ROOT / "backend" / "core"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from backend.api import paths, storage, summarize_service, transcribe_service
from backend.api.types import SummarizeParams, TranscribeParams
from faster import SUPPORTED_FORMATS
from utils import get_config


def _init_state() -> None:
    st.session_state.setdefault("job_id", None)
    st.session_state.setdefault("transcript_text", "")
    st.session_state.setdefault("summary_text", "")
    st.session_state.setdefault("summary_edit", "")
    st.session_state.setdefault("summary_1_text", "")
    st.session_state.setdefault("summary_2_text", "")
    st.session_state.setdefault("summary_1_model", "")
    st.session_state.setdefault("summary_2_model", "")
    st.session_state.setdefault("chosen_summary_text", "")
    st.session_state.setdefault("chosen_summary_path", "")
    st.session_state.setdefault("transcript_path", "")
    st.session_state.setdefault("summary_path", "")
    st.session_state.setdefault("is_transcribing", False)
    st.session_state.setdefault("is_summarizing", False)


def _reset_outputs() -> None:
    st.session_state["transcript_text"] = ""
    st.session_state["summary_text"] = ""
    st.session_state["summary_edit"] = ""
    st.session_state["summary_1_text"] = ""
    st.session_state["summary_2_text"] = ""
    st.session_state["summary_1_model"] = ""
    st.session_state["summary_2_model"] = ""
    st.session_state["chosen_summary_text"] = ""
    st.session_state["chosen_summary_path"] = ""
    st.session_state["transcript_path"] = ""
    st.session_state["summary_path"] = ""


def _get_live_transcribe_max_lines() -> int:
    max_lines = get_config("live_transcribe_max_lines")
    if isinstance(max_lines, int) and max_lines > 0:
        return max_lines
    return 10


def _delete_job_dir(job_id: str | None) -> None:
    if not job_id:
        return
    job_dir = paths.get_job_dir(job_id)
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)


def _transcribe_flow(audio_bytes: bytes, original_filename: str) -> None:
    if st.session_state.get("is_transcribing"):
        _delete_job_dir(st.session_state.get("job_id"))
        _reset_outputs()

    st.session_state["is_transcribing"] = True
    job_meta = storage.create_job({"original_filename": original_filename})
    st.session_state["job_id"] = job_meta.job_id
    _reset_outputs()

    storage.save_audio_bytes(
        {
            "job_id": job_meta.job_id,
            "original_filename": original_filename,
            "audio_bytes": audio_bytes,
        }
    )

    job_dir = paths.get_job_dir(job_meta.job_id)
    output_path = job_dir / "transcript.txt"

    segments_box = st.empty()
    status_box = st.empty()
    status_box.info("Transcribing, please wait...")
    segment_lines: list[str] = []
    has_first_segment = False
    max_lines = _get_live_transcribe_max_lines()
    box_height = max_lines * 20

    def _on_segment(event: dict) -> None:
        nonlocal has_first_segment
        segment_line = event.get("segment_line")
        if segment_line:
            if not has_first_segment:
                status_box.empty()
                has_first_segment = True
            segment_lines.append(segment_line)
            visible_lines = segment_lines[-max_lines:]
            segments_box.code(
                "\n".join(visible_lines),
                height=box_height,
            )

    try:
        transcribe_service.run_transcribe(
            TranscribeParams(
                job_id=job_meta.job_id,
                input_path=str(
                    job_dir / f"input{Path(original_filename).suffix.lower()}"
                ),
                output_path=str(output_path),
            ),
            on_segment=_on_segment,
        )

        transcript_text = output_path.read_text()
        st.session_state["transcript_text"] = transcript_text
        st.session_state["transcript_path"] = str(output_path)
    finally:
        status_box.empty()
        st.session_state["is_transcribing"] = False


def _summarize_flow(job_id: str, transcript_path: str) -> None:
    job_dir = paths.get_job_dir(job_id)
    output_path = job_dir / "summary.txt"

    status_box = st.empty()
    status_box.info("Summarizing, please wait...")
    preview = st.empty()
    summary_text = ""
    has_first_chunk = False

    def _on_chunk(chunk: str) -> None:
        nonlocal summary_text, has_first_chunk
        if not has_first_chunk:
            status_box.empty()
            has_first_chunk = True
        summary_text += chunk
        preview.markdown(summary_text)

    try:
        summarize_service.run_summary(
            SummarizeParams(
                job_id=job_id,
                transcript_path=transcript_path,
                output_path=str(output_path),
            ),
            on_chunk=_on_chunk,
        )

        st.session_state["summary_text"] = output_path.read_text()
        st.session_state["summary_edit"] = st.session_state["summary_text"]
        st.session_state["summary_path"] = str(output_path)
    finally:
        status_box.empty()


def _choose_summary(which: int) -> None:
    job_id = st.session_state.get("job_id")
    if not job_id:
        st.error("No active job found. Please summarize again.")
        return

    if which == 1:
        chosen_text = st.session_state.get("summary_1_text", "")
    else:
        chosen_text = st.session_state.get("summary_2_text", "")

    if not chosen_text:
        st.warning("Chosen summary is empty.")
        return

    summary_path = storage.save_summary_text(
        {"job_id": job_id, "summary_text": chosen_text}
    )

    st.session_state["summary_text"] = chosen_text
    st.session_state["summary_edit"] = chosen_text
    st.session_state["summary_path"] = str(summary_path)
    st.session_state["chosen_summary_text"] = chosen_text
    st.session_state["chosen_summary_path"] = str(summary_path)

    st.session_state["summary_1_text"] = ""
    st.session_state["summary_2_text"] = ""


def _dual_summarize_flow(job_id: str, transcript_path: str) -> None:
    status_box = st.empty()
    status_box.info("Generating summaries, please wait...")

    try:
        result = summarize_service.run_dual_summary(
            SummarizeParams(
                job_id=job_id,
                transcript_path=transcript_path,
                output_path="",
            )
        )

        st.session_state["summary_1_text"] = result.summary_1
        st.session_state["summary_2_text"] = result.summary_2
        st.session_state["summary_1_model"] = result.model_1 or ""
        st.session_state["summary_2_model"] = result.model_2 or ""
    finally:
        status_box.empty()


def _summarize_from_input(
    transcript_text: str | None,
    transcript_file: bytes | None,
    transcript_filename: str | None,
) -> None:
    if st.session_state.get("is_summarizing"):
        _reset_outputs()

    st.session_state["is_summarizing"] = True

    st.session_state["summary_text"] = ""
    st.session_state["summary_edit"] = ""
    st.session_state["summary_path"] = ""
    st.session_state["chosen_summary_text"] = ""
    st.session_state["chosen_summary_path"] = ""
    
    try:
        if transcript_file:
            transcript_text = transcript_file.decode("utf-8", errors="replace")

        if transcript_text:
            job_meta = storage.create_job(
                {"original_filename": transcript_filename or "transcript.txt"}
            )
            st.session_state["job_id"] = job_meta.job_id
            transcript_path = storage.save_transcript_text(
                {"job_id": job_meta.job_id, "transcript_text": transcript_text}
            )
            st.session_state["transcript_text"] = transcript_text
            st.session_state["transcript_path"] = str(transcript_path)
            _dual_summarize_flow(job_meta.job_id, str(transcript_path))
            return

        job_id = st.session_state.get("job_id")
        transcript_path = st.session_state.get("transcript_path")
        if not job_id or not transcript_path:
            st.warning("Please provide a transcript to summarize.")
            return

        _dual_summarize_flow(job_id, transcript_path)
    finally:
        st.session_state["is_summarizing"] = False


def main() -> None:
    st.set_page_config(page_title="Meeting Transcribe", layout="wide")
    _init_state()

    st.title("Meeting Transcribe & Summarize")
    st.caption("Upload audio, transcribe with progress, then summarize and export.")

    mode = st.radio("Mode", ["Transcribe", "Summarize"], horizontal=True)

    if mode == "Transcribe":
        allowed_types = [ext.lstrip(".") for ext in SUPPORTED_FORMATS]
        uploaded_file = st.file_uploader(
            "Upload a meeting audio file",
            type=allowed_types,
            accept_multiple_files=False,
        )

        if uploaded_file:
            st.audio(uploaded_file)
            st.write(
                {
                    "filename": uploaded_file.name,
                    "size_mb": round(len(uploaded_file.getvalue()) / (1024 * 1024), 2),
                }
            )

            if st.button("Transcribe", type="primary"):
                _transcribe_flow(uploaded_file.getvalue(), uploaded_file.name)

        if st.session_state["transcript_text"]:
            with st.expander("Transcript", expanded=True):
                st.text_area(
                    "Transcript text",
                    value=st.session_state["transcript_text"],
                    height=220,
                )

            st.download_button(
                "Export Transcribe",
                data=st.session_state["transcript_text"],
                file_name=Path(st.session_state["transcript_path"]).name,
            )

    if mode == "Summarize":
        st.subheader("Summarize a transcript")
        transcript_upload = st.file_uploader(
            "Upload transcript (.txt)", type=["txt"], accept_multiple_files=False
        )
        default_transcript = st.session_state.get("transcript_text") or ""
        transcript_text = st.text_area(
            "Paste transcript text",
            value=default_transcript,
            height=200,
        )

        if st.button("Summarize", type="primary"):
            transcript_file_bytes = (
                transcript_upload.getvalue() if transcript_upload else None
            )
            transcript_filename = (
                transcript_upload.name if transcript_upload else None
            )
            _summarize_from_input(
                transcript_text.strip() or None,
                transcript_file_bytes,
                transcript_filename,
            )

        if (
            st.session_state.get("summary_1_text")
            and st.session_state.get("summary_2_text")
            and not st.session_state.get("summary_text")
        ):
            st.subheader("Compare summaries")
            col1, col2 = st.columns(2)

            with col1:
                model_1 = st.session_state.get("summary_1_model") or "Model 1"
                st.markdown(f"**Summary 1 ({model_1})**")
                st.text_area(
                    "Summary 1",
                    value=st.session_state.get("summary_1_text", ""),
                    height=250,
                    key="summary_1_view",
                )
                if st.button("Choose this summary", key="choose_summary_1"):
                    _choose_summary(1)

            with col2:
                model_2 = st.session_state.get("summary_2_model") or "Model 2"
                st.markdown(f"**Summary 2 ({model_2})**")
                st.text_area(
                    "Summary 2",
                    value=st.session_state.get("summary_2_text", ""),
                    height=250,
                    key="summary_2_view",
                )
                if st.button("Choose this summary", key="choose_summary_2"):
                    _choose_summary(2)

    if st.session_state["summary_text"]:
        st.subheader("Summary")
        st.session_state["summary_edit"] = st.text_area(
            "Edit summary before export (Please wait 15s after editing)",
            value=st.session_state["summary_edit"],
            height=200,
        )
        st.download_button(
            "Export Summarize",
            data=st.session_state["summary_edit"],
            file_name=Path(st.session_state["summary_path"]).name,
        )


if __name__ == "__main__":
    main()
