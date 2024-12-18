from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = "Air99**"

# Database connection function
def get_db_connection():
    conn = sqlite3.connect("debate.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    # Fetch topics from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM topic')
    topics = cursor.fetchall()  # Fixed variable name from 'topic' to 'topics'
    conn.close()
    return render_template("index.html", topics=topics)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for("register"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user (userName, password, isAdmin) VALUES (?, ?, ?)', (username, password, 0))  # Set default time values to 0
        conn.commit()
        conn.close()
        flash('User registration successful')
        return redirect(url_for("login"))

    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password required', 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE userName = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:                                  # Check password directly without hashing
            session['user'] = username
            flash('Login successful', 'success')
            return redirect(url_for("view_topics"))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user',None)
    flash('You have logged out.','info')
    return redirect(url_for("index"))

@app.route("/topics")
def view_topics():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM topic')
    topics = cursor.fetchall()
    conn.close()

    if not topics:
        messsage = "There are no topics available!."
        return render_template('topics.html', messsage=messsage)

    return render_template('topics.html', topics=topics)

    
@app.route("/topic/<int:topic_id>")
def topic(topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM topic WHERE topic_id= ?', (topic_id,))
    topic = cursor.fetchone()

    cursor.execute('SELECT * FROM claim WHERE topic = ? ORDER BY updateTime DESC', (topic_id,))
    claims = cursor.fetchall()
    conn.close()

    if topic is None:
        messsage = "There are no available topics rn!"
        return redirect(url_for('view_topics'))

    return render_template("topics.html", topic=topic, claims=claims)

@app.route('/new_topic', methods=['GET', 'POST'])
def new_topic():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description') 

        if not title:
            flash('Title is required!', 'error')
            return redirect(url_for('new_topic'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO topic (topicName, description) VALUES (?, ?)', (title, description))
        conn.commit()
        conn.close()

        flash('Topic created successfully!', 'success')
        return redirect(url_for('view_topics'))

    return render_template('new_topic.html')

@app.route('/claim/<int:claim_id>')
def claim(claim_id):
    conn = get_db_connection()
    claim = conn.execute('SELECT * FROM claim WHERE claimID = ?', (claim_id,)).fetchone()
    replies = conn.execute('SELECT * FROM replies WHERE replyTextID IN (SELECT reply FROM replyToClaim WHERE claim = ?)', 
                           (claim_id,)).fetchall() 
    conn.close()
    
    if not claim:
        flash('Claim not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('claim.html', claim=claim, replies=replies)

@app.route('/new_claim/<int:topic_id>', methods=['GET', 'POST'])
def new_claim(topic_id):

        conn = get_db_connection()
        cursor= conn.cursor()
        cursor.execute('SELECT * FROM topic WHERE topic_id = ?',(topic_id,))
        topic = cursor.fetchone()
        conn.close()

        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            username = session.get('user')

            conn = get_db_connection()
            cursor= conn.cursor()
            cursor.execute('SELECT * FROM user WHERE userName = ?',(username,))
            user = cursor.fetchone()
            user_id = user['userID'] if user else None


            if not title or not description:
                flash('Title and description required.')
                return redirect(url_for('new_claim', topic_id=topic_id))

            cursor.execute('INSERT INTO claim (text, topic, postingUser, creationTime, updateTime) VALUES (?, ?, ?, ?, ?)', (description, topic_id, user_id,int(datetime.now().timestamp()), int(datetime.now().timestamp())))
            conn.commit()
            conn.close()

            flash('Claim created successfully!')
            return redirect(url_for('topic', topic_id=topic_id))

        return render_template('new_claim.html', topic=topic, topic_id=topic_id)

@app.route('/new_reply/<int:claim_id>', methods=['GET','POST'])
def new_reply(claim_id):
    if request.method == 'POST':
        content = request.form['content']
        relation_type = request.form['relation_type']
        
        username = session.get('user')  
        conn = get_db_connection()
        cursor=conn.cursor()
        cursor.execute('SELECT * FROM user WHERE userName =?', (username,))
        user = cursor.fetchone()
        user_id = user['userID'] if user else None

        if not content or not relation_type:
            flash('Reply content and relation type are needed')
            return redirect(url_for('claim', claim_id=claim_id))
        
        cursor.execute('INSERT INTO replies (postingUser, creationTime,text) VALUES (?, ?, ?)', (user_id, int(datetime.now().timestamp()), content))
        reply_id = conn.lastrowid
        cursor.execute('INSERT INTO replyToClaim (reply, claim) VALUES (?, ?)', (reply_id, claim_id))

        conn.commit()
        conn.close()

        flash('Reply posted successfully!', 'success')
        return redirect(url_for('claim', claim_id=claim_id))

if __name__ == "__main__":
    app.run(debug=True)
