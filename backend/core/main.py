from faster import transcribe_and_diarize

if __name__ == "__main__":
    input_file = get_config("input_file")
    output_dir = get_config("output_dir")
    output_file = generate_output_filename(input_file, output_dir)
    
    transcribe_and_diarize(input_file, output_file)