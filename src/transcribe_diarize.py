import os

from faster import (
    get_output_paths,
    transcribe_and_diarize,
    write_json_output,
    write_txt_output,
)


def run_transcribe_diarize(
    *,
    input_file: str,
    output_dir: str,
    transcription_config: dict,
    diarization_config: dict,
    unknown_speaker: str = "unknown",
    max_speaker_gap: float = 0.0,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    result = transcribe_and_diarize(
        input_file=input_file,
        transcription_config=transcription_config,
        diarization_config=diarization_config,
        unknown_speaker=unknown_speaker,
        max_speaker_gap=max_speaker_gap,
    )

    output_paths = get_output_paths(
        input_file=input_file,
        output_dir=output_dir,
    )
    write_txt_output(
        merged_segments=result["merged_segments"],
        output_path=output_paths["txt_path"],
    )
    write_json_output(
        merged_segments=result["merged_segments"],
        output_path=output_paths["json_path"],
    )

    return {
        "output_paths": output_paths,
        "result": result,
    }
