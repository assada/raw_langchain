import { useRef, useCallback } from 'react';
import { SSE } from 'sse.js';
import { useChatStore } from '../store/index.js';
import { STATUSES, MESSAGES, SENDER_TYPES, MESSAGE_SUBTYPES, CSS_CLASSES, THINKING_STATES } from '../constants/constants.js';

// TODO: Replace with actual API call to get user_id and thread_id
const USER_ID = '1437ade37359488e95c0727a1cdf1786d24edce3';
const THREAD_ID = 'edd5a53c-da04-4db4-84e0-a9f3592eef45';

export const useSSE = () => {
    const sseRef = useRef(null);
    const {
        setConnectionStatus,
        setLoading,
        setSending,
        appendToCurrentAssistantMessage,
        addMessage,
        finalizeAssistantMessage,
        clearCurrentAssistantMessage,
        setCurrentAssistantMessage,
        loadHistory,
        startThinkingProcess,
        setThinkingState,
        addThinkingEvent,
        completeThinkingProcess,
        clearThinkingProcess
    } = useChatStore();

    const loadChatHistory = useCallback(async () => {
        setLoading(true);
        
        try {
            if (sseRef.current) {
                sseRef.current.close();
            }

            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogMTAzLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';

            const historicalMessages = [];
            sseRef.current = new SSE(`/api/v1/chat/${USER_ID}/thread/${THREAD_ID}`, {
                headers: {
                    'Authorization': 'Bearer ' + authToken
                },
                autoReconnect: false,
                start: false
            });

            const handleHistoryMessage = (e) => {
                const data = parseEventData(e);
                if (!data) return;
                historicalMessages.push(data);
            };

            const handleHistoryOpen = () => {
                console.log('History SSE connection opened');
            };

            const handleHistoryError = (e) => {
                console.error('History SSE Error:', e);
                const errorMessage = extractErrorMessage(e);
                addMessage(errorMessage, SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);
                setLoading(false);
            };

            const handleHistoryEnd = () => {
                console.log('History loading completed');

                if (historicalMessages.length > 0) {
                    loadHistory(historicalMessages);
                }
                
                setLoading(false);
                if (sseRef.current) {
                    sseRef.current.close();
                    sseRef.current = null;
                }
            };

            sseRef.current.addEventListener('open', handleHistoryOpen);
            sseRef.current.addEventListener('ai_message', handleHistoryMessage);
            sseRef.current.addEventListener('human_message', handleHistoryMessage);
            sseRef.current.addEventListener('ui', handleHistoryMessage);
            sseRef.current.addEventListener('tool_call', handleHistoryMessage);
            sseRef.current.addEventListener('tool_result', handleHistoryMessage);
            sseRef.current.addEventListener('error', handleHistoryError);
            sseRef.current.addEventListener('stream_end', handleHistoryEnd);
            sseRef.current.addEventListener('readystatechange', (e) => {
                if (e.readyState === 2) {
                    setLoading(false);
                }
            });

            sseRef.current.stream();

        } catch (error) {
            console.error('Error loading chat history:', error);
            addMessage('Error loading chat history', SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);
            setLoading(false);
        }
    }, [setLoading, addMessage, loadHistory, parseEventData, extractErrorMessage]);

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
        
        if (data.content) {
            setCurrentAssistantMessage(data.content, data.trace_id);
        }
    }, [parseEventData, setCurrentAssistantMessage]);

    const handleToolCall = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        console.log('Tool Call:', data);
        
        addThinkingEvent('tool_call', data);
    }, [parseEventData, addThinkingEvent]);

    const handleToolResult = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        console.log('Tool Result:', data);
        
        addThinkingEvent('tool_result', data);
    }, [parseEventData, addThinkingEvent]);

    const handleToken = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;

        setThinkingState(THINKING_STATES.RESPONDING);
        
        if (data.content) {
            appendToCurrentAssistantMessage(data.content);
        }
    }, [parseEventData, appendToCurrentAssistantMessage, setThinkingState]);

    const handleUIMessage = useCallback((e) => {
        const data = parseEventData(e);
        if (!data) return;
        
        addMessage(data, SENDER_TYPES.ASSISTANT, MESSAGE_SUBTYPES.UI, CSS_CLASSES.UI_MESSAGE);
    }, [parseEventData, addMessage]);

    const handleSSEError = useCallback((e) => {
        console.error('SSE Error:', e);
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.CONNECTION_ERROR);
        
        const errorMessage = extractErrorMessage(e);
        addMessage(errorMessage, SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);
        
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
        
        completeThinkingProcess();
        finalizeAssistantMessage();
        setSending(false);
        setLoading(false);
        setConnectionStatus(STATUSES.DISCONNECTED, MESSAGES.READY);
        
        if (sseRef.current) {
            sseRef.current.close();
        }
    }, [completeThinkingProcess, finalizeAssistantMessage, setSending, setLoading, setConnectionStatus]);

    const setupSSEListeners = useCallback(() => {
        if (!sseRef.current) return;

        const handlers = {
            'open': handleSSEOpen,
            'ai_message': handleAIMessage,
            'tool_call': handleToolCall,
            'tool_result': handleToolResult,
            'token': handleToken,
            'ui': handleUIMessage,
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
        handleToken,
        handleUIMessage,
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
        startThinkingProcess();

        try {
            // TODO: Mocked data, replace with actual API call
            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogMTAzLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';
            sseRef.current = new SSE(`/api/v1/chat/${USER_ID}/thread/${THREAD_ID}/stream`, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                payload: JSON.stringify({
                    message: message,
                    // thread_id: 1
                }),
                autoReconnect: false,
                start: false
            });

            setupSSEListeners();
            sseRef.current.stream();

        } catch (error) {
            console.error('Error:', error);
            addMessage(MESSAGES.CREATE_ERROR, SENDER_TYPES.SYSTEM, MESSAGE_SUBTYPES.ERROR, CSS_CLASSES.ERROR);
            setLoading(false);
            setSending(false);
        }
    }, [
        setSending,
        setLoading,
        clearCurrentAssistantMessage,
        startThinkingProcess,
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
        closeConnection,
        loadChatHistory,
        getUserId: () => USER_ID,
        getThreadId: () => THREAD_ID
    };
}; 