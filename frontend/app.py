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

from backend.api import paths, storage, summarize_service, task_service, transcribe_service
from backend.api.types import CreateTaskWebhookParams, SummarizeParams, TranscribeParams
from faster import SUPPORTED_FORMATS
from utils import get_config


def _init_state() -> None:
    st.session_state.setdefault("app_mode", "Transcribe")
    st.session_state.setdefault("switch_to_summarize", False)
    st.session_state.setdefault("summarize_ui_variant", "full")
    st.session_state.setdefault("job_id", None)
    st.session_state.setdefault("transcript_text", "")
    st.session_state.setdefault("summary_text", "")
    st.session_state.setdefault("summary_edit", "")
    st.session_state.setdefault("summary_1_text", "")
    st.session_state.setdefault("summary_2_text", "")
    st.session_state.setdefault("summary_1_model", "")
    st.session_state.setdefault("summary_2_model", "")
    st.session_state.setdefault("judge_result", None)
    st.session_state.setdefault("judge_report_markdown", "")
    st.session_state.setdefault("judge_report_path", "")
    st.session_state.setdefault("chosen_summary_text", "")
    st.session_state.setdefault("chosen_summary_path", "")
    st.session_state.setdefault("transcript_path", "")
    st.session_state.setdefault("summary_path", "")
    st.session_state.setdefault("is_transcribing", False)
    st.session_state.setdefault("is_summarizing", False)
    st.session_state.setdefault("summarize_source", "")
    st.session_state.setdefault("trigger_summarize_now", False)
    st.session_state.setdefault("manual_transcript_input", "")


def _reset_outputs() -> None:
    st.session_state["transcript_text"] = ""
    st.session_state["summary_text"] = ""
    st.session_state["summary_edit"] = ""
    st.session_state["summary_1_text"] = ""
    st.session_state["summary_2_text"] = ""
    st.session_state["summary_1_model"] = ""
    st.session_state["summary_2_model"] = ""
    st.session_state["judge_result"] = None
    st.session_state["judge_report_markdown"] = ""
    st.session_state["judge_report_path"] = ""
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
        if result.judge_result:
            judge_result = result.judge_result.model_dump()
            st.session_state["judge_result"] = judge_result
            st.session_state["judge_report_markdown"] = (
                judge_result.get("report_markdown") or ""
            )
            st.session_state["judge_report_path"] = judge_result.get("report_path") or ""
        else:
            st.session_state["judge_result"] = None
            st.session_state["judge_report_markdown"] = ""
            st.session_state["judge_report_path"] = ""
    finally:
        status_box.empty()


def _summarize_from_input(
    manual_transcript_text: str | None,
    transcript_file: bytes | None,
    transcript_filename: str | None,
) -> None:
    if st.session_state.get("is_summarizing"):
        return

    st.session_state["is_summarizing"] = True
    st.session_state["summary_text"] = ""
    st.session_state["summary_edit"] = ""
    st.session_state["summary_path"] = ""
    st.session_state["chosen_summary_text"] = ""
    st.session_state["chosen_summary_path"] = ""

    try:
        decoded_transcript = ""
        if transcript_file:
            decoded_transcript = transcript_file.decode("utf-8", errors="replace").strip()

        if decoded_transcript:
            st.session_state["summarize_source"] = "manual_file"
            _summarize_manual_input(decoded_transcript, transcript_filename or "transcript.txt")
            return

        manual_text = (manual_transcript_text or "").strip()
        if manual_text:
            st.session_state["summarize_source"] = "manual_text"
            _summarize_manual_input(manual_text, transcript_filename or "transcript.txt")
            return

        st.session_state["summarize_source"] = "transcribe_current"
        _summarize_existing_job()
    finally:
        st.session_state["is_summarizing"] = False


def _summarize_manual_input(transcript_text: str, transcript_filename: str) -> None:
    if not transcript_text.strip():
        st.warning("Please provide a transcript to summarize.")
        return

    job_meta = storage.create_job({"original_filename": transcript_filename})
    st.session_state["job_id"] = job_meta.job_id
    transcript_path = storage.save_transcript_text(
        {"job_id": job_meta.job_id, "transcript_text": transcript_text}
    )
    st.session_state["transcript_text"] = transcript_text
    st.session_state["transcript_path"] = str(transcript_path)
    _dual_summarize_flow(job_meta.job_id, str(transcript_path))


def _summarize_existing_job() -> None:
    job_id = st.session_state.get("job_id")
    transcript_path = st.session_state.get("transcript_path")
    if not job_id or not transcript_path:
        st.warning("No transcribe job found. Please transcribe or provide manual transcript.")
        return

    _dual_summarize_flow(job_id, transcript_path)


def _create_task_flow() -> None:
    summary_text = (st.session_state.get("summary_edit") or "").strip()
    if not summary_text:
        st.warning("Summary is empty. Please edit or generate summary before creating task.")
        return

    result = task_service.send_create_task_webhook(
        CreateTaskWebhookParams(
            summary_text=summary_text,
            job_id=st.session_state.get("job_id"),
        )
    )

    if result.ok:
        st.success(f"Create Task webhook sent successfully (HTTP {result.status_code}).")
    else:
        st.error(f"Create Task failed (HTTP {result.status_code}): {result.message}")

    if result.raw_response is not None:
        st.write("Webhook response:")
        st.write(result.raw_response)


