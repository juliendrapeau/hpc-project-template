# Project Template  

A template for Python projects. A typical structure for a Python coding project is proposed. Moreover, a High-Performance Computing (HPC) pipeline is included to improve workflow on SLURM clusters.

## Usage  

You should download directly this repository and use it to start your project.

The branch "main" should be the main branch for developping and testing the code for your project. The branch "hpc" should be used on clusters using SLURM to help organize your data. Once your code is fully done and tested on the "main" branch, you should merge the "main" branch into the "hpc" branch. You can then simply pull the changes to the cluster.  

Currently, this project only supports job array as a way to send multiple jobs.  

On the cluster, you need to change the parameters files according to your needs. This template uses four parameters files:  

- slurm_params.json : Parameters necessary for launching a job on SLURM.
- simul_params.json : Main parameters necessary for running your Python script. Only add parameters that DO NOT CHANGE for each simulation in the job array.
- range_array_params.json : Changing parameters necessary for running your Python script. Only add parameters THAT DO CHANGE in between in task in the job array. You should add them as a list of parameters or as a dictionnary containing the appropriate range.
- other_params.json : General information to add to the metadata.json file, such as a description of the simulations.

Once this is done, you can prepare the job. To do this, use the following command:  

```
python tools/job_prepper.py parameters/simulation_name/
```

This creates the output directory and subdirectories, including the job script and the metadata file. Finally, you can run the job script using:  

```
python tools/job_launcher.py simulation_name/run_X/
```

## HPC Quickstart

Here is the basic steps to launch a job with the "HPC". Let's suppose that you are on the cluster, where you cloned your repository. Make sure that you pulled the latest commit from "main", that you commit the latest version of "hpc", and that the requirements-hpc.txt is updated (the githash of the current commit is saved)!

1. Change the four parameters files in "parameters/simulation_name/".  

2. Prepare the job.  

```
python tools/job_prepper.py parameters/simulation_name/
```

3. Launch the job.  

```
python tools/job_launcher.py simulation_name/run_X/
```

## To-Do  

Suggestions are welcome! Don't hesitate to contribute to the project by implementing new features. Keep it as simple and as well-documented as possible.  

- Add daemons to: launch jobs at regular time steps, update the metadata files after completion of the jobs, relaunch failed jobs.
- Implement a larger workflow with "Nextflow", "Maestro" or "SnakeMake".
- Implement a SQL database.
