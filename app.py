import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Disable proxies to avoid httpx conflicts
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/we_relate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth configuration
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

db = SQLAlchemy(app)

# Create Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
    client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
    scope=["openid", "email", "profile"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# Set up OAuth storage after models are defined

# Authentication service
def is_authenticated():
    return session.get('user_id') is not None

def get_current_user():
    if is_authenticated():
        return User.query.get(session['user_id'])
    return None

def create_or_update_user(user_info):
    """Create or update user from Google OAuth info"""
    user = User.query.filter_by(email=user_info['email']).first()
    
    if not user:
        user = User(
            email=user_info['email'],
            username=user_info.get('name', user_info['email'].split('@')[0]),
            google_id=user_info['id'],
            name=user_info.get('name'),
            picture=user_info.get('picture')
        )
        db.session.add(user)
    else:
        # Update existing user info
        user.google_id = user_info['id']
        user.name = user_info.get('name')
        user.picture = user_info.get('picture')
        if not user.username:
            user.username = user_info.get('name', user_info['email'].split('@')[0])
    
    db.session.commit()
    return user

# Make functions available to templates
@app.context_processor
def inject_user():
    return dict(get_current_user=get_current_user, is_authenticated=is_authenticated)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=True)
    picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    people = db.relationship('Person', backref='user', lazy=True, cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship("User")

# Set up OAuth storage after models are defined
google_bp.storage = SQLAlchemyStorage(OAuth, db.session, user=lambda: get_current_user())

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    diagnoses = db.Column(db.Text)
    communication_style = db.Column(db.Text)
    triggers = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=True)
    title = db.Column(db.String(200))
    scenario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize Anthropic client
def get_anthropic_client():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    print(f"API key loaded: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API key starts with: {api_key[:10]}...")
    
    if not api_key:
        print("No API key found in environment")
        return None
    
    try:
        # Initialize with explicit http client to avoid conflicts
        import httpx
        http_client = httpx.Client(timeout=60.0)
        client = anthropic.Anthropic(
            api_key=api_key,
            http_client=http_client
        )
        print("Anthropic client initialized successfully with custom httpx client")
        return client
    except Exception as e:
        print(f"Error with custom client: {e}")
        try:
            # Fallback to default initialization
            client = anthropic.Anthropic(api_key=api_key)
            print("Anthropic client initialized with defaults")
            return client
        except Exception as e2:
            print(f"Error with default client: {e2}")
            return None

# Routes
@app.route('/')
def index():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    user = get_current_user()
    if not user:
        # Clear invalid session and redirect to login
        session.pop('user_id', None)
        return redirect(url_for('login'))
    
    recent_conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.created_at.desc()).limit(5).all()
    people = Person.query.filter_by(user_id=user.id).all()
    
    return render_template('index.html', user=user, conversations=recent_conversations, people=people)

@app.route('/login')
def login():
    # Check if user is already authenticated
    if is_authenticated():
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/auth/google')
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    
    # Get user info from Google
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash('Failed to fetch user info from Google', 'error')
        return redirect(url_for('login'))
    
    user_info = resp.json()
    
    # Create or update user
    user = create_or_update_user(user_info)
    
    # Log the user in
    session['user_id'] = user.id
    
    flash(f'Welcome, {user.name or user.username}!', 'success')
    return redirect(url_for('index'))

# OAuth callback handler
@google_bp.route('/authorized')
def google_logged_in():
    if not google.authorized:
        flash('Authorization failed', 'error')
        return redirect(url_for('login'))
    
    return redirect(url_for('google_login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/api/sidebar-data')
def sidebar_data():
    if not is_authenticated():
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get people
    people = Person.query.filter_by(user_id=user.id).all()
    people_data = [{'id': p.id, 'name': p.name} for p in people]
    
    # Get recent conversations
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.created_at.desc()).limit(10).all()
    conversations_data = [{
        'id': c.id,
        'title': c.title,
        'date': c.created_at.strftime('%m/%d')
    } for c in conversations]
    
    return jsonify({
        'people': people_data,
        'conversations': conversations_data
    })

@app.route('/people')
def people():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    user = get_current_user()
    people = Person.query.filter_by(user_id=user.id).all()
    return render_template('people.html', people=people)

