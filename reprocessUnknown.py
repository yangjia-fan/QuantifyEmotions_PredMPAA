import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from os.path import join
from openai import OpenAI
import time

# Initialize OpenAI client
# DIR_IN = join("scripts", "Bucketed_EfficiencyModel_Correction_Batch2_Intermediate")
# DIR_OUT = join("scripts", "Bucketed_EfficiencyModel_Correction_Batch2_Intermediate_Final")
DIR_IN = join("scripts", "Bucketed_EfficiencyModel_Usage")
DIR_OUT = join("scripts", "Bucketed_EfficiencyModel_Correction_Batch3")
# DIR_IN = join("scripts", "Bucketed_Corrected_Final_200")
# DIR_OUT = join("scripts", "Bucketed_Corrected_Final_200_Correction")

client = OpenAI(api_key="")

# Define buckets
BUCKETS = {
    "Profanity": "Language",
    "Sexual Content": "Nudity/Sensuality",
    "Violence": "Brutal Bloody Scenes",
    "Drug/Alcohol": "Drug/Alcohol Use",
    "General": "No apparent features related to other buckets"
}


def load_json(file_path):
    """Load a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def chunk_sentences(sentences, chunk_size=10):
    """Split sentences into batches of specified size."""
    for i in range(0, len(sentences), chunk_size):
        yield sentences[i:i + chunk_size]

def classify_sentence_batch(sentence_batch, max_retries=5):
    """
    Classify a batch of sentences in one API call with retry logic.

    Args:
        sentence_batch (list): List of sentences to classify.
        max_retries (int): Maximum number of retries on failure.

    Returns:
        list: A list of tuples (sentence, category).
    """
    categories = "\n".join([f"{key}: {value}" for key, value in BUCKETS.items()])
    sentences_text = "\n".join([f"Line {i+1}: {sentence}" for i, sentence in enumerate(sentence_batch)])

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that classifies movie script lines into predefined categories.",
        },
        {
            "role": "user",
            "content": f"""
            Classify each of the following lines into one of the predefined categories:
            {categories}.
            
            Lines:
            {sentences_text}
            
            Provide your answer in the following format, one line per result:
            Line <line_number>: <exact_category_name>
            """,
        },
    ]

    retry_count = 0

    while retry_count <= max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150 * len(sentence_batch),  # Allow enough tokens for the response
                temperature=0,
            )

            response_lines = response.choices[0].message.content.strip().split("\n")
            batch_results = []
            for response_line in response_lines:
                if response_line.startswith("Line"):
                    line_number, category = response_line.split(":", 1)
                    line_index = int(line_number.split()[1]) - 1
                    batch_results.append((sentence_batch[line_index], category.strip()))
            return batch_results  # Return results if successful

        except Exception as e:
            retry_count += 1
            # print(f"Error encountered: {e}. Retrying ({retry_count}/{max_retries})...")
            time.sleep(2 ** retry_count)  # Exponential backoff

    # Fallback if all retries fail
    print(f"Failed to classify batch after {max_retries} retries. Assigning 'Unknown' to all sentences.")
    return [(sentence, "Unknown") for sentence in sentence_batch]


def classify_sentences_parallel(sentences):
    """
    Use ThreadPoolExecutor to classify sentences in parallel batches.
    """
    results = []
    sentence_batches = list(chunk_sentences(sentences, chunk_size=10))  # Create chunks of 10 sentences

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(classify_sentence_batch, batch): batch for batch in sentence_batches}
        with tqdm(total=len(sentence_batches), desc="Classifying Sentences") as pbar:
            for future in as_completed(futures):
                try:
                    batch_result = future.result()
                    results.extend(batch_result)  # Append the batch result (sentence, category tuples)
                except Exception as e:
                    tqdm.write(f"Error processing batch: {e}")
                finally:
                    pbar.update(1)
    return results


def reprocess_unknown_parallel(json_data):
    """
    Reprocess sentences in the 'Unknown' category for both dialogue and narration
    using parallel processing and batch queries.
    """
    def extract_sentences(unknown_list):
        """Extract sentences from the Unknown bucket, whether strings or dictionaries."""
        sentences = []
        for entry in unknown_list:
            if isinstance(entry, str):  # Entry is a plain string
                sentences.append(entry)
            elif isinstance(entry, dict):  # Entry is a dictionary with a 'sentence' key
                sentences.append(entry.get("sentence", ""))
        return sentences

    # Extract sentences from dialogue and narration Unknown sections
    dialogue_unknown = json_data["dialogue"].get("Unknown", [])
    narration_unknown = json_data["narration"].get("Unknown", [])

    dialogue_sentences = extract_sentences(dialogue_unknown)
    narration_sentences = extract_sentences(narration_unknown)

    # Process dialogue Unknown sentences in parallel
    dialogue_results = classify_sentences_parallel(dialogue_sentences)

    # Process narration Unknown sentences in parallel
    narration_results = classify_sentences_parallel(narration_sentences)

    # Update the Unknown buckets with the reprocessed results
    json_data["dialogue"]["Unknown"] = [
        {"sentence": sentence, "category": category} for sentence, category in dialogue_results
    ]

    json_data["narration"]["Unknown"] = [
        {"sentence": sentence, "category": category} for sentence, category in narration_results
    ]

    return json_data


if __name__ == "__main__":
    os.makedirs(DIR_OUT, exist_ok=True)

    # Iterate over all files in the input directory
    for file_name in tqdm(os.listdir(DIR_IN), desc="Processing and Reprocessing Files"):
        if file_name.endswith(".json"):
            input_file = os.path.join(DIR_IN, file_name)

            # Load the input JSON file
            data = load_json(input_file)

            mpaa = data.get("mpaa", "NR")
            
            if mpaa in ["G", "PG", "NR"]:

                # Reprocess the Unknown sections using parallel processing
                updated_data = reprocess_unknown_parallel(data)

                # Save the updated JSON file to the output directory
                output_file = os.path.join(DIR_OUT, file_name)
                with open(output_file, 'w') as file:
                    json.dump(updated_data, file, indent=4)
            
            else:
                print(f"voided {mpaa}")

    print("Reprocessing completed for all files.")
