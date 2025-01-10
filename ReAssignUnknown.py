import json
import os
from tqdm import tqdm
from os.path import join
from fuzzywuzzy import fuzz, process

# Define input and output directories
# DIR_IN = join("scripts", "Bucketed_EfficiencyModel_Correction")
# DIR_OUT = join("scripts", "Bucketed_Corrected_200")
DIR_IN = join("scripts", "Bucketed_EfficiencyModel_Correction_Batch3")
DIR_OUT = join("scripts", "Bucketed_EfficiencyModel_Correction_Batch3_Final")

# Define buckets and mapping
BUCKETS = [
    "Profanity",
    "Sexual Content",
    "Violence",
    "Drug/Alcohol",
    "General"
]

bucket_mapping = {
    "Profanity (Language)": "Profanity",
    "Sexual Content (Nudity/Sensuality)": "Sexual Content",
    "Violence (Brutal Scenes)": "Violence",
    "Drug/Alcohol Use": "Drug/Alcohol",
    "General": "General"
}

def load_json(file_path):
    """Load a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data, file_path):
    """Save a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def get_closest_bucket(category, bucket_mapping, threshold=50):
    """Find the closest matching bucket name based on similarity."""
    closest_match, similarity = process.extractOne(category, bucket_mapping.keys(), scorer=fuzz.ratio)
    # print(f"Matching '{category}' -> '{closest_match}' (Similarity: {similarity})")  # Debugging
    if similarity >= threshold:
        return bucket_mapping[closest_match]  # Return the simplified label
    return None  # Return None if no match is found

def reprocess_unknown_bucket(data):
    """
    Process the 'Unknown' bucket and reassign sentences to appropriate buckets.
    """
    for section in ["dialogue", "narration"]:
        if "Unknown" not in data[section]:
            continue

        # Extract and delete the Unknown bucket
        unknown_entries = data[section].pop("Unknown", [])

        print(f"Processing {len(unknown_entries)} entries in the 'Unknown' bucket of {section}.")

        for entry in unknown_entries:
            sentence = entry["sentence"]
            original_category = entry["category"]

            # Match to the closest bucket
            corrected_bucket = get_closest_bucket(original_category, bucket_mapping)

            if corrected_bucket:
                # Assign to the corrected bucket
                data[section].setdefault(corrected_bucket, []).append(sentence)
            else:
                # Recreate the 'Unknown' bucket if not already present
                data[section].setdefault("Unknown", []).append(entry)

    return data

if __name__ == "__main__":
    os.makedirs(DIR_OUT, exist_ok=True)

    # Iterate over all files in the input directory
    for file_name in tqdm(os.listdir(DIR_IN), desc="Processing files"):
        if file_name.endswith(".json"):
            input_file = join(DIR_IN, file_name)
            output_file = join(DIR_OUT, file_name.replace("_Corrected_Corrected.json", "_Corrected.json"))

            # Load the JSON data
            data = load_json(input_file)

            # Process the 'Unknown' bucket
            corrected_data = reprocess_unknown_bucket(data)

            # Save the corrected JSON data
            save_json(corrected_data, output_file)
            print(f"Saved corrected file to: {output_file}")
