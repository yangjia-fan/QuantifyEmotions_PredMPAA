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

## Usage (these files must be run in order)

First, visit Aveek's Repository to see details of how to scrape PDF scripts from Internet Sources. This step would be running the `get_scripts.py` file (See Aveek's site for more details)
`@misc{Saha_Movie_Script_Database_2021,
    author = {Saha, Aveek},
    month = {7},
    title = {{Movie Script Database}},
    url = {https://github.com/Aveek-Saha/Movie-Script-Database},
    year = {2021}
}`

Since the MPAA metadata function was added, run the `get_metadata.py` from this repository to perform step 2. 

Run `clean_files.py`, `parse_files.py`, `txt_ND.py`, and `preprocess2json.py` to perform steps 3, 4, 5, and 6.

Both the `bucketing.py` and `bucketing_efficientPlusPlusPlus.py` could be used for step 7. Note that `bucketing.py` utilizes an agentic workflow style of prompting. It is not efficient but ensures accuracy. On the other hand, `bucketing_efficientPlusPlusPlus.py` uses batch prompting, which increases the chance of error in API returns, but saves much more time when needing to categorize large amounts of scripts. 

Run `reprocessUnknown.py` to perform step 8, and `ReAssignUnknown.py` to perform step 9.

To obtain a usable frequency table for analytical and prediction purposes, run `frequencyGeneration.py` for step 10. The sample table `output_simp_500.csv` was provided. 

To use the frequency table for analysis and prediction, refer to the markdown files - `Prediction-Analysis_mpaa.ipynb` or `Prediction-Analysis_category.ipynb` which predicts whether the movie is family-friendly or not.

Note.
- Throughout the process, you can always run `sampleCount.py` to check how many scripts of each MPAA rating you have, thus knowing if more scripts need to be obtained for a more balanced dataset.
- Always ensure clear directory management when API calls reach daily limits to start returning defect batches. When this happens, you can temporarily stop processing, and when you want to reinitiate, run `smartRemove.py` on the directory from which you are pulling the unprocessed files. This will identify the files you already processed in the destination directory and remove matching ones in the original directory to ensure nothing is reprocessed again.

## Insights for future developments
Due to limited time in testing the hypothesis, current phases of the research have yet to test out the method of using compare-sort on an ensemble of the same themed buckets (merged between different movies of all MPAA types) to establish a universal metric of bucket-specific intensity. If could be done, may have been more informative to predictions than frequencies, which carried the problem of PG-13 movies having many counts of profanity in the form of i.e. "Hech", as opposed to more intense profanity in R-rated movies. Obtaining a mean, standard deviation and outlier detection for each film will inform the intensities of buckets, delineating i.e., “Heck” (in PG-13) from “F..k” (in R). To obtain a dataset used to train an LLM model that can assign intensity scores on a universal scale, run `bucketSynthesis.py`