def main() -> None:
    st.set_page_config(page_title="Meeting Transcribe", layout="wide")
    _init_state()

    st.title("Meeting Transcribe & Summarize")
    st.caption("Upload audio, transcribe with progress, then summarize and export.")

    if st.session_state.get("switch_to_summarize"):
        st.session_state["app_mode"] = "Summarize"
        st.session_state["switch_to_summarize"] = False

    mode_options = ["Transcribe", "Summarize"]
    current_mode = st.session_state.get("app_mode", "Transcribe")
    if current_mode not in mode_options:
        current_mode = "Transcribe"

    mode = st.radio(
        "Mode",
        mode_options,
        horizontal=True,
        index=mode_options.index(current_mode),
    )
    if mode != current_mode and mode == "Summarize":
        # User switched via radio, so show full summarize inputs.
        st.session_state["summarize_ui_variant"] = "full"
    st.session_state["app_mode"] = mode

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

            col_export, col_summarize = st.columns(2)
            with col_export:
                st.download_button(
                    "Export Transcribe",
                    data=st.session_state["transcript_text"],
                    file_name=Path(st.session_state["transcript_path"]).name,
                )
            with col_summarize:
                if st.button("Summarize", key="quick_summarize_button", type="primary"):
                    st.session_state["switch_to_summarize"] = True
                    st.session_state["summarize_ui_variant"] = "minimal"
                    st.session_state["summarize_source"] = "transcribe_current"
                    st.session_state["trigger_summarize_now"] = True
                    st.session_state["manual_transcript_input"] = ""
                    st.rerun()

    if mode == "Summarize":
        st.subheader("Summarize a transcript")

        has_transcribe_job = bool(
            st.session_state.get("job_id")
            and st.session_state.get("transcript_path")
            and st.session_state.get("transcript_text")
        )
        if has_transcribe_job:
            st.caption("Detected transcript from current transcribe job (read-only).")
            st.text_area(
                "Transcript from transcribe job",
                value=st.session_state.get("transcript_text") or "",
                height=160,
                disabled=True,
            )
        else:
            st.caption("No transcribe job detected. Provide transcript manually.")

        is_minimal_summarize_ui = bool(
            has_transcribe_job
            and st.session_state.get("summarize_ui_variant") == "minimal"
            and st.session_state.get("summarize_source") == "transcribe_current"
        )

        transcript_upload = None
        manual_transcript_text = ""
        if not is_minimal_summarize_ui:
            transcript_upload = st.file_uploader(
                "Upload transcript (.txt)", type=["txt"], accept_multiple_files=False
            )
            manual_transcript_text = st.text_area(
                "Paste transcript text (optional for manual mode)",
                key="manual_transcript_input",
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
                manual_transcript_text.strip() or None,
                transcript_file_bytes,
                transcript_filename,
            )

        if st.session_state.get("trigger_summarize_now"):
            st.session_state["trigger_summarize_now"] = False
            st.session_state["summarize_source"] = "transcribe_current"
            _summarize_existing_job()

        if (
            st.session_state.get("summary_1_text")
            and st.session_state.get("summary_2_text")
            and not st.session_state.get("summary_text")
        ):
            st.subheader("Compare summaries")
            judge_result = st.session_state.get("judge_result") or {}
            if judge_result:
                judge_error = judge_result.get("error_message")
                recommended_summary = judge_result.get("recommended_summary")
                if judge_error:
                    st.warning(f"Judge unavailable: {judge_error}")
                elif recommended_summary in {1, 2}:
                    st.success(f"Judge recommends: Summary {recommended_summary}")
                else:
                    st.info("Judge result: no strong winner (tie).")

                criteria = judge_result.get("criteria") or []
                if criteria:
                    st.markdown("**Judge criteria scores**")
                    for criterion in criteria:
                        criterion_line = (
                            f"- {criterion.get('display_name', criterion.get('name', 'criterion'))}: "
                            f"S1={criterion.get('summary_1_score', '-')}, "
                            f"S2={criterion.get('summary_2_score', '-')}, "
                            f"direction={criterion.get('direction', 'higher_is_better')}"
                        )
                        reason = str(criterion.get("reason") or "").strip()
                        if reason:
                            criterion_line += f", note={reason}"
                        st.markdown(criterion_line)

                total_score_1 = judge_result.get("total_score_1")
                total_score_2 = judge_result.get("total_score_2")
                if total_score_1 is not None and total_score_2 is not None:
                    st.markdown(
                        f"**Judge total** ({judge_result.get('scoring_mode', 'simple_average')}): "
                        f"Summary 1 = `{float(total_score_1):.2f}`, "
                        f"Summary 2 = `{float(total_score_2):.2f}`"
                    )

                if any(
                    criterion.get("direction") == "lower_is_better"
                    for criterion in criteria
                    if isinstance(criterion, dict)
                ):
                    st.caption(
                        "Criteria with lower_is_better are direction-normalized internally for total scoring."
                    )

                report_markdown = st.session_state.get("judge_report_markdown") or ""
                if report_markdown:
                    with st.expander("Judge full report", expanded=False):
                        st.markdown(report_markdown)

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
        if st.button("Create Task", key="create_task_button", type="primary"):
            _create_task_flow()


if __name__ == "__main__":
    main()
