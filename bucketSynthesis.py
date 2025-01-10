import os
import json
from os.path import join, splitext
from tqdm import tqdm

# Define input and output directories
DIR_IN = join("scripts", "Bucketed_Corrected")
DIR_OUT = join("scripts", "Synthesized_Buckets")

# Define buckets of interest
BUCKETS = [
    "Profanity",
    "Sexual Content",
    "Violence",
    "Drug/Alcohol"
]

# Define MPAA priority (lower is less inappropriate)
MPAA_PRIORITY = {
    "G": 1,
    "PG": 2,
    "PG-13": 3,
    "R": 4,
    "NC-17": 5,
    "NR": 6  # NR is processed last due to its undefined nature
}

def sanitize_bucket_name(bucket_name):
    """Sanitize bucket name to create valid file names."""
    return bucket_name.replace("/", "_")

def get_mpaa_priority(mpaa):
    """Get priority value for an MPAA rating."""
    return MPAA_PRIORITY.get(mpaa, float("inf"))  # Default to high priority for unknown ratings

def process_files(dir_in, dir_out, buckets):
    # Ensure output directory exists
    os.makedirs(dir_out, exist_ok=True)

    # Initialize bucket-specific data
    bucketed_sentences = {bucket: {"bucket": bucket, "dialogue": [], "narration": []} for bucket in buckets}

    # Get the list of files with their MPAA ratings
    files = []
    for filename in os.listdir(dir_in):
        if filename.endswith(".json"):
            input_file = join(dir_in, filename)
            with open(input_file, 'r') as f:
                data = json.load(f)
                mpaa_rating = data.get("mpaa", "NR")  # Default to "NR" if missing
                files.append((filename, mpaa_rating))

    # Sort files by MPAA priority
    files.sort(key=lambda x: get_mpaa_priority(x[1]))

    # Process files bucket by bucket
    for bucket in buckets:
        # Reinitialize indices for each bucket
        global_id_dialogue = 1
        global_id_narration = 1

        # Iterate through files for this bucket
        for filename, mpaa_rating in tqdm(files, desc=f"Processing files for {bucket}"):
            input_file = join(dir_in, filename)
            file_id = splitext(filename)[0]  # Extract file name without extension
            with open(input_file, 'r') as f:
                data = json.load(f)

            # Extract dialogue and narration for the current bucket
            dialogues = data.get("dialogue", {}).get(bucket, [])
            narration = data.get("narration", {}).get(bucket, [])

            # Append dialogue sentences for the current bucket
            for sentence in dialogues:
                bucketed_sentences[bucket]["dialogue"].append({
                    "sentence": sentence,
                    "mpaa": mpaa_rating,
                    "id": global_id_dialogue,
                    "file_id": file_id
                })
                global_id_dialogue += 1  # Increment the global dialogue ID

            # Append narration sentences for the current bucket
            for sentence in narration:
                bucketed_sentences[bucket]["narration"].append({
                    "sentence": sentence,
                    "mpaa": mpaa_rating,
                    "id": global_id_narration,
                    "file_id": file_id
                })
                global_id_narration += 1  # Increment the global narration ID

    # Write bucket-specific files to the output directory
    for bucket, content in bucketed_sentences.items():
        sanitized_bucket_name = sanitize_bucket_name(bucket)
        output_file = join(dir_out, f"{sanitized_bucket_name}_Sentences.json")
        with open(output_file, 'w') as f:
            json.dump(content, f, indent=4)

    print(f"Organized sentences written to: {dir_out}")

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(DIR_OUT, exist_ok=True)

    # Run the processing function
    process_files(DIR_IN, DIR_OUT, BUCKETS)
