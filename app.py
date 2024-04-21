# Import necessary modules
from flask import Flask, Response, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
from dotenv import load_dotenv
import requests
import os

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD')
app.config['GITHUB_PAT'] = os.getenv('GITHUB_PAT')

# Initialize SQLAlchemy database
db = SQLAlchemy(app)

# Configure BasicAuth for user login
basic_auth = BasicAuth(app)

# Define database models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=True)
    todos = db.relationship('Todo', backref='project', cascade='all, delete-orphan')

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('pending', 'complete'), default='pending', nullable=False)
    created_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=True)
    updated_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=True)

# Function to create all tables within the application context
def create_tables():
    with app.app_context():
        db.create_all()

# Call the function to create tables
create_tables()

# Route to render the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == app.config['BASIC_AUTH_USERNAME'] and password == app.config['BASIC_AUTH_PASSWORD']:
            return redirect(url_for('index'))  # Redirect to the main page upon successful login
        else:
            error_message = "Invalid username or password. Please try again."
            return render_template('login.html', error_message=error_message)
    else:
        return render_template('login.html')

# Route to render the index.html template
@app.route('/home')
@basic_auth.required
def index():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

# Route to create a new project
@app.route('/create-project', methods=['POST'])
def create_project():
    if request.method == 'POST':
        title = request.form['title']
        new_project = Project(title=title)
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('index'))  # Redirect to the main page after creating the project

# Route to render the project detail page
# @app.route('/projects/<int:project_id>/todo-list')
# @basic_auth.required
# def project_detail(project_id):
#     project = Project.query.get_or_404(project_id)
#     todos = project.todos
#      gist_url = create_secret_gist(project_id)

#     return render_template('project.html', project=project, todos=todos)
# Route to render the project detail page
# 
@app.route('/projects/<int:project_id>/todo-list')
@basic_auth.required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    todos = project.todos
    pending_todos = Todo.query.filter_by(project_id=project_id, status='pending').all()
    completed_todos = Todo.query.filter_by(project_id=project_id, status='complete').all()
    gist_url = create_secret_gist(project_id)
    return render_template('project.html', project=project, todos=todos, pending_todos=pending_todos, completed_todos=completed_todos, gist_url=gist_url)
# 
# Route to add a new todo to a project
@app.route('/projects/<int:project_id>/add-todo', methods=['POST'])
def add_todo_to_project(project_id):
    if request.method == 'POST':
        project = Project.query.get_or_404(project_id)
        description = request.form['description']
        new_todo = Todo(description=description, project=project)
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project_id))  # Redirect to the project detail page after adding the todo

# Flask route for updating the status of a todo item
@app.route('/projects/<int:project_id>/todos/<int:todo_id>/update-status', methods=['POST'])
def update_todo_status(project_id, todo_id):
    if request.method == 'POST':
        todo = Todo.query.get_or_404(todo_id)
        todo.status = 'complete' if todo.status == 'pending' else 'pending'
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project_id))

# Flask route for deleting a todo item
@app.route('/projects/<int:project_id>/todos/<int:todo_id>/delete', methods=['POST'])
def delete_todo(project_id, todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('project_detail', project_id=project_id))

# Route to handle AJAX request to update the status of a todo
@app.route('/update-todo-status', methods=['POST'])
def ajax_update_todo_status():
    if request.method == 'POST':
        data = request.get_json()
        todo_id = data.get('todo_id')
        status = data.get('status')
        
        if todo_id is None or status not in ['pending', 'complete']:
            return jsonify({'success': False, 'error': 'Invalid request parameters'}), 400

        todo = Todo.query.get(todo_id)
        if todo is None:
            return jsonify({'success': False, 'error': 'Todo not found'}), 404

        todo.status = status
        db.session.commit()
        return jsonify({'success': True}), 200
    
def generate_markdown_summary(project):
    # Generate markdown summary for the project
    # Include project title, number of completed todos, list of pending todos, list of completed todos
    markdown_summary = f"# {project.title}\n"
    total_todos = len(project.todos)
    completed_todos = sum(1 for todo in project.todos if todo.status == 'complete')
    markdown_summary += f"Summary: {completed_todos} / {total_todos} completed\n\n"
    
    # Add pending todos
    markdown_summary += "## Pending Todos\n"
    for todo in project.todos:
        if todo.status == 'pending':
            markdown_summary += f"- {todo.description}\n"
    
    # Add completed todos
    markdown_summary += "\n## Completed Todos\n"
    for todo in project.todos:
        if todo.status == 'complete':
            markdown_summary += f"- {todo.description}\n"

    return markdown_summary

def create_secret_gist(project_id):
    url = 'https://api.github.com/gists'
    headers = {'Authorization': f'token {app.config["GITHUB_PAT"]}'}
    project = Project.query.get_or_404(project_id)
    markdown_summary = generate_markdown_summary(project)
    payload = {
        'public': False,
        'files': {
            f'{project.title}.md': {
                'content': markdown_summary
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()['html_url']
    else:
        return None

# Example usage:
# access_token = 'your-access-token'
# project_id = 1  # Assuming you have a way to retrieve the project ID
# gist_url = create_secret_gist(access_token, project_id)
# if gist_url:
#     print('Secret gist created:', gist_url)
# else:
#     print('Failed to create secret gist')

if __name__ == '__main__':
    app.run(debug=True)
    
 
    
