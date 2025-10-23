from flask import Flask, render_template, redirect, url_for, request, session, make_response, jsonify
from browniegate import *
import os
from dotenv import load_dotenv
import sqlite3

app = Flask(__name__)

load_dotenv(dotenv_path="creds.env")
PROJECT_UUID = os.getenv('PROJECT_UUID')
API_KEY = os.getenv('API_KEY')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
BROWNIE_GATE_URL = 'http://10.8.0.3:5000' 
app.secret_key = os.getenv('FLASK_SECRET_KEY')

connection_obj = sqlite3.connect('data.db')
cursor_obj = connection_obj.cursor()
table_creation_query = """
    CREATE TABLE IF NOT EXISTS data(
        user_id VARCHAR(255) NOT NULL,
        score INT
    );
"""
cursor_obj.execute(table_creation_query)
connection_obj.close()

gate = brownieGate(api_key=API_KEY, project_uuid=PROJECT_UUID, encryption_key=ENCRYPTION_KEY, url=BROWNIE_GATE_URL, debug=True)

def setup_user_in_database(user_id):
    connection_obj = sqlite3.connect('data.db')
    cursor = connection_obj.cursor()
    cursor.execute("SELECT count(*) FROM data WHERE user_id = ?",(user_id,))

    result = cursor.fetchone()
    if result:
        if result[0] == 0:
            cursor.execute("INSERT INTO data VALUES (?, ?)",(user_id, 0,)) 
            connection_obj.commit()
            
    connection_obj.close()

def setup_user_session(user_id):
    success, data = gate.get_user_data(user_id)
    if success:
        session['user_id'] = user_id
        session['username'] = data.get('username')
            
def get_user_score(user_id):
    connection_obj = sqlite3.connect('data.db')
    cursor = connection_obj.cursor()
    cursor.execute("SELECT score FROM data WHERE user_id = ?",(user_id,))
    result = cursor.fetchone()
    if result:
        score = result[0]
        session['score'] = score
    else:
        session['score'] = 0    
        
@app.route('/update_count', methods=['POST'])
def update_count():
    data = request.json
    score = data.get('score', 0)
    session['score'] = score
    
    connection_obj = sqlite3.connect('data.db')
    cursor = connection_obj.cursor()
    
    cursor.execute('UPDATE data SET score = ? WHERE user_id = ?', (score, session['user_id']))
    
    if cursor.rowcount == 0: 
        cursor.execute('INSERT INTO data (user_id, score) VALUES (?, ?)', (session['user_id'], score))
    
    connection_obj.commit()
    connection_obj.close()

    return jsonify({"status": "success", "score": score})

@app.route("/")
def root():
    return redirect(url_for('login'))

@app.route("/login")
def login():
    if session.get('user_id') or request.cookies.get('auth'):
        return redirect(url_for('counter'))
    
    return render_template("login.html", brownie_gate_url=f'{BROWNIE_GATE_URL}/gate/auth?project_uuid={PROJECT_UUID}')

@app.route("/auth/callback")
def callback():
    try:
        success, user_id = gate.verify_payload(gate.decrypt_payload(request.args.get("payload")))
        if success:
            resp = make_response(redirect(url_for('counter')))
            resp.set_cookie('auth',gate.generate_cookie(user_id).decode(),max_age=60*60*24*7,secure=False)
            setup_user_in_database(user_id)
            return resp
        else:
            return 'Error'

    except Exception as e:
        return str(e), 400
    
@app.route("/counter")
def counter():
    if not session.get('user_id'):
        if not request.cookies.get('auth'):
            return redirect(url_for('login'))
        
        user_id, cookie_hash = gate.decrypt_cookie(request.cookies.get('auth'))
        if not gate.validate_cookie(user_id, cookie_hash):
            return redirect(url_for('login'))
        
        setup_user_session(user_id)
        
    if not session.get('score'):
        get_user_score(session['user_id'])

    return render_template('counter.html')

@app.route('/logout')
def logout():
    gate.remove_cookie(session.get('user_id'))
    session.clear()
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('auth')
    return resp

@app.route('/get_pfp/me')
def get_pfp():
    if session.get('user_id'):
        pfp = gate.get_pfp(session.get('user_id'))
        
        if not pfp:
            pfp = None
        
        return {'success': True, 'pfp': pfp}
    else:
        return {'success': False}

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)