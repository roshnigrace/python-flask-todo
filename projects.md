import requests
import os

# Function to create a Gist with the given content
def create_gist(content, filename):
    # Define the Gist API URL
    gist_api_url = 'https://api.github.com/gists'

    # Define the data for the Gist creation request
    data = {
        'description': 'Project Summary',
        'public': False,
        'files': {
            filename: {
                'content': content
            }
        }
    }

    # Add authentication token if available
    access_token = os.environ.get('GITHUB_PAT')
    headers = {'Authorization': f'token {access_token}'} if access_token else {}

    # Make the POST request to create the Gist
    response = requests.post(gist_api_url, headers=headers, json=data)

    # Check if the request was successful
    if response.status_code == 201:
        gist_data = response.json()
        gist_url = gist_data['html_url']
        return gist_url
    else:
        print('Failed to create Gist:', response.text)
        return None

# Function to generate markdown content for the project summary
def generate_markdown(project_title, completed_todos, total_todos, pending_todos, completed_todos_list):
    # Generate markdown content for the project summary
    markdown_content = f"# {project_title}\n\n"
    markdown_content += f"Summary: {completed_todos} / {total_todos} completed.\n\n"

    markdown_content += "## Pending Todos\n"
    for todo in pending_todos:
        markdown_content += f"- [ ] {todo}\n"

    markdown_content += "\n## Completed Todos\n"
    for todo in completed_todos_list:
        markdown_content += f"- [x] {todo}\n"

    return markdown_content

# Example usage
if __name__ == "__main__":
    # Example project summary data
    project_title = "Sample Project"
    completed_todos = 5
    total_todos = 10
    pending_todos = ["Task 1", "Task 2", "Task 3"]
    completed_todos_list = ["Task 4", "Task 5"]

    # Generate markdown content for the project summary
    markdown_content = generate_markdown(project_title, completed_todos, total_todos, pending_todos, completed_todos_list)

    # Create a Gist with the markdown content
    gist_url = create_gist(markdown_content, f'{project_title}.md')
    if gist_url:
        print('Gist created successfully:', gist_url)
    else:
        print('Failed to create Gist')
