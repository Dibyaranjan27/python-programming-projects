from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todoos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), nullable=False, default="Medium")
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")  # <-- Add this!

# Home Route (Show Tasks with Pagination)
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)  # Get the page number from URL
    tasks = Task.query.paginate(page=page, per_page=5)  # Paginate results

    return render_template('index.html', tasks=tasks)  # Pass paginated object

# Add Task
@app.route('/add', methods=['POST'])
def add_task():
    content = request.form.get('content')
    priority = request.form.get('priority', 'Medium')
    status = request.form.get('status', 'Pending')  # <-- Get status from form
    due_date_str = request.form.get('due_date')

    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None

    if content:
        new_task = Task(content=content, priority=priority, status=status, due_date=due_date)
        db.session.add(new_task)
        db.session.commit()
    
    return redirect(url_for('index'))

# Mark Task as Completed (Toggle)
@app.route('/complete/<int:id>')
def complete_task(id):
    task = Task.query.get(id)
    if task:
        task.completed = not task.completed
        db.session.commit()
    return redirect(url_for('index'))

# Edit Task (Form Page)
@app.route('/edit/<int:id>')
def edit_task(id):
    task = Task.query.get(id)
    return render_template('edit.html', task=task)

# Update Task (Save Changes)
@app.route('/update/<int:id>', methods=['POST'])
def update_task(id):
    task = Task.query.get_or_404(id)

    # Get values from form
    task.content = request.form['content']
    task.status = request.form['status']  # Ensure you're correctly getting the selected value
    task.priority = request.form['priority']

    try:
        db.session.commit()
        return redirect(url_for('index'))  # Redirect to the main page after update
    except:
        return "There was an issue updating the task"

# Delete Task
@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get(id)
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

# Filter Tasks (Today, Upcoming, Completed, Pending)
@app.route('/filter/<category>')
def filter_tasks(category):
    page = request.args.get('page', 1, type=int)  # Get the page number

    # Filtering based on category
    if category == "today":
        tasks = Task.query.filter_by(status="Today").paginate(page=page, per_page=5)
    elif category == "upcoming":
        tasks = Task.query.filter_by(status="Upcoming").paginate(page=page, per_page=5)
    elif category == "completed":
        tasks = Task.query.filter_by(status="Completed").paginate(page=page, per_page=5)
    elif category == "pending":
        tasks = Task.query.filter_by(status="Pending").paginate(page=page, per_page=5)
    else:
        tasks = Task.query.paginate(page=page, per_page=5)  # Default: Show all tasks

    return render_template('index.html', tasks=tasks, category=category)


# Update Task Status (AJAX)
@app.route("/update_status/<int:task_id>", methods=["POST"])
def update_status(task_id):
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"success": False, "error": "Task not found"}), 404

        data = request.get_json()
        if data is None:
            return jsonify({"success": False, "error": "Invalid JSON data"}), 400

        completed = data.get("completed")

        if completed is None:
            return jsonify({"success": False, "error": "Missing 'completed' field"}), 400

        # Update the task status
        task.status = "Completed" if completed else "Upcoming"  # Adjust this as per logic
        db.session.commit()

        return jsonify({"success": True, "status": task.status})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
