import os
import spacy
from os.path import join
from os import makedirs
from tqdm import tqdm  # Import tqdm for progress bar

# Load spacy's English language model
nlp = spacy.load("en_core_web_sm")

countd = 0  # Counter for files deleted due to insufficient lines

def parse_mpaa_d_lines_to_individual_txt(input_file, output_file):
    global countd
    
    line_count = 0  # Initialize line counter

    with open(output_file, 'w') as txt_file:
        with open(input_file, 'r') as file:
            # Transcribe the first line as the MPAA prompt
            first_line = file.readline().strip()
            mpaa_value = first_line  # Assume the first line is the MPAA label
            txt_file.write(f"MPAA: {mpaa_value}\n")  # Write MPAA as the first line
            
            # Process lines starting with "D:" and "N:" for completions
            for line in file:
                line = line.strip()
                
                # Update current tag if line starts with "D:" or "N:"
                if line.startswith("D:") or line.startswith("N:"):
                    current_tag = line[:2]  # Set current tag to "D:" or "N:"
                    content = line.split(":", 1)[1].strip()  # Extract content after tag

                    # Use spacy to split content into sentences
                    doc = nlp(content)
                    sentences = [sent.text.strip() for sent in doc.sents]

                    # Write each sentence as a separate line with the current tag
                    for sentence in sentences:
                        if sentence:  # Ensure sentence is not empty
                            txt_file.write(f"{current_tag} {sentence}\n")
                            line_count += 1  # Increment line count

    # Check line count and delete the file if it has fewer than 100 lines (excluding the first line)
    if line_count < 100:
        os.remove(output_file)
        countd += 1

# MAIN Function
if __name__ == "__main__":
    DIR_FINAL = join("scripts", "refined")  # Original folder with .txt files
    DIR_OUT = join("scripts", "txt_spacy_ND")  # New output folder for .txt files

    # Ensure output directory exists
    makedirs(DIR_OUT, exist_ok=True)

    # Get list of files to process and initialize tqdm progress bar
    files = [f for f in os.listdir(DIR_FINAL) if f.endswith('.txt')]
    count = 0

    # Iterate over each .txt file in the input directory with tqdm for progress
    for filename in tqdm(files, desc="Processing files"):
        input_file = join(DIR_FINAL, filename)
        output_file = join(DIR_OUT, f"{os.path.splitext(filename)[0]}.txt")
        parse_mpaa_d_lines_to_individual_txt(input_file, output_file)
        count += 1

    print(f"{count - countd} files usable")  # Usable files are those not deleted


# import os
# import nltk
# from os.path import join
# from os import makedirs
# from tqdm import tqdm  # Import tqdm for progress bar

# # Download the Punkt tokenizer if it's not already available
# nltk.download("punkt_tab")
# from nltk.tokenize import sent_tokenize

# countd = 0  # Counter for files deleted due to insufficient lines

# def parse_mpaa_d_lines_to_individual_txt(input_file, output_file):
#     global countd
    
#     line_count = 0  # Initialize line counter

#     with open(output_file, 'w') as txt_file:
#         with open(input_file, 'r') as file:
#             # Transcribe the first line as the MPAA prompt
#             first_line = file.readline().strip()
#             mpaa_value = first_line  # Assume the first line is the MPAA label
#             txt_file.write(f"MPAA: {mpaa_value}\n")  # Write MPAA as the first line
            
#             # Process lines starting with "D:" and "N:" for completions
#             for line in file:
#                 line = line.strip()
                
#                 # Update current tag if line starts with "D:" or "N:"
#                 if line.startswith("D:") or line.startswith("N:"):
#                     current_tag = line[:2]  # Set current tag to "D:" or "N:"
#                     content = line.split(":", 1)[1].strip()  # Extract content after tag

#                     # Use nltk's sent_tokenize to split content into sentences
#                     sentences = sent_tokenize(content)

#                     # Write each sentence as a separate line with the current tag
#                     for sentence in sentences:
#                         sentence = sentence.strip()  # Remove extra spaces
#                         if sentence:  # Ensure sentence is not empty
#                             txt_file.write(f"{current_tag} {sentence}\n")
#                             line_count += 1  # Increment line count

#     # Check line count and delete the file if it has fewer than 100 lines (excluding the first line)
#     if line_count < 100:
#         os.remove(output_file)
#         countd += 1

# # MAIN Function
# if __name__ == "__main__":
#     DIR_FINAL = join("scripts", "refined")  # Original folder with .txt files
#     DIR_OUT = join("scripts", "txt_ND")  # New output folder for .txt files

#     # Ensure output directory exists
#     makedirs(DIR_OUT, exist_ok=True)

#     # Get list of files to process and initialize tqdm progress bar
#     files = [f for f in os.listdir(DIR_FINAL) if f.endswith('.txt')]
#     count = 0

#     # Iterate over each .txt file in the input directory with tqdm for progress
#     for filename in tqdm(files, desc="Processing files"):
#         input_file = join(DIR_FINAL, filename)
#         output_file = join(DIR_OUT, f"{os.path.splitext(filename)[0]}.txt")
#         parse_mpaa_d_lines_to_individual_txt(input_file, output_file)
#         count += 1

#     print(f"{count - countd} files usable")  # Usable files are those not deleted
