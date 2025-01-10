import os
import re
import json
from tqdm import tqdm
import pandas as pd
from os.path import join

# Input and output directories
DIR_IN = join("scripts", "Prediction_Usage")
DIR_OUT = join("scripts", "FrequencyTable", "output_simp_500.csv")  # Specify full path to CSV file

# MPAA count dictionary for debugging
mpaa_count = {
    "G": 0,
    "PG": 0,
    "PG-13": 0,
    "R": 0,
    "NC-17": 0,
    "NR": 0,
    "Unknown": 0  # For missing or invalid MPAA ratings
}

# Function to calculate relative frequencies
def calculate_relative_frequencies(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        movie_name = re.sub(r"(_Corrected\.json|_Bucketed\.json)$", "", os.path.basename(file_path))
        mpaa = data.get("mpaa", "Unknown")  # Default to "Unknown" if MPAA is missing
        
        # Increment MPAA count for debugging
        if mpaa in mpaa_count:
            mpaa_count[mpaa] += 1
        else:
            mpaa_count["Unknown"] += 1

        dialogue = data.get("dialogue", {})
        narration = data.get("narration", {})
        
        dialogue_total = sum(len(sentences) for sentences in dialogue.values())
        narration_total = sum(len(sentences) for sentences in narration.values())
        total_sentences = dialogue_total + narration_total
        
        # Calculate overall bucket frequencies
        overall_freq = {}
        all_buckets = set(dialogue.keys()).union(narration.keys())
        for bucket in all_buckets:
            bucket_total = len(dialogue.get(bucket, [])) + len(narration.get(bucket, []))
            overall_freq[f"overall_{bucket}"] = bucket_total / total_sentences if total_sentences > 0 else 0
        
        # Classification for MPAA ratings
        if mpaa in ["G", "PG", "PG-13"]:
            mpaa_category = "Family-Friendly"
        elif mpaa in ["R", "NC-17", "NR"]:
            mpaa_category = "Adult"
        else:
            mpaa_category = "Unknown"
        
        result = {
            "movie_name": movie_name,
            "mpaa": mpaa,
            "mpaa_category": mpaa_category,
        }
        result.update(overall_freq)
        
        return result
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error processing file {file_path}: {e}")
        return None

# Process all files in the input directory
all_results = []
skipped_files = []
total_files = 0

for file_name in tqdm(os.listdir(DIR_IN), desc="Processing files"):
    if file_name.endswith(".json"):
        file_path = join(DIR_IN, file_name)
        result = calculate_relative_frequencies(file_path)
        if result:
            all_results.append(result)
        else:
            skipped_files.append(file_name)
        total_files += 1
    else:
        print(f"Skipping non-JSON file: {file_name}")
        skipped_files.append(file_name)

# Save results to a CSV
os.makedirs(os.path.dirname(DIR_OUT), exist_ok=True)
df = pd.DataFrame(all_results)
df.to_csv(DIR_OUT, index=False)

# Print MPAA counts summary
print("\nMPAA Rating Counts (Debugging):")
for rating, count in mpaa_count.items():
    print(f"{rating}: {count}")

# Print summary of skipped files
print(f"\nTotal files processed: {total_files}")
print(f"Skipped files: {len(skipped_files)}")

if skipped_files:
    print("\nSkipped Files:")
    for skipped_file in skipped_files:
        print(f" - {skipped_file}")

print(f"\nOutput saved to {DIR_OUT}")
