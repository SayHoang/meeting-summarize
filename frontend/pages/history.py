import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api import storage

_TEXT_ENCODING = "utf-8"


def main() -> None:
    st.set_page_config(page_title="Meeting History", layout="wide")
    st.title("Meeting History")

    jobs = storage.list_jobs()
    if not jobs:
        st.info("No jobs found yet.")
        return

    for job in jobs:
        with st.expander(f"{job.job_id} • {job.status}", expanded=False):
            st.write(job.model_dump())

            if job.transcript_path and Path(job.transcript_path).exists():
                transcript_text = Path(job.transcript_path).read_text(encoding=_TEXT_ENCODING)
                st.download_button(
                    "Download Transcript",
                    data=transcript_text,
                    file_name=Path(job.transcript_path).name,
                    key=f"transcript_{job.job_id}",
                )

            if job.summary_path and Path(job.summary_path).exists():
                summary_text = Path(job.summary_path).read_text(encoding=_TEXT_ENCODING)
                st.download_button(
                    "Download Summary",
                    data=summary_text,
                    file_name=Path(job.summary_path).name,
                    key=f"summary_{job.job_id}",
                )


if __name__ == "__main__":
    main()
