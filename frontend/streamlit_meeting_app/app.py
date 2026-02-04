import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from backend.meeting_pipeline import paths, storage, summarize_service, transcribe_service
from backend.meeting_pipeline.types import SummarizeParams, TranscribeParams
from faster import SUPPORTED_FORMATS


def _init_state() -> None:
    st.session_state.setdefault("job_id", None)
    st.session_state.setdefault("transcript_text", "")
    st.session_state.setdefault("summary_text", "")
    st.session_state.setdefault("summary_edit", "")
    st.session_state.setdefault("transcript_path", "")
    st.session_state.setdefault("summary_path", "")


def _reset_outputs() -> None:
    st.session_state["transcript_text"] = ""
    st.session_state["summary_text"] = ""
    st.session_state["summary_edit"] = ""
    st.session_state["transcript_path"] = ""
    st.session_state["summary_path"] = ""


def _transcribe_flow(audio_bytes: bytes, original_filename: str) -> None:
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

    progress = st.progress(0)
    status = st.empty()

    def _on_progress(event) -> None:
        progress.progress(int(event.percent))
        status.caption(event.message)

    transcribe_service.run_transcribe(
        TranscribeParams(
            job_id=job_meta.job_id,
            input_path=str(job_dir / f"input{Path(original_filename).suffix.lower()}"),
            output_path=str(output_path),
        ),
        on_progress=_on_progress,
    )

    transcript_text = output_path.read_text()
    st.session_state["transcript_text"] = transcript_text
    st.session_state["transcript_path"] = str(output_path)


def _summarize_flow() -> None:
    job_id = st.session_state.get("job_id")
    transcript_path = st.session_state.get("transcript_path")

    if not job_id or not transcript_path:
        st.warning("Please transcribe first.")
        return

    job_dir = paths.get_job_dir(job_id)
    output_path = job_dir / "summary.txt"

    progress = st.progress(0)
    status = st.empty()
    preview = st.empty()
    summary_text = ""

    def _on_progress(event) -> None:
        progress.progress(int(event.percent))
        status.caption(event.message)

    def _on_chunk(chunk: str) -> None:
        nonlocal summary_text
        summary_text += chunk
        preview.markdown(summary_text)

    summarize_service.run_summary(
        SummarizeParams(
            job_id=job_id,
            transcript_path=transcript_path,
            output_path=str(output_path),
        ),
        on_progress=_on_progress,
        on_chunk=_on_chunk,
    )

    st.session_state["summary_text"] = output_path.read_text()
    st.session_state["summary_edit"] = st.session_state["summary_text"]
    st.session_state["summary_path"] = str(output_path)


def main() -> None:
    st.set_page_config(page_title="Meeting Transcribe", layout="wide")
    _init_state()

    st.title("Meeting Transcribe & Summarize")
    st.caption("Upload audio, transcribe with progress, then summarize and export.")

    allowed_types = [ext.lstrip(".") for ext in SUPPORTED_FORMATS]
    uploaded_file = st.file_uploader(
        "Upload a meeting audio file", type=allowed_types, accept_multiple_files=False
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

        if st.button("Summarize", type="primary"):
            _summarize_flow()

    if st.session_state["summary_text"]:
        st.subheader("Summary")
        st.session_state["summary_edit"] = st.text_area(
            "Edit summary before export",
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
