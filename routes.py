import os
from flask import render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, socketio
from models import User, Project, Service, Testimonial, ChatMessage, SiteConfig
from forms import LoginForm, RegistrationForm, ProfileForm, ProjectForm, ServiceForm, TestimonialForm, ChatMessageForm, SiteConfigForm
from urllib.parse import urlparse
from flask_socketio import emit, join_room, leave_room

# Public routes
@app.route('/')
@app.route('/index')
def index():
    projects = Project.query.order_by(Project.created_at.desc()).limit(3).all()
    services = Service.query.all()
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).limit(4).all()
    return render_template('index.html', 
                           title='SeuCodigo - Portfólio Profissional',
                           projects=projects,
                           services=services,
                           testimonials=testimonials)

@app.route('/projects')
def projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('projects.html', title='Projetos - SeuCodigo', projects=projects)

@app.route('/services')
def services():
    services = Service.query.all()
    return render_template('services.html', title='Serviços - SeuCodigo', services=services)

@app.route('/testimonials')
def testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('testimonials.html', title='Depoimentos - SeuCodigo', testimonials=testimonials)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Se o usuário já estiver logado, verifica se é admin e redireciona para a página adequada
        app.logger.info(f"Usuário já autenticado: {current_user.username}, Admin: {current_user.is_admin}")
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        app.logger.info(f"Tentativa de login com: {form.email.data}")
        
        # Tenta encontrar o usuário por email ou nome de usuário
        user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.email.data)
        ).first()
        
        if user is None:
            app.logger.info("Usuário não encontrado")
            flash('Email/usuário ou senha inválidos', 'danger')
            return redirect(url_for('login'))
        
        app.logger.info(f"Usuário encontrado: {user.username}, Admin: {user.is_admin}")
            
        if not user.check_password(form.password.data):
            app.logger.info("Senha incorreta")
            flash('Email/usuário ou senha inválidos', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        app.logger.info(f"Next page: {next_page}")
        
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        flash('Login realizado com sucesso!', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='Login - SeuCodigo', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Você saiu da sua conta', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Parabéns, você está registrado! Agora você pode fazer login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Registrar - SeuCodigo', form=form)

# User profile routes
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Seu perfil foi atualizado!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.bio.data = current_user.bio
    
    return render_template('profile.html', title='Meu Perfil - SeuCodigo', form=form)

# Chat routes
@app.route('/chat', methods=['GET'])
@login_required
def chat():
    form = ChatMessageForm()
    
    # Get admin user for chat
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        flash('Não há administrador disponível para chat no momento.', 'warning')
        return redirect(url_for('index'))
    
    # Get chat history between current user and admin
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == admin.id)) |
        ((ChatMessage.sender_id == admin.id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp).all()
    
    # Mark unread messages as read
    unread_messages = ChatMessage.query.filter_by(
        recipient_id=current_user.id, 
        sender_id=admin.id,
        read=False
    ).all()
    
    for msg in unread_messages:
        msg.read = True
    
    db.session.commit()
    
    return render_template('chat.html', 
                          title='Chat - SeuCodigo', 
                          form=form, 
                          messages=messages, 
                          admin=admin, 
                          socket_enabled=True)

@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    # Get chat partner id from request or use admin id
    partner_id = request.args.get('partner_id', type=int)
    if not partner_id:
        # Default to admin if no partner specified
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            partner_id = admin.id
        else:
            return jsonify({'error': 'No chat partner found'}), 404
    
    # Get messages between the current user and the partner
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == partner_id)) |
        ((ChatMessage.sender_id == partner_id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp).all()
    
    # Mark unread messages as read
    unread_messages = ChatMessage.query.filter_by(
        recipient_id=current_user.id, 
        sender_id=partner_id,
        read=False
    ).all()
    
    for msg in unread_messages:
        msg.read = True
    
    db.session.commit()
    
    return jsonify([msg.to_dict() for msg in messages])

@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    data = request.json
    if not data or 'content' not in data or 'recipient_id' not in data:
        return jsonify({'error': 'Invalid message data'}), 400
    
    recipient = User.query.get(data['recipient_id'])
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404
    
    message = ChatMessage(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        content=data['content']
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify(message.to_dict()), 201

# Site configuration route
@app.route('/admin/site-config', methods=['GET', 'POST'])
@login_required
def admin_site_config():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    from utils import save_uploaded_file
    
    config = SiteConfig.get_settings()
    form = SiteConfigForm()
    
    if form.validate_on_submit():
        # Processar upload do logo
        if form.logo_file.data:
            logo_path = save_uploaded_file(form.logo_file.data, subfolder='logo')
            if logo_path:
                config.logo_url = logo_path
        # Caso contrário, usar URL se foi fornecida
        elif form.logo_url.data:
            config.logo_url = form.logo_url.data
            
        # Processar upload do favicon
        if form.favicon_file.data:
            favicon_path = save_uploaded_file(form.favicon_file.data, subfolder='favicon')
            if favicon_path:
                config.favicon_url = favicon_path
        # Caso contrário, usar URL se foi fornecida
        elif form.favicon_url.data:
            config.favicon_url = form.favicon_url.data
        
        # Atualizar demais configurações
        config.company_name = form.company_name.data
        config.email = form.email.data
        config.phone = form.phone.data
        config.country = form.country.data
        config.address = form.address.data
        config.latitude = form.latitude.data
        config.longitude = form.longitude.data
        config.whatsapp = form.whatsapp.data
        config.instagram = form.instagram.data
        config.facebook = form.facebook.data
        config.linkedin = form.linkedin.data
        config.twitter = form.twitter.data
        config.youtube = form.youtube.data
        config.github = form.github.data
        
        db.session.commit()
        flash('Configurações do site atualizadas com sucesso!', 'success')
        return redirect(url_for('admin_site_config'))
    
    elif request.method == 'GET':
        form.company_name.data = config.company_name
        form.email.data = config.email
        form.phone.data = config.phone
        form.country.data = config.country
        form.address.data = config.address
        form.latitude.data = config.latitude
        form.longitude.data = config.longitude
        form.logo_url.data = config.logo_url
        form.favicon_url.data = config.favicon_url
        form.whatsapp.data = config.whatsapp
        form.instagram.data = config.instagram
        form.facebook.data = config.facebook
        form.linkedin.data = config.linkedin
        form.twitter.data = config.twitter
        form.youtube.data = config.youtube
        form.github.data = config.github
    
    return render_template('admin/site_config.html', 
                          title='Configurações do Site - SeuCodigo',
                          form=form,
                          config=config)

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    projects_count = Project.query.count()
    services_count = Service.query.count()
    testimonials_count = Testimonial.query.count()
    users_count = User.query.count()
    
    # Get users with unread messages
    users_with_messages = db.session.query(User).join(
        ChatMessage, ChatMessage.sender_id == User.id
    ).filter(
        ChatMessage.recipient_id == current_user.id,
        ChatMessage.read == False
    ).distinct().all()
    
    return render_template('admin/dashboard.html', 
                           title='Painel Admin - SeuCodigo',
                           projects_count=projects_count,
                           services_count=services_count,
                           testimonials_count=testimonials_count,
                           users_count=users_count,
                           users_with_messages=users_with_messages)

@app.route('/admin/projects', methods=['GET', 'POST'])
@login_required
def admin_projects():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            image_url=form.image_url.data,
            link=form.link.data
        )
        db.session.add(project)
        db.session.commit()
        flash('Projeto adicionado com sucesso!', 'success')
        return redirect(url_for('admin_projects'))
    
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('admin/projects.html', 
                           title='Gerenciar Projetos - SeuCodigo',
                           form=form, 
                           projects=projects)

@app.route('/admin/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    project = Project.query.get_or_404(id)
    form = ProjectForm()
    
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.image_url = form.image_url.data
        project.link = form.link.data
        db.session.commit()
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_projects'))
    elif request.method == 'GET':
        form.title.data = project.title
        form.description.data = project.description
        form.image_url.data = project.image_url
        form.link.data = project.link
    
    return render_template('admin/projects.html', 
                           title='Editar Projeto - SeuCodigo',
                           form=form, 
                           edit_mode=True,
                           project=project,
                           projects=Project.query.order_by(Project.created_at.desc()).all())

@app.route('/admin/projects/<int:id>/delete', methods=['POST'])
@login_required
def delete_project(id):
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash('Projeto excluído com sucesso!', 'success')
    return redirect(url_for('admin_projects'))

@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(
            title=form.title.data,
            description=form.description.data,
            icon=form.icon.data,
            price=form.price.data
        )
        db.session.add(service)
        db.session.commit()
        flash('Serviço adicionado com sucesso!', 'success')
        return redirect(url_for('admin_services'))
    
    services = Service.query.all()
    return render_template('admin/services.html', 
                           title='Gerenciar Serviços - SeuCodigo',
                           form=form, 
                           services=services)

@app.route('/admin/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_service(id):
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    service = Service.query.get_or_404(id)
    form = ServiceForm()
    
    if form.validate_on_submit():
        service.title = form.title.data
        service.description = form.description.data
        service.icon = form.icon.data
        service.price = form.price.data
        db.session.commit()
        flash('Serviço atualizado com sucesso!', 'success')
        return redirect(url_for('admin_services'))
    elif request.method == 'GET':
        form.title.data = service.title
        form.description.data = service.description
        form.icon.data = service.icon
        form.price.data = service.price
    
    return render_template('admin/services.html', 
                           title='Editar Serviço - SeuCodigo',
                           form=form, 
                           edit_mode=True,
                           service=service,
                           services=Service.query.all())

@app.route('/admin/services/<int:id>/delete', methods=['POST'])
@login_required
def delete_service(id):
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Serviço excluído com sucesso!', 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/testimonials', methods=['GET', 'POST'])
@login_required
def admin_testimonials():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            client_name=form.client_name.data,
            content=form.content.data,
            company=form.company.data,
            position=form.position.data,
            rating=form.rating.data
        )
        db.session.add(testimonial)
        db.session.commit()
        flash('Depoimento adicionado com sucesso!', 'success')
        return redirect(url_for('admin_testimonials'))
    
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', 
                           title='Gerenciar Depoimentos - SeuCodigo',
                           form=form, 
                           testimonials=testimonials)

