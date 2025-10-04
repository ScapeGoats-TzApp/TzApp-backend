from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for Angular frontend

# Set OpenAI API key
openai.api_key = "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"

# Store conversation history (in production, use a database)
conversation_history = {}
saved_chats = {}  # Store saved chat sessions

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get or create conversation history for this session
        if session_id not in conversation_history:
            conversation_history[session_id] = []
            # Add system prompt for new sessions
            system_prompt = """You are a friendly and empathetic assistant named Tzappu.
You are specialized in vacations, accomodations and booking recommendations. If the user tries to ask other related questions, you won't answer.
Please:
- Use a warm, conversational tone with natural language
- Express emotions and empathy when appropriate
- Use casual language, contractions, and conversational phrases
- Ask follow-up questions to better understand the user
- Include appropriate emojis occasionally to convey emotion
- Break up long responses into smaller paragraphs
- Admit when you're not sure about something
- Share personal-seeming observations and opinions
Remember to stay helpful while being relatable and human-like."""
            conversation_history[session_id].append({"role": "system", "content": system_prompt})
        
        # Add user message to conversation
        conversation_history[session_id].append({"role": "user", "content": user_message})
        
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Using gpt-3.5-turbo instead of gpt-5
            messages=conversation_history[session_id],
            temperature=0.7,
            presence_penalty=0.6,
            frequency_penalty=0.3,
            max_tokens=500,
        )
        
        assistant_reply = response["choices"][0]["message"]["content"]
        
        # Add assistant response to conversation
        conversation_history[session_id].append({"role": "assistant", "content": assistant_reply})
        
        return jsonify({
            'response': assistant_reply,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in conversation_history:
            del conversation_history[session_id]
        
        return jsonify({'message': 'Chat cleared successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/save', methods=['POST'])
def save_chat():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        chat_title = data.get('title', f'Chat {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        if session_id not in conversation_history:
            return jsonify({'error': 'No conversation found for this session'}), 404
        
        # Create saved chat entry
        saved_chat = {
            'id': str(uuid.uuid4()),
            'title': chat_title,
            'session_id': session_id,
            'messages': conversation_history[session_id].copy(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        saved_chats[saved_chat['id']] = saved_chat
        
        return jsonify({
            'chat_id': saved_chat['id'],
            'title': saved_chat['title'],
            'message': 'Chat saved successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/load/<chat_id>', methods=['GET'])
def load_chat(chat_id):
    try:
        if chat_id not in saved_chats:
            return jsonify({'error': 'Chat not found'}), 404
        
        saved_chat = saved_chats[chat_id]
        
        # Restore conversation history
        conversation_history[saved_chat['session_id']] = saved_chat['messages'].copy()
        
        return jsonify({
            'chat_id': saved_chat['id'],
            'title': saved_chat['title'],
            'session_id': saved_chat['session_id'],
            'messages': saved_chat['messages'],
            'created_at': saved_chat['created_at']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/list', methods=['GET'])
def list_saved_chats():
    try:
        chat_list = []
        for chat_id, chat_data in saved_chats.items():
            chat_list.append({
                'id': chat_id,
                'title': chat_data['title'],
                'created_at': chat_data['created_at'],
                'updated_at': chat_data['updated_at'],
                'message_count': len([msg for msg in chat_data['messages'] if msg['role'] != 'system'])
            })
        
        # Sort by updated_at descending (most recent first)
        chat_list.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return jsonify({'chats': chat_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/delete/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    try:
        if chat_id not in saved_chats:
            return jsonify({'error': 'Chat not found'}), 404
        
        del saved_chats[chat_id]
        return jsonify({'message': 'Chat deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/update/<chat_id>', methods=['PUT'])
def update_chat(chat_id):
    try:
        data = request.get_json()
        new_title = data.get('title')
        
        if chat_id not in saved_chats:
            return jsonify({'error': 'Chat not found'}), 404
        
        if new_title:
            saved_chats[chat_id]['title'] = new_title
            saved_chats[chat_id]['updated_at'] = datetime.now().isoformat()
        
        return jsonify({
            'chat_id': chat_id,
            'title': saved_chats[chat_id]['title'],
            'message': 'Chat updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
