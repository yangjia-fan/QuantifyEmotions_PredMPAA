import json
import os
from tqdm import tqdm
from os.path import join
from openai import OpenAI

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Define input and output directories
DIR_IN = join("scripts", "APIready_SmallSample")
DIR_OUT = join("scripts", "Bucketed")


client = OpenAI(api_key="")

# Define buckets
BUCKETS = [
    "Profanity (Language)",
    "Sexual Content (Nudity/Sensuality)",
    "Violence (Brutal Scenes)",
    "Drug/Alcohol Use",
    "General (No apparent features related to other buckets)"
]

bucket_mapping = {
    "Profanity (Language)": "Profanity",
    "Sexual Content (Nudity/Sensuality)": "Sexual Content",
    "Violence (Brutal Scenes)": "Violence",
    "Drug/Alcohol Use": "Drug/Alcohol",
    "General": "General"
}

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    
def get_closest_bucket(llm_output, bucket_mapping, threshold=70):
    """
    Finds the closest matching bucket name based on similarity.

    Args:
        llm_output (str): The bucket name returned by the LLM.
        bucket_mapping (dict): Mapping of full bucket names to simplified labels.
        threshold (int): Minimum similarity score for a match.

    Returns:
        str: Simplified bucket name if a match is found, otherwise "Unknown".
    """
    closest_match, similarity = process.extractOne(llm_output, bucket_mapping.keys(), scorer=fuzz.ratio)

    if similarity >= threshold:
        return bucket_mapping[closest_match]  # Return the simplified label
    else:
        return "Unknown"
    
def classify_by_sections(json_data, buckets, bucket_mapping, threshold=70):

    """
    Classifies dialogue sentences into subcategories (P, S, V, D, G) using fuzzy matching,
    while also handling narration. Includes reprompting for validation.

    Args:
        json_data (dict): Input JSON data with 'dialogue' and 'narration' sections.
        buckets (list): List of predefined categories for classification.
        bucket_mapping (dict): Mapping from full bucket names to simplified labels.
        threshold (int): Minimum similarity score for fuzzy matching.

    Returns:
        dict: Classified sentences with dialogue organized into subcategories and narration handled separately.
    """
    mpaa_rating = json_data.get("MPAA", "Unknown")

    results = {
        "mpaa": mpaa_rating,
        "dialogue": {label: [] for label in bucket_mapping.values()},  # Initialize subcategories
        "narration": {label: [] for label in bucket_mapping.values()}
    }

    # Classify dialogue
    for sentence_obj in tqdm(json_data.get("dialogue", []), desc="Parsing Dialogue Sentences"):
        sentence = sentence_obj["text"]
        
        # Initial classification
        identified_bucket, reasoning = classify_sentence_with_reasoning(sentence, buckets, "dialogue")

        # Reprompt for validation
        validated_bucket, validated_reasoning = reprompt_llm(sentence, identified_bucket, reasoning, buckets)

        simplified_bucket = get_closest_bucket(validated_bucket, bucket_mapping, threshold)

        # Append the sentence to the correct subcategory
        if simplified_bucket in results["dialogue"]:
            results["dialogue"][simplified_bucket].append({
                "line": sentence,
                "reasoning": reasoning,
                "validated_bucket": validated_bucket,  # Add validated bucket for traceability
                "validated_reasoning": validated_reasoning  # Add validated bucket for traceability
            })
        else:
            # If no valid match is found, assign to an "Unknown" bucket
            results["dialogue"].setdefault("Unknown", []).append({
                "line": sentence,
                "reasoning": reasoning,
                "validated_bucket": validated_bucket,
                "validated_reasoning": validated_reasoning  # Add validated bucket for traceability
            })

    # Classify narration
    for sentence_obj in tqdm(json_data.get("narration", []), desc="Parsing Narration Sentences"):
        sentence = sentence_obj["text"]
        
        # Initial classification
        identified_bucket, reasoning = classify_sentence_with_reasoning(sentence, buckets, "narration")
        
        # Reprompt for validation
        validated_bucket, validated_reasoning = reprompt_llm(sentence, identified_bucket, reasoning, buckets)

        simplified_bucket = get_closest_bucket(validated_bucket, bucket_mapping, threshold)

        # Append the sentence to the correct subcategory
        if simplified_bucket in results["narration"]:
            results["narration"][simplified_bucket].append({
                "line": sentence,
                "reasoning": reasoning,
                "validated_bucket": validated_bucket,
                "validated_reasoning": validated_reasoning  # Add validated bucket for traceability
            })
        else:
            # If no valid match is found, assign to an "Unknown" bucket
            results["narration"].setdefault("Unknown", []).append({
                "line": sentence,
                "reasoning": reasoning,
                "validated_bucket": validated_bucket,
                "validated_reasoning": validated_reasoning
            })

    return results


