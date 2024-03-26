import itertools
import json
import os
import sys
from datetime import datetime

import git
import numpy as np


def load_json(file_path):
    """
    Load a JSON file from a file path.

    Parameters
    ----------
    file_path : str
        The path to the JSON file to load.

    Returns
    -------
    parameters : dict
        The loaded JSON file.
    """

    with open(file_path, "r") as file:
        parameters = json.load(file)
    return parameters


def dump_json(data, filename):
    """
    Dump data into a JSON file.

    Parameters
    ----------
    data : dict
        The data to dump.
    filename : str
        The path to the JSON file to create.
    """

    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


def create_directory_structure(dir, prefix="run_"):
    """
    Create a directory structure for a new job. The structure is as follows:

    dir_name/
    ├── run_1/
    │   ├── data/
    │   ├── slurm/
    │   │   ├── error/
    │   │   └── output/
    ├── run_2/
    │   ├── data/
    │   ├── slurm/
    │   │   ├── error/
    │   │   └── output/
    ...

    A new directory is created with the prefix followed by the next available number.

    Parameters
    ----------
    dir_name : str
        The name of directory where the new directory will be created.
    prefix : str
        The prefix to use for the new directory.

    Returns
    -------
    next_dir_path : str
        The path to the new directory.
    """

    # Ensure the directory exists
    os.makedirs(dir, exist_ok=True)

    # Find the next available subdirectory number with the prefix
    existing_dirs = [
        d
        for d in os.listdir(dir)
        if os.path.isdir(os.path.join(dir, d)) and d.startswith(prefix)
    ]
    highest_num = 0
    for dir_name in existing_dirs:
        try:
            num = int(dir_name.replace(prefix, ""))
            highest_num = max(highest_num, num)
        except ValueError:
            continue  # Skip directories that do not end with a number

    # Create the next subdirectory
    next_dir_name = f"{prefix}{highest_num + 1}"
    next_dir_path = os.path.join(dir, next_dir_name)
    os.makedirs(next_dir_path, exist_ok=True)

    # Create other subdirectories
    os.makedirs(os.path.join(next_dir_path, "data"), exist_ok=True)
    os.makedirs(os.path.join(next_dir_path, "slurm/error"), exist_ok=True)
    os.makedirs(os.path.join(next_dir_path, "slurm/output"), exist_ok=True)

    return next_dir_path


def generate_metadata_file(
    metadata_path, slurm_params, simulation_params, array_params, other_params
):
    """
    Generate a metadata file for the job. The metadata file contains the following categories:

    - general_metadata: author, creation_date, description, github_version
    - job_information: job_id, state, start_time, end_time, elapsed_time
    - slurm_parameters: all the parameters from the slurm parameters file
    - simulation_parameters: all the parameters from the simulation parameters file
    - array_parameters: all the parameters from the array parameters file

    Parameters
    ----------
    metadata_path : str
        The path to the metadata file to create.
    slurm_params : dict
        The parameters from the slurm parameters file.
    simulation_params : dict
        The parameters from the simulation parameters file.
    array_params : dict
        The parameters from the array parameters file.
    other_params : dict
        The parameters from the other parameters file.
    """

    metadata = {
        "general_metadata": {
            "author": "Julien Drapeau",
            "creation_date": datetime.today().strftime("%d/%m/%Y"),
            "description": other_params["description"],
            "github_version": git.Repo(
                search_parent_directories=True
            ).head.object.hexsha,
        },
        "job_information": {
            "job_id": None,
            "state": None,
            "start_time": None,
            "end_time": None,
            "elapsed_time": None,
        },
        "slurm_parameters": slurm_params,
        "simulation_parameters": simulation_params,
        "array_parameters": array_params,
    }
    with open(metadata_path, "w") as file:
        json.dump(metadata, file, indent=4)