@app.route('/people/new', methods=['GET', 'POST'])
def new_person():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user = get_current_user()
        person = Person(
            user_id=user.id,
            name=request.form['name'],
            description=request.form.get('description', ''),
            diagnoses=request.form.get('diagnoses', ''),
            communication_style=request.form.get('communication_style', ''),
            triggers=request.form.get('triggers', '')
        )
        db.session.add(person)
        db.session.commit()
        return redirect(url_for('people'))
    
    return render_template('new_person.html')

@app.route('/people/<int:person_id>/edit', methods=['GET', 'POST'])
def edit_person(person_id):
    if not is_authenticated():
        return redirect(url_for('login'))
    
    user = get_current_user()
    person = Person.query.filter_by(id=person_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        person.name = request.form['name']
        person.description = request.form.get('description', '')
        person.diagnoses = request.form.get('diagnoses', '')
        person.communication_style = request.form.get('communication_style', '')
        person.triggers = request.form.get('triggers', '')
        db.session.commit()
        return redirect(url_for('people'))
    
    return render_template('edit_person.html', person=person)

@app.route('/chat')
def chat():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    user = get_current_user()
    people = Person.query.filter_by(user_id=user.id).all()
    return render_template('chat.html', people=people)

@app.route('/chat/new', methods=['POST'])
def new_chat():
    if not is_authenticated():
        return redirect(url_for('login'))
    
    user = get_current_user()
    person_id = request.form.get('person_id')
    scenario = request.form.get('scenario', '')
    
    conversation = Conversation(
        user_id=user.id,
        person_id=person_id if person_id else None,
        title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        scenario=scenario
    )
    db.session.add(conversation)
    db.session.commit()
    
    return redirect(url_for('conversation', conversation_id=conversation.id))

@app.route('/conversations/<int:conversation_id>')
def conversation(conversation_id):
    if not is_authenticated():
        return redirect(url_for('login'))
    
    user = get_current_user()
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first_or_404()
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
    
    return render_template('conversation.html', conversation=conversation, messages=messages)

@app.route('/conversations/<int:conversation_id>/send', methods=['POST'])
def send_message(conversation_id):
    if not is_authenticated():
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = get_current_user()
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first_or_404()
    
    user_message = request.form['message']
    
    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # Generate AI response
    client = get_anthropic_client()
    if not client:
        ai_response = "I'm sorry, but the AI service is not configured. Please check your API key."
    else:
        try:
            # Build context from partner info and conversation history
            context = build_conversation_context(conversation, user_message)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": context}]
            )
            ai_response = response.content[0].text
        except Exception as e:
            ai_response = f"I'm experiencing technical difficulties. Please try again later. Error: {str(e)}"
    
    # Save AI response
    ai_msg = Message(
        conversation_id=conversation.id,
        role='assistant',
        content=ai_response
    )
    db.session.add(ai_msg)
    db.session.commit()
    
    return render_template('message_partial.html', messages=[user_msg, ai_msg])

def build_conversation_context(conversation, user_message):
    context = """You are a relationship coach specializing in de-escalation communication. Your role is to help users practice healthy communication in all their human relationships.

Guidelines:
- Provide constructive feedback on communication approaches
- Suggest de-escalation techniques when appropriate
- Help reframe messages to be more empathetic and understanding
- Ask clarifying questions to better understand the situation
- Offer specific, actionable advice

"""
    
    # Add person context if available
    if conversation.person_id:
        person = Person.query.get(conversation.person_id)
        if person:
            context += f"""
Person Information:
- Name: {person.name}
- Description: {person.description}
- Diagnoses: {person.diagnoses}
- Communication Style: {person.communication_style}
- Known Triggers: {person.triggers}

"""
    
    # Add scenario context
    if conversation.scenario:
        context += f"Scenario: {conversation.scenario}\n\n"
    
    # Add conversation history
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
    if messages:
        context += "Conversation History:\n"
        for msg in messages:
            role = "User" if msg.role == "user" else "Coach"
            context += f"{role}: {msg.content}\n"
    
    context += f"\nUser: {user_message}\n\nCoach:"
    
    return context

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)