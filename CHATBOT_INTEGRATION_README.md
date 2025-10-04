# Chatbot Integration - TzApp

This document explains how to run the integrated chatbot system with the Angular frontend and Flask backend.

## Architecture

- **Frontend**: Angular application with chatbot page
- **Backend**: Flask API server handling OpenAI GPT requests
- **AI Model**: OpenAI GPT-3.5-turbo (configurable)

## Files Created/Modified

### Backend Files
- `chatbot_api.py` - Flask API server
- `requirements.txt` - Python dependencies
- `start_backend.sh` - Backend startup script

### Frontend Files
- `Frontend/TzApp-frontend/src/app/pages/chatbot-page/chatbot-page.ts` - Updated component
- `Frontend/TzApp-frontend/src/app/pages/chatbot-page/chatbot-page.html` - Updated template
- `Frontend/TzApp-frontend/src/app/pages/chatbot-page/chatbot-page.scss` - Updated styles
- `Frontend/TzApp-frontend/src/app/pipes/nl2br.pipe.ts` - Custom pipe for line breaks
- `Frontend/TzApp-frontend/src/app/services/user-profile.service.ts` - User profile management
- `Frontend/TzApp-frontend/src/app/services/chat.service.ts` - Chat persistence management

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to the project root
cd /home/luca/Tzapp

# Install Python dependencies
pip install -r requirements.txt

# Start the Flask backend server
./start_backend.sh
# OR manually:
python chatbot_api.py
```

The backend will start on `http://localhost:5000`

### 2. Frontend Setup

```bash
# Navigate to the Angular frontend directory
cd /home/luca/Tzapp/Frontend/TzApp-frontend

# Install dependencies (if not already done)
npm install

# Start the Angular development server
ng serve
```

The frontend will start on `http://localhost:4200`

## Features

### Chatbot Functionality
- **Real-time messaging** with OpenAI GPT-3.5-turbo
- **Session management** with unique session IDs
- **Conversation history** maintained per session
- **Chat persistence** - save and load conversations
- **Typing indicators** while waiting for responses
- **Error handling** with user-friendly messages
- **Clear chat** functionality to start new conversations
- **Saved chats sidebar** for easy access to previous conversations

### UI Features
- **Responsive design** matching the existing TzApp theme
- **Message bubbles** for user and assistant messages with proper text wrapping
- **User avatar** with selected goat photo from user profile
- **Auto-scroll** to latest messages
- **Loading states** with animated typing indicator
- **Enter key** to send messages
- **Send button** with disabled state during loading
- **Custom scrollbar** styling
- **Text justification** and proper line breaks for better readability

### Backend API Endpoints

- `POST /api/chat` - Send a message and get AI response
- `POST /api/chat/clear` - Clear conversation history
- `POST /api/chat/save` - Save current chat with title
- `GET /api/chat/load/<chat_id>` - Load a saved chat
- `GET /api/chat/list` - Get list of all saved chats
- `DELETE /api/chat/delete/<chat_id>` - Delete a saved chat
- `PUT /api/chat/update/<chat_id>` - Update chat title
- `GET /health` - Health check endpoint

## Configuration

### OpenAI API Key
The API key is currently hardcoded in `chatbot_api.py`. For production, consider:
- Using environment variables
- Storing in a secure configuration file
- Using a secrets management service

### Model Configuration
Currently using `gpt-3.5-turbo`. To change:
1. Edit the `model` parameter in `chatbot_api.py`
2. Update the API key if using a different model

### CORS Configuration
CORS is enabled for all origins. For production, restrict to your domain:
```python
CORS(app, origins=["http://localhost:4200", "https://yourdomain.com"])
```

## Usage

1. Start both backend and frontend servers
2. Navigate to the chatbot page in your Angular app
3. Type a message and press Enter or click Send
4. The AI assistant (Tzappu) will respond with travel and accommodation recommendations
5. Use "Save Chat" to save your conversation with a custom title
6. Access saved chats from the sidebar on the right
7. Click on any saved chat to load and continue that conversation
8. Use "Clear Chat" to clear the current conversation
9. Delete saved chats by clicking the × button when hovering over them

## Troubleshooting

### Backend Issues
- Ensure Python dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is available
- Verify OpenAI API key is valid

### Frontend Issues
- Ensure Angular dependencies are installed: `npm install`
- Check if port 4200 is available
- Verify backend is running on port 5000

### CORS Issues
- Ensure Flask-CORS is installed
- Check browser console for CORS errors
- Verify backend is running and accessible

## Security Notes

- The OpenAI API key is exposed in the code - move to environment variables for production
- Consider rate limiting for the API endpoints
- Implement proper authentication if needed
- Validate and sanitize user inputs

## Recent Updates

### Chat Persistence Feature
- **Save conversations**: Users can now save their chat conversations with custom titles
- **Load saved chats**: Access and continue previous conversations from a sidebar
- **Delete chats**: Remove unwanted saved conversations
- **Chat management**: Full CRUD operations for chat persistence
- **English interface**: All UI elements are in English for international accessibility

### Text Wrapping & User Avatar Fixes
- **Fixed text wrapping**: User messages now properly wrap and justify text instead of staying on one line
- **Dynamic goat avatar**: User messages now display the selected goat photo from the user profile instead of a generic "U" avatar
- **Improved styling**: Added better line spacing, word wrapping, and text justification for both user and assistant messages
- **User profile service**: Created a service to manage user profile data including goat image selection

### User Profile Service
The new `UserProfileService` provides:
- Default user profile creation
- Goat image selection from available options
- Profile persistence in localStorage
- Observable profile updates for real-time UI updates

### Chat Service
The new `ChatService` provides:
- Save current conversations with custom titles
- Load previously saved chats
- Delete unwanted conversations
- List all saved chats with metadata
- Real-time updates for chat management

## Future Enhancements

- Add user authentication
- Implement conversation persistence in database
- Add file upload support for travel documents
- Implement voice input/output
- Add conversation export functionality
- Implement rate limiting and usage tracking
- Add goat selection UI in profile page
- Implement user name customization