@app.route('/admin/testimonials/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_testimonial(id):
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    testimonial = Testimonial.query.get_or_404(id)
    form = TestimonialForm()
    
    if form.validate_on_submit():
        testimonial.client_name = form.client_name.data
        testimonial.content = form.content.data
        testimonial.company = form.company.data
        testimonial.position = form.position.data
        testimonial.rating = form.rating.data
        db.session.commit()
        flash('Depoimento atualizado com sucesso!', 'success')
        return redirect(url_for('admin_testimonials'))
    elif request.method == 'GET':
        form.client_name.data = testimonial.client_name
        form.content.data = testimonial.content
        form.company.data = testimonial.company
        form.position.data = testimonial.position
        form.rating.data = testimonial.rating
    
    return render_template('admin/testimonials.html', 
                           title='Editar Depoimento - SeuCodigo',
                           form=form, 
                           edit_mode=True,
                           testimonial=testimonial,
                           testimonials=Testimonial.query.order_by(Testimonial.created_at.desc()).all())

@app.route('/admin/testimonials/<int:id>/delete', methods=['POST'])
@login_required
def delete_testimonial(id):
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    flash('Depoimento excluído com sucesso!', 'success')
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/chats')
@login_required
def admin_chats():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    # Get users who have sent messages to admin
    users = db.session.query(User).join(
        ChatMessage, ChatMessage.sender_id == User.id
    ).filter(
        ChatMessage.recipient_id == current_user.id,
        User.id != current_user.id
    ).distinct().all()
    
    # Get selected user or first user in the list
    selected_user_id = request.args.get('user_id', type=int)
    selected_user = None
    
    if selected_user_id:
        selected_user = User.query.get(selected_user_id)
    elif users:
        selected_user = users[0]
    
    if selected_user:
        # Get chat messages
        messages = ChatMessage.query.filter(
            ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == selected_user.id)) |
            ((ChatMessage.sender_id == selected_user.id) & (ChatMessage.recipient_id == current_user.id))
        ).order_by(ChatMessage.timestamp).all()
        
        # Mark unread messages as read
        unread_messages = ChatMessage.query.filter_by(
            recipient_id=current_user.id, 
            sender_id=selected_user.id,
            read=False
        ).all()
        
        for msg in unread_messages:
            msg.read = True
        
        db.session.commit()
    else:
        messages = []
    
    form = ChatMessageForm()
    
    return render_template('admin/chats.html', 
                          title='Gerenciar Mensagens - SeuCodigo',
                          users_with_messages=users,
                          current_chat_user=selected_user,
                          messages=messages,
                          form=form,
                          socket_enabled=True)

