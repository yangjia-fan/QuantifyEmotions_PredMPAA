import os
import json
from collections import Counter
from os.path import join
from tqdm import tqdm

# Define input directory
DIR_IN = join("scripts", "Prediction_Usage")

def load_json(file_path):
    """Load a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def count_mpaa_keys(folder_path):
    """Count occurrences of `mpaa` key values in JSON files."""
    mpaa_counter = Counter()

    # Iterate over all files in the directory
    for file_name in tqdm(os.listdir(folder_path), desc="Processing files"):
        if file_name.endswith(".json"):
            file_path = join(folder_path, file_name)

            # Load the JSON file
            try:
                data = load_json(file_path)
                # Get the `mpaa` value and update the counter
                mpaa_value = data.get("mpaa", "Unknown")
                mpaa_counter[mpaa_value] += 1
            except Exception as e:
                print(f"Error processing file {file_name}: {e}")
    
    return mpaa_counter

if __name__ == "__main__":
    # Count MPAA types
    mpaa_counts = count_mpaa_keys(DIR_IN)

    # Print results
    print("MPAA Key Counts:")
    for mpaa_type, count in mpaa_counts.items():
        print(f"{mpaa_type}: {count}")
