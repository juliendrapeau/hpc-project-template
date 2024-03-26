import json
import os
import subprocess
import sys


def submit_job(slurm_script_path, metadata_file_path):
    """
    Submit a job to Slurm and update the metadata file with the job ID.

    Parameters
    ----------
    slurm_script_path : str
        Path to the Slurm script to be submitted.
    metadata_file_path : str
        Path to the metadata file.
    """

    # Submit the job to Slurm and capture the output
    result = subprocess.run(
        ["sbatch", slurm_script_path], stdout=subprocess.PIPE, text=True
    )
    job_id_str = result.stdout.strip()
    job_id = job_id_str.split()[-1]

    # Initially update metadata with the job ID
    update_metadata(metadata_file_path, {"job_id": job_id})


def update_metadata(metadata_file_path, job_details):
    """
    Update the metadata file with the job details.

    Parameters
    ----------
    metadata_file_path : str
        Path to the metadata file.
    job_details : dict
        Dictionary containing the job details to be added to the metadata.
    """

    # Load the existing metadata
    with open(metadata_file_path, "r") as file:
        metadata = json.load(file)

    # Update the metadata with the job details
    if "job_information" not in metadata:
        metadata["job_information"] = {}
    metadata["job_information"].update(job_details)

    # Save the updated metadata
    with open(metadata_file_path, "w") as file:
        json.dump(metadata, file, indent=4)


if __name__ == "__main__":

    # Find the subdirectory path from the command line
    sub_dir_path = sys.argv[1]

    slurm_script_path = os.path.join(sub_dir_path, "job_script.sh")
    metadata_file_path = os.path.join(sub_dir_path, "metadata.json")

    submit_job(slurm_script_path, metadata_file_path)
    print("Job submitted successfully.")
