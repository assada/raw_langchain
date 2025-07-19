export const STATUSES = {
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected'
};

export const MESSAGES = {
    READY: 'Ready',
    CONNECTING: 'Connecting...',
    CONNECTED: 'Connected',
    DISCONNECTED: 'Connection closed',
    ERROR: 'Error',
    THINKING: 'Thinking...',
    RESPONDING: 'Responding...',
    CONNECTION_ERROR: 'Connection error',
    RECEIVE_ERROR: 'Error receiving response',
    CREATE_ERROR: 'Error creating connection'
};

export const THINKING_STATES = {
    THINKING: 'thinking',
    RESPONDING: 'responding',
    COMPLETED: 'completed'
};

export const CSS_CLASSES = {
    MESSAGE: 'message',
    USER_MESSAGE: 'user-message',
    ASSISTANT_MESSAGE: 'assistant-message',
    TOOL_CALL: 'tool-call',
    LOADING: 'loading',
    ERROR: 'error',
    CONNECTION_STATUS: 'connection-status',
    UI_MESSAGE: 'ui-message'
};

export const SENDER_TYPES = {
    USER: 'user',
    ASSISTANT: 'assistant',
    SYSTEM: 'system'
};

export const MESSAGE_SUBTYPES = {
    MESSAGE: 'message',
    TOOL_CALL: 'tool_call',
    TOOL_RESULT: 'tool_result',
    ERROR: 'error',
    LOADING: 'loading',
    UI: 'ui'
}; 