def classify_sentence_with_reasoning(sentence, buckets, sentence_type):
    """
    Classifies a single sentence into a category and returns reasoning.

    Args:
        sentence (str): The sentence to classify.
        buckets (list): List of predefined categories.
        sentence_type (str): 'dialogue' or 'narration' for prompt customization.

    Returns:
        tuple: (bucket, reasoning) where bucket is the assigned category,
               and reasoning explains the decision.
    """
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that classifies movie script lines into predefined categories.",
        },
        {
            "role": "user",
            "content": f"""
            Classify this {sentence_type} line into one of the following categories: {', '.join(buckets)}.
            Provide the category and explain your reasoning in detail.
            Line: "{sentence}"
            Output your response as:
            Category: <category>
            Reasoning: <reasoning>
            """,
        },
    ]
    try:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0,
    )
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "Unknown", "Error during API call"

    # Parse the response
    lines = response.choices[0].message.content.strip().split("\n")
    category = ""
    reasoning = ""
    for line in lines:
        if line.startswith("Category:"):
            category = line.split(":", 1)[1].strip()
        elif line.startswith("Reasoning:"):
            reasoning = line.split(":", 1)[1].strip()

    return category, reasoning

#agentic workflow
def reprompt_llm(line, current_bucket, reasoning, buckets):
    """
    Revalidates the bucket classification for a single line using the LLM.

    Args:
        line (str): The original line to classify.
        current_bucket (str): The current bucket assigned to the line.
        reasoning (str): The reasoning for the original classification.
        buckets (list): List of predefined categories for validation.

    Returns:
        tuple: (validated_category, validated_reasoning)
            - validated_category: The revalidated bucket classification.
            - validated_reasoning: The reasoning for the revalidated classification.
    """
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that classifies movie script lines into predefined categories.",
        },
        {
            "role": "user",
            "content": f"""
            The following line: "{line}" was classified under the category '{current_bucket}' with the reasoning:
            "{reasoning}".
    
            Does this line most closely relate to '{current_bucket}' compared to these other categories:
            {', '.join(buckets)}? If yes, confirm the category. If not, provide the most appropriate category and explain why.

            Output your response as:
            Validated Category: <validated_category>
            Reasoning: <reasoning>
            """,
        },
    ]
    
    try:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0,
    )
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "Unknown", "Error during API call"

    # Parse the response
    lines = response.choices[0].message.content.strip().split("\n")
    validated_category = ""
    validated_reasoning = ""

    for line in lines:
        if line.startswith("Validated Category:"):
            validated_category = line.split(":", 1)[1].strip()
        elif line.startswith("Reasoning:"):
            validated_reasoning = line.split(":", 1)[1].strip()

    return validated_category, validated_reasoning




# MAIN FUNCTION
if __name__ == "__main__":

    os.makedirs(DIR_OUT, exist_ok=True)

    # Iterate over all files in the input directory
    for file_name in tqdm(os.listdir(DIR_IN), desc="Processing files"):
        if file_name.endswith("_APIready.json"):
            input_file = os.path.join(DIR_IN, file_name)
            
            # Load the input JSON file
            data = load_json(input_file)

            # Classify the data by sections (dialogue and narration)
            classified_results = classify_by_sections(data, BUCKETS, bucket_mapping)

            # Save the classified results to the output directory
            output_file = os.path.join(DIR_OUT, file_name.replace("_APIready.json", "_Bucketed.json"))
            with open(output_file, 'w') as file:
                json.dump(classified_results, file, indent=4)

    
    