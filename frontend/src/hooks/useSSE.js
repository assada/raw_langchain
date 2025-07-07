import { useRef, useCallback } from 'react';
import { SSE } from 'sse.js';
import { useChatStore } from '../store/index.js';
import { STATUSES, MESSAGES, MESSAGE_TYPES, CSS_CLASSES } from '../constants/constants.js';

export const useSSE = () => {
    const sseRef = useRef(null);
    const {
        setConnectionStatus,
        setLoading,
        setSending,
        appendToCurrentAssistantMessage,
        addMessage,
        finalizeAssistantMessage,
        clearCurrentAssistantMessage
    } = useChatStore();

    const parseEventData = useCallback((e) => {
        try {
            return JSON.parse(e.data);
        } catch (parseError) {
            console.error('Error parsing event data:', parseError);
            return null;
        }
    }, []);

    const extractErrorMessage = useCallback((e) => {
        if (!e.data) return MESSAGES.RECEIVE_ERROR;
        
        try {
            const errorData = JSON.parse(e.data);
            return errorData.content || MESSAGES.RECEIVE_ERROR;
        } catch (parseError) {
            console.error('Error parsing error data:', parseError);
            return MESSAGES.RECEIVE_ERROR;
        }
    }, []);

    const handleSSEOpen = useCallback(() => {
        console.log('SSE connection opened');
        setConnectionStatus(STATUSES.CONNECTED, MESSAGES.CONNECTED);
        setLoading(false);
    }, [setConnectionStatus, setLoading]);

    const handleAIMessage = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        console.log('AI Message:', data);
        
        if (data.content) {
            appendToCurrentAssistantMessage(data.content);
        }
    }, [parseEventData, appendToCurrentAssistantMessage]);

    const handleToolCall = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        console.log('Tool Call:', data);
        
        const toolMessage = `🔧 Tool call: ${data.name}(${JSON.stringify(data.args)})`;
        addMessage(toolMessage, MESSAGE_TYPES.ASSISTANT, CSS_CLASSES.TOOL_CALL);
    }, [parseEventData, addMessage]);

    const handleToolResult = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        console.log('Tool Result:', data);
        
        const toolMessage = `🔧 ${data.tool_name}: ${data.content}`;
        addMessage(toolMessage, MESSAGE_TYPES.ASSISTANT, CSS_CLASSES.TOOL_CALL);
    }, [parseEventData, addMessage]);

    const handleSSEError = useCallback((e) => {
        console.error('SSE Error:', e);
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.CONNECTION_ERROR);
        
        const errorMessage = extractErrorMessage(e);
        addMessage(errorMessage, MESSAGE_TYPES.ERROR, CSS_CLASSES.ERROR);
        
        setLoading(false);
        setSending(false);
    }, [setConnectionStatus, extractErrorMessage, addMessage, setLoading, setSending]);

    const handleSSEAbort = useCallback(() => {
        console.log('SSE connection closed - resetting sending state');
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.DISCONNECTED);
        setSending(false);
        setLoading(false);
    }, [setConnectionStatus, setSending, setLoading]);

    const handleReadyStateChange = useCallback((e) => {
        const stateMessages = {
            0: [STATUSES.CONNECTING, MESSAGES.CONNECTING],
            1: [STATUSES.CONNECTED, MESSAGES.CONNECTED],
            2: [STATUSES.DISCONNECTED, MESSAGES.DISCONNECTED]
        };

        const [status, message] = stateMessages[e.readyState] || [];
        if (status && message) {
            setConnectionStatus(status, message);
            if (e.readyState === 2) {
                setSending(false);
            }
        }
    }, [setConnectionStatus, setSending]);

    const handleStreamEnd = useCallback(() => {
        console.log('Stream ended - resetting states');
        
        finalizeAssistantMessage();
        setSending(false);
        setLoading(false);
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.READY);
        
        if (sseRef.current) {
            sseRef.current.close();
        }
    }, [finalizeAssistantMessage, setSending, setLoading, setConnectionStatus]);

    const setupSSEListeners = useCallback(() => {
        if (!sseRef.current) return;

        const handlers = {
            'open': handleSSEOpen,
            'ai_message': handleAIMessage,
            'tool_call': handleToolCall,
            'tool_result': handleToolResult,
            'error': handleSSEError,
            'abort': handleSSEAbort,
            'readystatechange': handleReadyStateChange,
            'stream_end': handleStreamEnd
        };

        Object.entries(handlers).forEach(([event, handler]) => {
            sseRef.current.addEventListener(event, handler);
        });
    }, [
        handleSSEOpen,
        handleAIMessage,
        handleToolCall,
        handleToolResult,
        handleSSEError,
        handleSSEAbort,
        handleReadyStateChange,
        handleStreamEnd
    ]);

    const sendMessage = useCallback(async (message) => {
        if (!message.trim()) return;

        if (sseRef.current) {
            sseRef.current.close();
        }

        setSending(true);
        setLoading(true);
        clearCurrentAssistantMessage();

        try {
            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogMTAzLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';
            sseRef.current = new SSE('/api/v1/chat/1/thread/1/stream', {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                payload: JSON.stringify({
                    message: message,
                    thread_id: 1
                }),
                autoReconnect: false,
                start: false
            });

            setupSSEListeners();
            sseRef.current.stream();

        } catch (error) {
            console.error('Error:', error);
            addMessage(MESSAGES.CREATE_ERROR, MESSAGE_TYPES.ERROR, CSS_CLASSES.ERROR);
            setLoading(false);
            setSending(false);
        }
    }, [
        setSending,
        setLoading,
        clearCurrentAssistantMessage,
        setupSSEListeners,
        addMessage
    ]);

    const closeConnection = useCallback(() => {
        if (sseRef.current) {
            sseRef.current.close();
            sseRef.current = null;
        }
    }, []);

    return {
        sendMessage,
        closeConnection
    };
}; 