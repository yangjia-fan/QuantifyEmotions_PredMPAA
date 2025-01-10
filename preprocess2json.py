import os
import json
from tqdm import tqdm
# Define directories
from os.path import join

DIR_FINAL = join("scripts", "txt_spacy_ND")  # Original folder with .txt files
DIR_OUT = join("scripts", "APIready")  # New output folder for .json files

def preprocess_and_separate(file_path, output_dir):
    results = {
        "MPAA": None,  # Placeholder for MPAA rating
        "dialogue": [],
        "narration": []
    }

    # Read the file to extract MPAA and count lines
    with open(file_path, 'r') as file:
        lines = file.readlines()

        if lines:  # Ensure the file is not empty
            first_line = lines[0].strip()
            if first_line.startswith("MPAA:"):
                # Clean up duplicate "MPAA: " if present
                mpaa_raw = first_line.split(":", 1)[1].strip()  # Extract after the first colon
                if "MPAA:" in mpaa_raw:
                    mpaa_raw = mpaa_raw.replace("MPAA:", "").strip()  # Remove redundant "MPAA:"
                results["MPAA"] = mpaa_raw

    # Process the rest of the file with a progress bar
    with tqdm(total=len(lines), desc=f"Processing {os.path.basename(file_path)}") as pbar:
        for line_number, line in enumerate(lines, start=1):
            line = line.strip()

            # Check if the line starts with "D:" or "N:" and has more than one word
            if line.startswith("D:"):
                text = line[2:].strip()
                if len(text.split()) > 1:  # Exclude lines that are one word long
                    results["dialogue"].append({
                        "id": len(results["dialogue"]) + 1,
                        "line_number": line_number,
                        "text": text
                    })
            elif line.startswith("N:"):
                text = line[2:].strip()
                if len(text.split()) > 1:  # Exclude lines that are one word long
                    results["narration"].append({
                        "id": len(results["narration"]) + 1,
                        "line_number": line_number,
                        "text": text
                    })
            
            pbar.update(1)

    # Save results to a JSON file
    file_name = os.path.basename(file_path).replace('_parsed.txt', '_APIready.json')
    output_file = os.path.join(output_dir, file_name)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)

    return output_file

if __name__ == "__main__":
    # Process all .txt files in DIR_FINAL and save to DIR_OUT
    for file_name in os.listdir(DIR_FINAL):
        if file_name.endswith(".txt"):
            input_file = join(DIR_FINAL, file_name)
            print(f"Processing file: {file_name}")
            output_path = preprocess_and_separate(input_file, DIR_OUT)
            print(f"Preprocessed file saved to: {output_path}")
        
