import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Program, Project, Task, Milestone, Contact, Material
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///project_manager.db')

# Fix for Heroku postgres:// to postgresql://
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create tables
with app.app_context():
    db.create_all()


# ===== AUTHENTICATION ROUTES =====

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ===== DASHBOARD =====

@app.route('/dashboard')
@login_required
def dashboard():
    programs = Program.query.filter_by(user_id=current_user.id).all()
    standalone_projects = Project.query.filter_by(user_id=current_user.id, program_id=None).all()
    
    # Get some statistics
    total_programs = len(programs)
    total_projects = Project.query.filter_by(user_id=current_user.id).count()
    total_tasks = Task.query.join(Project).filter(Project.user_id == current_user.id).count()
    total_contacts = Contact.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html', 
                         programs=programs,
                         standalone_projects=standalone_projects,
                         stats={
                             'programs': total_programs,
                             'projects': total_projects,
                             'tasks': total_tasks,
                             'contacts': total_contacts
                         })


# ===== PROGRAM ROUTES =====

@app.route('/programs')
@login_required
def programs():
    programs = Program.query.filter_by(user_id=current_user.id).all()
    return render_template('programs.html', programs=programs)


@app.route('/program/new', methods=['GET', 'POST'])
@login_required
def new_program():
    if request.method == 'POST':
        program = Program(
            user_id=current_user.id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            status=request.form.get('status', 'Planning')
        )
        
        if request.form.get('start_date'):
            program.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        if request.form.get('end_date'):
            program.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        db.session.add(program)
        db.session.commit()
        
        flash('Program created successfully!', 'success')
        return redirect(url_for('view_program', program_id=program.id))
    
    return render_template('program_form.html', program=None)


@app.route('/program/<int:program_id>')
@login_required
def view_program(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('view_program.html', program=program, all_contacts=contacts)


@app.route('/program/<int:program_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_program(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        program.name = request.form.get('name')
        program.description = request.form.get('description')
        program.status = request.form.get('status')
        
        if request.form.get('start_date'):
            program.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        if request.form.get('end_date'):
            program.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Program updated successfully!', 'success')
        return redirect(url_for('view_program', program_id=program.id))
    
    return render_template('program_form.html', program=program)


@app.route('/program/<int:program_id>/delete', methods=['POST'])
@login_required
def delete_program(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(program)
    db.session.commit()
    flash('Program deleted successfully!', 'success')
    return redirect(url_for('programs'))


# ===== PROJECT ROUTES =====

@app.route('/projects')
@login_required
def projects():
    all_projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('projects.html', projects=all_projects)


@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        project = Project(
            user_id=current_user.id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            status=request.form.get('status', 'Planning')
        )
        
        # Check if this is part of a program
        program_id = request.form.get('program_id')
        if program_id:
            project.program_id = int(program_id)
        
        if request.form.get('start_date'):
            project.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        if request.form.get('end_date'):
            project.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('view_project', project_id=project.id))
    
    programs = Program.query.filter_by(user_id=current_user.id).all()
    return render_template('project_form.html', project=None, programs=programs)


@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('view_project.html', project=project, all_contacts=contacts)


@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.status = request.form.get('status')
        
        program_id = request.form.get('program_id')
        project.program_id = int(program_id) if program_id else None
        
        if request.form.get('start_date'):
            project.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        if request.form.get('end_date'):
            project.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('view_project', project_id=project.id))
    
    programs = Program.query.filter_by(user_id=current_user.id).all()
    return render_template('project_form.html', project=project, programs=programs)


@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('projects'))


# ===== TASK ROUTES =====

@app.route('/project/<int:project_id>/task/new', methods=['GET', 'POST'])
@login_required
def new_task(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        task = Task(
            project_id=project_id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            status=request.form.get('status', 'Not Started'),
            priority=request.form.get('priority', 'Medium'),
            completion_percentage=int(request.form.get('completion_percentage', 0))
        )
        
        if request.form.get('start_date'):
            task.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        if request.form.get('end_date'):
            task.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    
    return render_template('task_form.html', task=None, project=project)


@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        task.name = request.form.get('name')
        task.description = request.form.get('description')
        task.status = request.form.get('status')
        task.priority = request.form.get('priority')
        task.completion_percentage = int(request.form.get('completion_percentage', 0))
        
        if request.form.get('start_date'):
            task.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        if request.form.get('end_date'):
            task.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('view_project', project_id=task.project_id))
    
    return render_template('task_form.html', task=task, project=task.project)


@app.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('view_project', project_id=project_id))


# ===== CONTACT ROUTES =====

@app.route('/contacts')
@login_required
def contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', contacts=contacts)


