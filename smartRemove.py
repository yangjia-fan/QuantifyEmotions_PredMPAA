import os
from os.path import join
from tqdm import tqdm

# Define folder paths
# DIR_IN = join("scripts", "Bucketed_EfficiencyModel")
# DIR_OUT = join("scripts", "APIready_Usage")
DIR_IN = join("scripts", "Bucketed_EfficiencyModel_Correction_Batch3")
DIR_OUT = join("scripts", "Bucketed_EfficiencyModel_Usage")

# Function to delete files in APIready folder that match the pattern
def delete_matching_files(bucketed_folder, apiready_folder):
    # Get list of files in bucketed folder
    bucketed_files = [f for f in os.listdir(bucketed_folder) if f.endswith("_Bucketed.json")]

    progress_bar = tqdm(bucketed_files, desc="Deleting Matching Files")

    for bucketed_file in progress_bar:
        # Derive the corresponding APIready file name
        base_name = bucketed_file.replace("_Bucketed.json", "")
        # apiready_file_name = f"{base_name}_APIready.json"
        apiready_file_name = f"{base_name}_Bucketed.json"

        # Full path of the file in APIready folder
        apiready_file_path = join(apiready_folder, apiready_file_name)

        # Check if the file exists in APIready folder
        if os.path.exists(apiready_file_path):
            # Delete the file
            os.remove(apiready_file_path)
            progress_bar.write(f"Deleted: {apiready_file_name}")
        else:
            progress_bar.write(f"{apiready_file_name} is already absent")


if __name__ == "__main__":
    delete_matching_files(DIR_IN, DIR_OUT)
