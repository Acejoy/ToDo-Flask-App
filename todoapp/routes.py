import os
import secrets

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from PIL import Image

from todoapp import app, bcrypt, db
from todoapp.forms import (LoginForm, RegistrationForm, ToDoListForm,
                           UpdateAccountForm)
from todoapp.models import ToDoList, User


@app.route('/')
@app.route('/home')
def home():
    if current_user.is_authenticated:
        print('Hello')
        print(current_user)
        todoLists = ToDoList.query.filter_by(author=current_user).all()
        print(todoLists)
        return render_template('home.html', lists=todoLists)
    else:
        return render_template('home.html', lists=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash(f'Login Unsuccessfull for {form.email.data}!Check email or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form= RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your Account has been created. You can now Login!', 'success')        
        return redirect(url_for('login'))
    return render_template('register.html', title='Register New Account', form=form)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))

def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex+f_ext
	picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
	output_size = (125, 125)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(picture_path)
	return picture_fn

@app.route('/account', methods =['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.picture.data:
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file
		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash('Your account has been updated', 'success')
		return redirect(url_for('account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
	return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route('/list/new', methods =['GET', 'POST'])
@login_required
def new_list():
	form = ToDoListForm()
	if form.validate_on_submit():
		new_todolist = ToDoList(title=form.title.data, content=form.content.data, author=current_user)
		db.session.add(new_todolist)
		db.session.commit()
		flash('Your ToDo List has been created', 'success')
		return redirect(url_for('home'))
	return render_template('create_list.html', title='Create New List',
												 form=form, legend='Create New List')


@app.route('/list/<int:list_id>')
def todolist(list_id):
	get_todolist = ToDoList.query.get_or_404(list_id)
	return render_template('todolist.html', title=get_todolist.title, tasklist=get_todolist)


@app.route('/list/<int:list_id>/update', methods=['GET', 'POST'])
@login_required
def update_list(list_id):
    cur_todolist = ToDoList.query.get_or_404(list_id)
    if cur_todolist.author != current_user:
        abort(403)
    
    form=ToDoListForm()
    if form.validate_on_submit():
        cur_todolist.title = form.title.data
        cur_todolist.content = form.content.data
        db.session.commit()
        flash('Your post has been updated', 'success')
        return redirect(url_for('todolist', list_id=list_id))
    elif request.method == 'GET':
        form.title.data = cur_todolist.title
        form.content.data = cur_todolist.content
    
    return render_template('create_list.html', title='Update List',
										 form=form, legend='Update List')


@app.route('/list/<int:list_id>/delete', methods=['POST'])
@login_required
def delete_list(list_id):
    cur_todolist = ToDoList.query.get_or_404(list_id)
    if cur_todolist.author != current_user:
        abort(403)
    db.session.delete(cur_todolist)
    db.session.commit()
    flash('Your List has been deleted', 'success')
    return redirect(url_for('home'))