# Página de teste para admin
@app.route('/admin-test')
def admin_test():
    return render_template('admin_test.html')

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        # Create a personal room for the user
        join_room(str(current_user.id))
        app.logger.info(f'User {current_user.id} connected')

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(str(current_user.id))
        app.logger.info(f'User {current_user.id} disconnected')

@socketio.on('join_chat')
def handle_join_chat(data):
    if current_user.is_authenticated:
        # Join a chat room between the current user and the partner
        partner_id = data.get('partner_id')
        if partner_id:
            # Create a unique room name for the conversation
            room = get_chat_room_name(current_user.id, int(partner_id))
            join_room(room)
            app.logger.info(f'User {current_user.id} joined chat room with {partner_id}')

@socketio.on('leave_chat')
def handle_leave_chat(data):
    if current_user.is_authenticated:
        partner_id = data.get('partner_id')
        if partner_id:
            room = get_chat_room_name(current_user.id, int(partner_id))
            leave_room(room)
            app.logger.info(f'User {current_user.id} left chat room with {partner_id}')

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return
    
    content = data.get('content')
    recipient_id = data.get('recipient_id')
    
    if not content or not recipient_id:
        return
    
    # Save the message to the database
    message = ChatMessage(
        sender_id=current_user.id,
        recipient_id=int(recipient_id),
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    # Prepare message data for the clients
    message_data = message.to_dict()
    
    # Emit to the chat room
    room = get_chat_room_name(current_user.id, int(recipient_id))
    emit('new_message', message_data, to=room)
    
    # Also emit to the recipient's personal room in case they're not in the chat room
    emit('new_message_notification', message_data, to=str(recipient_id))
    app.logger.info(f'Message sent from {current_user.id} to {recipient_id}')

# Helper function to create a consistent chat room name
def get_chat_room_name(user1_id, user2_id):
    # Always use the smaller ID first to ensure consistent room names
    return f"chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
