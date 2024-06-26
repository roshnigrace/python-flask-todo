﻿# Todo Manager Web Application

## Description

This is a Flask-based web application for managing todo lists and projects. It allows users to create projects, add todos to each project, mark todos as complete or pending, and delete todos.

## Features

- User authentication for secure login
- Create new projects with customizable titles
- Add todos to each project
- Mark todos as complete or pending
- Delete todos
- Export project summary as a secret gist on GitHub

## Setup Instructions

1. Clone the repository to your local machine.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Set up a MySQL database named `todo_db`.
4. Create a `.env` file in the project directory and add the following environment variables:Replace the database URI, username, password, and GitHub Personal Access Token (`GITHUB_PAT`) with your own values.
5. Run the Flask application using `python app.py`.
6. Access the application in your web browser at `http://localhost:5000`.

## Usage

- To log in, use the following credentials:
- Username: admin
- Password: admin

### How to Access the Summary

After creating or updating a project's todos, you can view the project summary by clicking on the provided GitHub Gist link. This link redirects you to the Gist page on GitHub, where you can see the markdown file containing the project summary.

