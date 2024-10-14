from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import random
import spacy
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for session management

# Load the spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Load intents from the JSON file
with open('intents.json', 'r') as file:
    intents = json.load(file)['intents']

# User "database" loaded from a file
users = {}

# Load user data from users.json if it exists
def load_users():
    global users
    if os.path.exists('users.json'):
        with open('users.json', 'r') as file:
            users = json.load(file)

# Save user data to users.json
def save_users():
    with open('users.json', 'w') as file:
        json.dump(users, file)

# Load users when the app starts
load_users()

# Fallback AI response
def ai_fallback_response(user_message):
    return f"I'm not sure how to respond to '{user_message}', but I'm learning!"

# Save email to contact.txt
def save_email(email):
    with open('contact.txt', 'a') as f:
        f.write(f'{email}\n')

# New route for the root URL
@app.route('/')
def home():
    return redirect(url_for('login'))

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists and the password is correct
        if username in users and users[username] == password:
            session['username'] = username  # Save username in session
            flash('Login successful!', 'success')
            return redirect(url_for('chatbot'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username is already taken
        if username in users:
            flash('Username already taken', 'error')
        else:
            users[username] = password  # Save the user in the database
            save_users()  # Save the updated users data to the file
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html')

# Route for the chatbot
@app.route('/chatbot')
def chatbot():
    if 'username' not in session:
        return redirect(url_for('login'))
    session['conversation'] = []  # Initialize conversation history
    return render_template('index.html')

# Chatbot interaction route
@app.route('/ask', methods=['POST'])
def ask():
    user_message = request.form['message'].lower()
    session['conversation'].append({'user': user_message})

    response = None
    for intent in intents:
        for pattern in intent['patterns']:
            if pattern in user_message:
                response = random.choice(intent['responses'])
                break
        if response:
            break
    
    # If no response, ask for the user's email and save it
    if not response:
        response = ai_fallback_response(user_message)
        response += " Could you please provide your email for further assistance?"
        session['email_requested'] = True  # Flag that email was requested
    else:
        session['email_requested'] = False

    session['conversation'].append({'bot': response})
    return jsonify({'response': response})

# Route to collect email if chatbot fails to answer
@app.route('/submit_email', methods=['POST'])
def submit_email():
    if 'email_requested' in session and session['email_requested']:
        email = request.form['email']
        save_email(email)
        session['email_requested'] = False
        return jsonify({'response': 'Thank you! We will get back to you soon.'})
    
    return jsonify({'response': 'No email needed at the moment.'})

if __name__ == "__main__":
    app.run(debug=True)