def generate_slurm_script(
    subdir_path, python_script_path, slurm_params, simul_path, array_path
):
    """
    Generate a SLURM script for the job.

    Parameters
    ----------
    subdir_path : str
        The path to the subdirectory where containing the simulation results.
    slurm_params : dict
        The parameters from the slurm parameters file.
    simul_path : str
        The path to the simulation parameters file.
    array_path : str
        The path to the array parameters file.
    """

    # Create the SLURM script paths
    slurm_script_path = os.path.join(subdir_path, "job_script.sh")
    output_path = os.path.join(subdir_path, "slurm/output")
    error_path = os.path.join(subdir_path, "slurm/error")

    # Create the SLURM script
    with open(slurm_script_path, "w") as script:

        # Be careful about the indendation
        script.write(
            f"""#!/bin/bash
#SBATCH --partition={slurm_params["partition"]}
#SBATCH --account={slurm_params["account"]}
#SBATCH --array={slurm_params["array"]}
#SBATCH --time={slurm_params["time"]}
#SBATCH --job-name={slurm_params["job_name"]}
#SBATCH --cpus-per-task={slurm_params["cpus_per_task"]}
#SBATCH --mem-per-cpu={slurm_params["mem_per_cpu"]}
#SBATCH --output={output_path}/slurm-%A-%a.out
#SBATCH --error={error_path}/slurm-%A-%a.err
#SBATCH --mail-user=julien.drapeau@usherbrooke.ca
#SBATCH --mail-type=ALL

export JAX_ENABLE_X64=True # JAX uses int32 by default

module load StdEnv/2020
source ENV/bin/activate

# Define the position of the desired combination in the list (1-indexed)
position=$SLURM_ARRAY_TASK_ID

# Load the combination at the specified position from array_params.json
array_dict=$(jq --argjson pos "$((position - 1))" '.[$pos]' {array_path})

# Load the other dictionary from simul_params.json
simul_dict=$(<{simul_path})

# Merge both dictionary
merged=$(jq -n --argjson array_dict "$array_dict" --argjson simul_dict "$simul_dict" '$simul_dict + $array_dict')

# Launch the Python script (-u for unbuffered output)
python -u {python_script_path} "$merged"

echo 'My job is finished !'"""
        )

        # # Copy the script to the output directory
        # shutil.copyfile(slurm_script_path, os.path.join(os.getcwd(), "job_script.sh"))


def add_array_parameters(range_array_params):
    """
    Add array parameters to the simulation parameters. The array parameters are generated from the range_array_params. The range_array_params is a dictionary where the keys are the parameter names and the values are either a list of values or a dictionary with the keys "start", "end", and "step". The function generates all the possible combinations of the parameters. The function returns a list of dictionaries where each dictionary is a combination of the parameters.

    Parameters
    ----------
    range_array_params : dict
        A dictionary containing the range of values for the array parameters.
    """

    param_names = list(range_array_params.keys())

    param_ranges = []
    for param_name in param_names:

        # Check if the parameter is a list or a dictionary
        if isinstance(range_array_params[param_name], list):
            param_ranges.append(range_array_params[param_name])
        elif isinstance(range_array_params[param_name], dict):
            range = np.arange(
                range_array_params[param_name]["start"],
                range_array_params[param_name]["end"],
                range_array_params[param_name]["step"],
            ).tolist()
            param_ranges.append(range)
        else:
            raise ValueError("Invalid range type")

    combinations = list(itertools.product(*param_ranges))

    result = []
    for combination in combinations:
        result.append(dict(zip(param_names, combination)))

    return result


if __name__ == "__main__":

    # Find the parameter path from the command line
    if len(sys.argv) != 3:
        raise ValueError(
            "Usage: python tools/job_prepper.py parameter_path python_script_path"
        )

    python_script_path = os.path.join(sys.argv[2])
    parameter_path = sys.argv[1]

    # Find parameters path
    range_array_path = os.path.join(parameter_path, "range_array_params.json")
    array_path = os.path.join(parameter_path, "array_params.json")
    simul_path = os.path.join(parameter_path, "simul_params.json")
    slurm_path = os.path.join(parameter_path, "slurm_params.json")
    other_path = os.path.join(parameter_path, "other_params.json")

    # Load parameters from path
    range_array_params = load_json(range_array_path)
    simul_params = load_json(simul_path)
    slurm_params = load_json(slurm_path)
    other_params = load_json(other_path)

    # Make sure the output directory is the same both parameters files
    if slurm_params["output_directory"] != simul_params["output_directory"]:
        raise ValueError("Output directories are different.")

    # Create array parameters
    dump_json(add_array_parameters(range_array_params), array_path)

    # Create directories
    sub_dir_path = create_directory_structure(slurm_params["output_directory"])
    print("Created the following directory: ", sub_dir_path)

    # Create paths for the job
    # primary_job_path = os.path.join(os.getcwd(), "job_script.sh")
    secondary_job_path = os.path.join(sub_dir_path, "job_script.sh")
    metadata_path = os.path.join(sub_dir_path, "metadata.json")

    # Generate SLURM script
    generate_slurm_script(
        sub_dir_path, python_script_path, slurm_params, simul_path, array_path
    )

    # Grant permissions to the SLURM script
    # os.chmod(primary_job_path, 0o700)
    os.chmod(secondary_job_path, 0o700)

    # Generate metadata file
    generate_metadata_file(
        metadata_path, slurm_params, simul_params, range_array_params, other_params
    )

    print(
        "Job preparation was a success. To submit the job, run the following command:"
    )
    print(f"python tools/job_launcher.py {sub_dir_path}")