@app.route('/contact/new', methods=['GET', 'POST'])
@login_required
def new_contact():
    if request.method == 'POST':
        contact = Contact(
            user_id=current_user.id,
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            role=request.form.get('role'),
            notes=request.form.get('notes')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        flash('Contact created successfully!', 'success')
        return redirect(url_for('contacts'))
    
    return render_template('contact_form.html', contact=None)


@app.route('/contact/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        contact.name = request.form.get('name')
        contact.email = request.form.get('email')
        contact.phone = request.form.get('phone')
        contact.role = request.form.get('role')
        contact.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Contact updated successfully!', 'success')
        return redirect(url_for('contacts'))
    
    return render_template('contact_form.html', contact=contact)


@app.route('/contact/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('contacts'))


# ===== ASSIGNMENT ROUTES =====

@app.route('/program/<int:program_id>/assign', methods=['POST'])
@login_required
def assign_to_program(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    contact_id = request.form.get('contact_id')
    contact = Contact.query.get_or_404(contact_id)
    
    if contact not in program.assigned_contacts:
        program.assigned_contacts.append(contact)
        db.session.commit()
    
    flash(f'{contact.name} assigned to program', 'success')
    return redirect(url_for('view_program', program_id=program_id))


@app.route('/project/<int:project_id>/assign', methods=['POST'])
@login_required
def assign_to_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    contact_id = request.form.get('contact_id')
    contact = Contact.query.get_or_404(contact_id)
    
    if contact not in project.assigned_contacts:
        project.assigned_contacts.append(contact)
        db.session.commit()
    
    flash(f'{contact.name} assigned to project', 'success')
    return redirect(url_for('view_project', project_id=project_id))


@app.route('/task/<int:task_id>/assign', methods=['POST'])
@login_required
def assign_to_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.project.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    contact_id = request.form.get('contact_id')
    contact = Contact.query.get_or_404(contact_id)
    
    if contact not in task.assigned_contacts:
        task.assigned_contacts.append(contact)
        db.session.commit()
    
    flash(f'{contact.name} assigned to task', 'success')
    return redirect(url_for('view_project', project_id=task.project_id))


# ===== MATERIAL ROUTES =====

@app.route('/program/<int:program_id>/material/new', methods=['POST'])
@login_required
def new_program_material(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    material = Material(
        program_id=program_id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        quantity=float(request.form.get('quantity', 1)),
        unit=request.form.get('unit'),
        cost_per_unit=float(request.form.get('cost_per_unit', 0)) if request.form.get('cost_per_unit') else None,
        supplier=request.form.get('supplier'),
        notes=request.form.get('notes')
    )
    
    db.session.add(material)
    db.session.commit()
    flash('Material added successfully!', 'success')
    return redirect(url_for('view_program', program_id=program_id))


@app.route('/project/<int:project_id>/material/new', methods=['POST'])
@login_required
def new_project_material(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    material = Material(
        project_id=project_id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        quantity=float(request.form.get('quantity', 1)),
        unit=request.form.get('unit'),
        cost_per_unit=float(request.form.get('cost_per_unit', 0)) if request.form.get('cost_per_unit') else None,
        supplier=request.form.get('supplier'),
        notes=request.form.get('notes')
    )
    
    db.session.add(material)
    db.session.commit()
    flash('Material added successfully!', 'success')
    return redirect(url_for('view_project', project_id=project_id))


@app.route('/task/<int:task_id>/material/new', methods=['POST'])
@login_required
def new_task_material(task_id):
    task = Task.query.get_or_404(task_id)
    if task.project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    material = Material(
        task_id=task_id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        quantity=float(request.form.get('quantity', 1)),
        unit=request.form.get('unit'),
        cost_per_unit=float(request.form.get('cost_per_unit', 0)) if request.form.get('cost_per_unit') else None,
        supplier=request.form.get('supplier'),
        notes=request.form.get('notes')
    )
    
    db.session.add(material)
    db.session.commit()
    flash('Material added successfully!', 'success')
    return redirect(url_for('view_project', project_id=task.project_id))


@app.route('/material/<int:material_id>/delete', methods=['POST'])
@login_required
def delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Verify ownership
    if material.program_id:
        if material.program.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        redirect_id = material.program_id
        redirect_route = 'view_program'
        redirect_param = 'program_id'
    elif material.project_id:
        if material.project.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        redirect_id = material.project_id
        redirect_route = 'view_project'
        redirect_param = 'project_id'
    else:
        if material.task.project.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        redirect_id = material.task.project_id
        redirect_route = 'view_project'
        redirect_param = 'project_id'
    
    db.session.delete(material)
    db.session.commit()
    flash('Material deleted successfully!', 'success')
    return redirect(url_for(redirect_route, **{redirect_param: redirect_id}))


# ===== MILESTONE ROUTES =====

@app.route('/program/<int:program_id>/milestone/new', methods=['POST'])
@login_required
def new_program_milestone(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    milestone = Milestone(
        program_id=program_id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        target_date=datetime.strptime(request.form.get('target_date'), '%Y-%m-%d').date()
    )
    
    db.session.add(milestone)
    db.session.commit()
    flash('Milestone added successfully!', 'success')
    return redirect(url_for('view_program', program_id=program_id))


@app.route('/project/<int:project_id>/milestone/new', methods=['POST'])
@login_required
def new_project_milestone(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    milestone = Milestone(
        project_id=project_id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        target_date=datetime.strptime(request.form.get('target_date'), '%Y-%m-%d').date()
    )
    
    db.session.add(milestone)
    db.session.commit()
    flash('Milestone added successfully!', 'success')
    return redirect(url_for('view_project', project_id=project_id))


@app.route('/milestone/<int:milestone_id>/toggle', methods=['POST'])
@login_required
def toggle_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    
    # Verify ownership
    if milestone.program_id:
        if milestone.program.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    else:
        if milestone.project.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    
    milestone.achieved = not milestone.achieved
    if milestone.achieved:
        milestone.achieved_date = datetime.utcnow().date()
    else:
        milestone.achieved_date = None
    
    db.session.commit()
    return jsonify({'achieved': milestone.achieved})


@app.route('/milestone/<int:milestone_id>/delete', methods=['POST'])
@login_required
def delete_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    
    # Verify ownership and get redirect info
    if milestone.program_id:
        if milestone.program.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        redirect_id = milestone.program_id
        redirect_route = 'view_program'
        redirect_param = 'program_id'
    else:
        if milestone.project.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        redirect_id = milestone.project_id
        redirect_route = 'view_project'
        redirect_param = 'project_id'
    
    db.session.delete(milestone)
    db.session.commit()
    flash('Milestone deleted successfully!', 'success')
    return redirect(url_for(redirect_route, **{redirect_param: redirect_id}))


if __name__ == '__main__':
    app.run(debug=True)
