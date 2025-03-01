from transformers import pipeline
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Load NLP sentiment analysis model
try:
    sentiment_pipeline = pipeline("sentiment-analysis")
except Exception as e:
    print(f"Error loading sentiment analysis pipeline: {e}")
    exit()

# Flask app for API
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
db = SQLAlchemy(app)

# Database model for user data
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    conversation_history = db.Column(db.Text, nullable=True)
    mood_history = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)

def detect_emotion_from_text(text):
    try:
        sentiment = sentiment_pipeline(text)
        return sentiment[0]['label']
    except Exception as e:
        return f"Error detecting emotion from text: {e}"

def generate_chatbot_response(user_input, user_mood):
    try:
        # Simple response generation based on mood
        if user_mood == "POSITIVE":
            return "That sounds great! Keep up the positive energy!"
        elif user_mood == "NEGATIVE":
            return "I'm here for you. How can I help you feel better?"
        else:
            return "I understand. Let's talk about it."
    except Exception as e:
        return f"Error generating chatbot response: {e}"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get('message', '')
        user_id = data.get('user_id', '')

        # Detect user's mood from text
        user_mood = detect_emotion_from_text(user_input)

        # Generate chatbot response
        chatbot_response = generate_chatbot_response(user_input, user_mood)

        # Save conversation history
        user = User.query.filter_by(username=user_id).first()
        if user:
            if user.conversation_history:
                user.conversation_history += f"\nUser: {user_input}\nBot: {chatbot_response}"
            else:
                user.conversation_history = f"User: {user_input}\nBot: {chatbot_response}"
            db.session.commit()
        else:
            new_user = User(username=user_id, conversation_history=f"User: {user_input}\nBot: {chatbot_response}")
            db.session.add(new_user)
            db.session.commit()

        return jsonify({"response": chatbot_response, "detected_mood": user_mood})
    except Exception as e:
        return jsonify({"error": f"Error processing chat request: {e}"}), 500

@app.route('/set_goal', methods=['POST'])
def set_goal():
    try:
        data = request.json
        user_id = data.get('user_id', '')
        goal = data.get('goal', '')

        user = User.query.filter_by(username=user_id).first()
        if user:
            user.goals = goal
            db.session.commit()
        else:
            new_user = User(username=user_id, goals=goal)
            db.session.add(new_user)
            db.session.commit()

        return jsonify({"message": "Goal set successfully"})
    except Exception as e:
        return jsonify({"error": f"Error setting goal: {e}"}), 500

@app.route('/get_goal', methods=['GET'])
def get_goal():
    try:
        user_id = request.args.get('user_id', '')

        user = User.query.filter_by(username=user_id).first()
        if user:
            return jsonify({"goal": user.goals})
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error getting goal: {e}"}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        user_id = request.json.get('user_id', '')

        user = User.query.filter_by(username=user_id).first()
        if user:
            user.conversation_history = None
            db.session.commit()
            return jsonify({"message": "Conversation history cleared"})
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error clearing history: {e}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
