# Team Management

Team Management is a web-based internal team management and project management portal built with Django.

The platform is designed to help software teams manage team members, assign tasks, track project progress, and share technical resources from a single workspace.

## 🚀 Project Overview

The system will provide three main modules:

* **Accounts** – User authentication, team profiles, roles, and team directory.
* **Tasks** – Project milestones, task management, priorities, deadlines, and Kanban board.
* **Resources** – Technical documents, external links, code snippets, file uploads, and comments.

## 🛠️ Technology Stack

* Python
* Django
* MySQL
* HTML
* Tailwind CSS
* Vanilla JavaScript
* Fetch API

## 📂 Project Structure

```text
Team_management/
│
├── accounts/       # Authentication and team management
├── tasks/          # Tasks, milestones and Kanban board
├── resources/      # Files, links, snippets and comments
│
├── Team_management/ # Main Django project configuration
├── templates/        # Common templates
├── static/           # CSS and JavaScript
├── media/            # Uploaded files
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 👥 Main Modules

### 1. Accounts

The Accounts module manages:

* User registration
* Login and logout
* User profiles
* Lead and Member roles
* Department information
* GitHub profiles
* Team directory

### 2. Tasks

The Tasks module manages:

* Project milestones
* Tasks
* Task assignment
* Task priority
* Due dates
* Task status
* Kanban board
* Search and filtering

Task statuses:

```text
Backlog → In Progress → Review → Done
```

### 3. Resources

The Resources module provides a shared knowledge vault for the team.

It supports:

* Documents
* PDF files
* Screenshots
* External links
* Code snippets
* Resource comments
* Copy URL/Snippet functionality

## ⚙️ Installation

Clone the repository:

```bash
git clone <repository-url>
cd Team_management
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

## 🔐 Environment Variables

Sensitive configuration such as database credentials and Django secret keys should be stored in a `.env` file and should not be committed to the repository.

## 📌 Project Status

🚧 **Currently in Development**

The project is being developed module by module, starting with the Accounts module followed by Tasks and Resources.

## 👨‍💻 Development

This project is intended for internal team collaboration, project tracking, and technical resource management.

More features and improvements will be added during development.
