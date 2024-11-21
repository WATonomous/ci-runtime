import yaml
import requests
from datetime import datetime
from collections import defaultdict, deque

def parse_workflow_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    
#create a dependency graph based on a workflow file 
def create_dependency_graph(workflow_data):
    jobs = workflow_data.get('jobs', {})
    dependency_graph = {}

    # Iterate over each job in the workflow
    for job_name, job_data in jobs.items():
        needs = job_data.get('needs', [])
        if not isinstance(needs, list):
            needs = [needs]  # Ensure it's a list even if a single dependency

        # Map job to its immediate dependencies
        dependency_graph[job_name] = needs

    return dependency_graph
    # has the form of
    # {jobA: [dep1, dep2], jobB: [dep3, dep4]}

# Function to get run ids of a workflow (ex provision.yml)
def getRunIds(owner, repo, pages, workflow_name):
    # Define the URL for workflow runs
    Run_Ids = []
    for i in range(pages):

        runs_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs?'
        headers = {'Authorization': f'token {token}'}
        params = {'per_page': 100, 'page': i}  # Start with page 1

        # Send the request to get recent workflow runs
        response = requests.get(runs_url, headers=headers, params=params)
        runs_data = response.json()
       
        # Check if the request was successful
        if response.status_code == 200:
            # Loop through each workflow run and save its id
            for run in runs_data['workflow_runs']:
                run_id = run['id']
                run_name = run['name']
                #this API doesn't allow you to filter by workflow name 
                if (run_name == workflow_name):
                    Run_Ids.append(run_id)
        else:
            print(f"Failed to retrieve workflow runs: {response.status_code}")

    return Run_Ids

#a job specific to a workflow run, so not useful
# def getGithubJob(owner, repo, job_id):
#     getUrl = f"https://api.github.com//repos/{owner}/{repo}/actions/jobs/{job_id}"

# Loop through all workflow runs of a workflow

def getWorkflowJobs(owner, repo, run_ids):
    job_runtimes = defaultdict(list)
    for id in run_ids:
        getUrl = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{id}/jobs?per_page=67"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(getUrl, headers=headers)
        jobs = response.json().get('jobs', [])

        for job in jobs:
            job_name = job['name']
            started_at = job['started_at']
            completed_at = job['completed_at']

            # Calculate duration if both timestamps are available
            if started_at and completed_at:
                start_time = datetime.fromisoformat(
                    started_at[:-1])  # Remove the 'Z'
                end_time = datetime.fromisoformat(
                    completed_at[:-1])  # Remove the 'Z'
                #duration = end_time - start_time
                duration = int((end_time - start_time).total_seconds())
                job_runtimes[job_name].append(duration)

    return job_runtimes

def AvgRuntimes(job_runtimes):

    newDict = {}

    for key in job_runtimes:
        avg = 0
        counted = 0
        for num in job_runtimes[key]:
            if num != 0:
                avg += num
                counted += 1
        if avg == 0 or counted ==0:
            avg = 0
        else:
            avg = avg // counted

        newDict[key] = avg
    return newDict

def calculate_longest_path(dependency_graph, job_runtimes):
    # Store the longest finish times for each job
    longest_finish_times = {}

    # Track the actual longest path (sequence of jobs)
    longest_paths = {}

    # Initialize the queue for jobs that can be run (no dependencies)
    queue = deque()

    # In-degree (to track jobs with no unsatisfied dependencies)
    in_degree = {job: 0 for job in dependency_graph}

    # Calculate the in-degrees of each job
    for job, dependencies in dependency_graph.items():
        for dep in dependencies:
            in_degree[dep] += 1

            # a count of each job and how many things it depends on
            # {'shellcheck': 1, 'ensure_file_sizes_are_within_limits': 1,
            # 'validate_provision_workflow_completeness': 1, 'ensure_directory_is_up_to_date': 3,
            # 'validate_host_schema': 12 ... }

    # Initialize the queue with jobs that have no dependencies
    for job in dependency_graph:
        if in_degree[job] == 0:
            queue.append(job)
            # Initialize longest time with the runtime of the job
            # Default to 0 if not in job_runtimes
            job_runtime = job_runtimes.get(job, 0)
            # Initialize with its own runtime
            longest_finish_times[job] = job_runtime
            longest_paths[job] = [job]  # Initialize the path to just this job

    # Traverse the dependency graph in topological order
    while queue:
        current_job = queue.popleft()

        # Process each dependent job
        for dependent_job in dependency_graph.get(current_job, []):
            # Ensure finish times and paths are initialized for dependent_job
            if dependent_job not in longest_finish_times:
                longest_finish_times[dependent_job] = 0
                # Initialize path for longest
                longest_paths[dependent_job] = []

            # Calculate the finish time for the longest path
            longest_current_finish = longest_finish_times[current_job] + job_runtimes.get(dependent_job, 0)

            if longest_current_finish > longest_finish_times[dependent_job]:
                longest_finish_times[dependent_job] = longest_current_finish
                # Update the longest path
                longest_paths[dependent_job] = longest_paths[current_job] + \
                    [dependent_job]

            # Decrement the in-degree and add to queue if it has no more dependencies
            in_degree[dependent_job] -= 1
            if in_degree[dependent_job] == 0:
                queue.append(dependent_job)

    # The overall theoretical longest runtime is the maximum finish time
    longest_runtime = max(longest_finish_times.values(), default=0)

    # Find the job that corresponds to the longest runtime path
    longest_job = max(longest_finish_times,
                      key=longest_finish_times.get, default=None)

    # Retrieve the longest path
    longest_path = longest_paths.get(longest_job, [])

    return {
        "longest_runtime": longest_runtime,
        "longest_path": longest_path
    }

### COMMANDS ###
workflow_file_path = 'provision.yml'  # Assuming it's in the same directory

# Replace with your GitHub token
token = 'your-personal-access-token'
owner = 'WATonomous'
repo = 'infra-config'

parsed_workflow = parse_workflow_yaml(workflow_file_path)

dependency_graph = create_dependency_graph(parsed_workflow)

# Number of Pages to fetch
num_pages = 5

# The workflow you want to fetch
workflow_name = "Provision"
# Needs to fetch all previous runs of all workflows and manually sift through them for the one you want
run_ids = getRunIds(owner, repo, 2, workflow_name)

# Fetch job runtime data from each workflow run
job_runtimes = getWorkflowJobs(owner, repo, run_ids)

print(job_runtimes)

# Get the average runtime for each job
avg_job_runtimes = AvgRuntimes(job_runtimes)

print(avg_job_runtimes)

result = calculate_longest_path(dependency_graph, avg_job_runtimes)
print(result)

