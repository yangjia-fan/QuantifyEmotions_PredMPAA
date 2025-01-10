# QuantifyEmotions_PredMPAA
A method to predict MPAA Ratings via Film Script Analysis and sentence clustering w/ LLMs

There are 8 steps to the whole process:

1. Collect scripts from various sources - Scrape websites for scripts in HTML, txt, doc, or pdf format (adopted from Aveek-Saha)
2. Collect metadata - Get metadata about the scripts including the matching MPAA rating from TMDb and IMDb (adapted from Aveek-Saha for the MPAA function)
3. Find duplicates from different sources - Automatically group and remove duplicates from different sources.
4. Parse Scripts - Convert script elements into lines with labels such as Character(C), Dialogue(D), Narration(N), Metadata(M), and MPAA.
5. Break chunked narrations and dialogues into individual sentences with SPACY, maintain coherent labels, and exclude labeled lines besides MPAA, D, and N.
6. Parse into JSON format for API calls.
7. Efficient Processing using batch prompting and threading for API calls to categorize each sentence within each script into buckets - Profanity (Language), Sexual Content (Nudity/Sensuality), Violence, Drug/Alcohol Use, General (No apparent features related to other buckets).
8. Due to efficient processing and API calling limit, defect batches will be returned with the label Unknown. Therefore, processed scripts will need to be reprocessed for the unknown sections. This is to ensure accuracy in the frequency of each bucket relative to the whole script.
9. Reassign the unknown section that was just reprocessed.
10. Generate a CSV table that presents the frequency of each bucket relative to its script volume. 

## Usage (these files must be run in order with considerate directory management)
