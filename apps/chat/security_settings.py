# Chat module security settings

# File upload security settings
CHAT_FILE_UPLOAD_SETTINGS = {
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
    "ALLOWED_EXTENSIONS": {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",  # Images
        ".pdf",
        ".doc",
        ".docx",
        ".txt",  # Documents
        ".mp3",
        ".wav",  # Audio
        ".mp4",
        ".avi",  # Video
    },
    "UPLOAD_PATH": "chat_media/",
    "SCAN_UPLOADED_FILES": True,  # Enable virus scanning if available
}

# WebSocket security settings
CHAT_WEBSOCKET_SETTINGS = {
    "RATE_LIMIT_MESSAGES_PER_MINUTE": 60,
    "MAX_MESSAGE_LENGTH": 5000,
    "REQUIRE_CONVERSATION_PARTICIPANT": True,
}

# Message validation settings
CHAT_MESSAGE_SETTINGS = {
    "MAX_TEXT_LENGTH": 5000,
    "ALLOWED_MESSAGE_TYPES": ["text", "image", "file", "audio", "video"],
    "REQUIRE_CONTENT": True,  # Either text or media must be provided
}
