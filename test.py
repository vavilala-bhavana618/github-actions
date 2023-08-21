import os
import csv
import requests
import pandas as pd
from github import Github
from jira import JIRA
import base64
import time
import sys

#GitHub Configuration
ACCESS_TOKEN = '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' # Replace with your personal access token
WORKFLOWS_FOLDER = 'workflow_files'
headers = {
    'Authorization': f'token {ACCESS_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
# Listing the repositories
owner = 'bhavanavavilala'
repos = ('testrepo1','testrepo2')  # Add more repository details as needed
repo_names=[]
for repo in repos:
    repo_names+=[owner+'/'+repo]
    
# Function to fetch run and job steps from GitHub
def fetch_run_and_job_steps(repo_owner, repo_name, workflow_name, workflow_runs):
    run_and_job_steps = []
    
    for workflow_run in workflow_runs:
        run_id = workflow_run.id
        
        # Make a GET request to retrieve job details for the workflow run
        api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}/jobs'
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            jobs = response.json()['jobs']
            
            for job in jobs:
                
                # Extract job and step details here
                job_name = job['name']
                job_start_time = job['started_at']
                job_end_time = job['completed_at']
                job_status = job['status']
                job_conclusion = job['conclusion']
                
                if job_conclusion == "success":
                    if job_name == "Deploy-to-Dev":
                        deployment_counts['Dev'] += 1
                    elif job_name == "Deploy-to-QA":
                        deployment_counts['QA'] += 1
                    elif job_name == "Deploy-to-Prod":
                        deployment_counts['Prod'] += 1
    
                # Get the pull request details if the workflow is triggered by a pull request
                if 'pull_request' in job:
                    pull_request = job['pull_request']
                    pr_number = pull_request['number']
                    pr_title = pull_request['title']
                else:
                    pr_number = None
                    pr_title = None

                # Iterate over each step in the job
                for step in job['steps']:
                    step_name = step['name']
                    status = step['status']
                    conclusion = step.get('conclusion', None)
                    step_number = step['number']
                    started_at = step['started_at']
                    completed_at = step['completed_at']

                    run_and_job_steps.append({
                        'Run ID': run_id,
                        'Run Name': workflow_name,
                        'Repository Name': f'{repo_owner}/{repo_name}',
                        'Run Number': workflow_run.run_number,
                        'Run Attempt': workflow_run.run_attempt,
                        'Head Commit Message': workflow_run.head_commit.message,
                        'Author': workflow_run.head_commit.author.name,
                        'Job Name': job_name,
                        'Step Name': step_name,
                        'Job Start Time': job_start_time,
                        'Job End Time': job_end_time,
                        'Job Status': job_status,
                        'Job Conclusion': job_conclusion,
                        'Pull Request Number': pr_number,
                        'Pull Request Title': pr_title,
                        'Status': status,
                        'Conclusion': conclusion,
                        'Step Number': step_number,
                        'Started At': started_at,
                        'Completed At': completed_at,
                        'Deployment count': deployment_counts
                        })
            #print(deployment_counts)
        else:
            print(f'Failed to retrieve job details for workflow run ID: {run_id}')
        
    
    return run_and_job_steps #,repo_name,deployment_counts


# Create a list to store all data
all_data = []

# Loop through each repository
for repo_name in repo_names:
    REPO_OWNER, REPO_NAME = repo_name.split('/')
    print(f'Fetching data for repository: {REPO_NAME}...')

    deployment_counts = {
            'Dev': 0,
            'Prod': 0,
            'QA': 0
    }
    # Connect to GitHub using the access token
    g = Github(ACCESS_TOKEN)

    repo = g.get_repo(f'{REPO_OWNER}/{REPO_NAME}')
    workflows_folder = repo.get_contents('.github/workflows')
    workflow_names_list = [file.name for file in workflows_folder if file.type == 'file']

    # Iterate over each workflow name and process its data
    for workflow_name in workflow_names_list:
        workflow = repo.get_workflow(workflow_name)
        workflow_runs = workflow.get_runs()
        
        workflow_data = fetch_run_and_job_steps(REPO_OWNER, REPO_NAME, workflow_name, workflow_runs)
        # Append the workflow data to the all_data list
        all_data.extend(workflow_data)

# Create a DataFrame from the collected data
df = pd.DataFrame(all_data)

# Save the combined data to a single CSV file
combined_csv_file = 'all_workflow_steps_data.csv'
df.to_csv(combined_csv_file, index=False)

print(f'Successfully captured all workflow steps data from all repositories in "{combined_csv_file}".')

