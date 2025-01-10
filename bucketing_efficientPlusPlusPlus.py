from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from tqdm import tqdm
from os.path import join
from openai import OpenAI
import time

# Initialize OpenAI client
DIR_IN = join("scripts", "APIready_SmallSample")
DIR_OUT = join("scripts", "Bucketed_SmallSample")

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
            print(f"Error encountered: {e}. Retrying ({retry_count}/{max_retries})...")
            time.sleep(2 ** retry_count)  # Exponential backoff

    # Fallback if all retries fail
    print(f"Failed to classify batch after {max_retries} retries. Assigning 'Unknown' to all sentences.")
    return [(sentence, "Unknown") for sentence in sentence_batch]

# def classify_sentence_batch(sentence_batch):
#     """
#     Classify a batch of sentences in one API call.
#     """
#     categories = "\n".join([f"{key}: {value}" for key, value in BUCKETS.items()])
#     sentences_text = "\n".join([f"Line {i+1}: {sentence}" for i, sentence in enumerate(sentence_batch)])
    
#     messages = [
#         {
#             "role": "system",
#             "content": "You are a helpful assistant that classifies movie script lines into predefined categories.",
#         },
#         {
#             "role": "user",
#             "content": f"""
#             Classify each of the following lines into one of the predefined categories:
#             {categories}.
            
#             Lines:
#             {sentences_text}
            
#             Provide your answer in the following format, one line per result:
#             Line <line_number>: <exact_category_name>
#             """,
#         },
#     ]

#     batch_results = []
#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=messages,
#             max_tokens=150 * len(sentence_batch),  # Allow enough tokens for the response
#             temperature=0,
#         )
        
#         response_lines = response.choices[0].message.content.strip().split("\n")
#         for response_line in response_lines:
#             if response_line.startswith("Line"):
#                 line_number, category = response_line.split(":", 1)
#                 line_index = int(line_number.split()[1]) - 1
#                 batch_results.append((sentence_batch[line_index], category.strip()))
#     except Exception as e:
#         print(f"Error: {e}")
#         for sentence in sentence_batch:
#             batch_results.append((sentence, "Unknown"))  # Fallback for the entire batch in case of failure

#     return batch_results


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


def classify_by_sections(json_data):
    """
    Classify dialogue and narration sections using parallel processing.
    """
    mpaa_rating = json_data.get("MPAA", "Unknown")
    results = {
        "mpaa": mpaa_rating,
        "dialogue": {label: [] for label in BUCKETS.keys()},
        "narration": {label: [] for label in BUCKETS.keys()},
    }

    # Process dialogue
    dialogue_sentences = [d["text"] for d in json_data.get("dialogue", [])]
    dialogue_results = classify_sentences_parallel(dialogue_sentences)

    for sentence, category in dialogue_results:
        if category in results["dialogue"]:
            results["dialogue"][category].append(sentence)
        else:
            results["dialogue"].setdefault("Unknown", []).append({"sentence": sentence, "category": category})

    # Process narration
    narration_sentences = [n["text"] for n in json_data.get("narration", [])]
    narration_results = classify_sentences_parallel(narration_sentences)

    for sentence, category in narration_results:
        if category in results["narration"]:
            results["narration"][category].append(sentence)
        else:
            results["narration"].setdefault("Unknown", []).append({"sentence": sentence, "category": category})

    return results


if __name__ == "__main__":
    os.makedirs(DIR_OUT, exist_ok=True)

    # Iterate over all files in the input directory
    for file_name in tqdm(os.listdir(DIR_IN), desc="Processing files"):
        if file_name.endswith("_APIready.json"):
            input_file = os.path.join(DIR_IN, file_name)

            # Load the input JSON file
            data = load_json(input_file)

            # Classify the data by sections (dialogue and narration)
            classified_results = classify_by_sections(data)

            # Save the classified results to the output directory
            output_file = os.path.join(DIR_OUT, file_name.replace("_APIready.json", "_Bucketed.json"))
            with open(output_file, 'w') as file:
                json.dump(classified_results, file, indent=4)
