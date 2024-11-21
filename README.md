# CI_Runtime
Calculate the fastest theoretical runtime for a Github Actions workflow assuming infinite concurrency and no waiting between jobs. 

# Features
- Fetches job runtimes for many workflow runs, and averages them
- Generates a dependency graph and identifies the longest execution path for all jobs

# Installation 
Prequisites:
- Python 3.7 or higher
- A GitHub personal access token with repo and workflow permissions.

Steps:
1. Clone the repository:
- git clone https://github.com/your-username/repository-name.git
2. Create a virtual environment and activate it:
- python3 -m venv venv
- source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
3. Install requirements:
- pip install -r requirements.txt

# Usage
- Update the "token" variable with your Github personal access token
- Update the "workflow_name" variable with the workflow you want
- Update the "workflow_file_path" variable with the path to your yaml file that defines the workflow
- run python3 Longest_CI_Path.py



