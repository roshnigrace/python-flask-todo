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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/todo_db'
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'admin'


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
@app.route('/projects/<int:project_id>/todo-list')
@basic_auth.required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    todos = project.todos
    return render_template('project.html', project=project, todos=todos)

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
    
# Function to export project summary as a secret gist on GitHub
def generate_markdown(project_title, completed_todos, total_todos, pending_todos, completed_todos_list):
    # Generate markdown content for the gist
    markdown_content = f"# {project_title}\n\n"
    markdown_content += f"**Summary:** {completed_todos} / {total_todos} completed.\n\n"
    
    # Section 1: Task list of pending todos
    markdown_content += "## Pending Todos\n"
    for todo in pending_todos:
        markdown_content += f"- [ ] {todo}\n"
    
    # Section 2: Task list of completed todos
    markdown_content += "\n## Completed Todos\n"
    for todo in completed_todos_list:
        markdown_content += f"- [x] {todo}\n"
    
    # Create a secret gist on GitHub
    access_token = os.environ.get('GITHUB_PAT')
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'files': {
            f'{project_title}.md': {
                'content': markdown_content
            }
        },
        'public': False
    }
    response = requests.post('https://api.github.com/gists', headers=headers, json=data)
    
    if response.status_code == 201:
        gist_url = response.json()['html_url']
        return gist_url  # Return the gist URL as a string
    else:
        return None  # Return None if gist creation fails
# Route to export project summary as a secret gist on GitHub
@app.route('/export-summary')
def export_summary():
    # Query project summary data from the database
    project = Project.query.first()  # Assuming there is at least one project in the database
    completed_todos = Todo.query.filter_by(status='complete').count()
    total_todos = Todo.query.count()
    pending_todos = [todo.description for todo in Todo.query.filter_by(status='pending').all()]
    completed_todos_list = [todo.description for todo in Todo.query.filter_by(status='complete').all()]

    # Render the summary template with the data
    return render_template('summary.html', project=project, completed_todos=completed_todos, total_todos=total_todos, pending_todos=pending_todos, completed_todos_list=completed_todos_list)
if __name__ == '__main__':
    app.run(debug=True)
