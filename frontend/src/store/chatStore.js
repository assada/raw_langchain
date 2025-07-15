import { create } from 'zustand';
import { STATUSES, MESSAGES, SENDER_TYPES, MESSAGE_SUBTYPES, CSS_CLASSES } from '../constants/constants.js';

export const useChatStore = create((set, get) => ({
    messages: [],
    input: '',
    isLoading: false,
    isSending: false,
    connectionStatus: {
        status: STATUSES.DISCONNECTED,
        message: MESSAGES.READY
    },
    currentAssistantMessage: '',
    currentAssistantTraceId: null,
    
    setInput: (input) => set({ input }),
    
    setLoading: (isLoading) => set({ isLoading }),
    
    setSending: (isSending) => set({ isSending }),
    
    setConnectionStatus: (status, message) => 
        set({ connectionStatus: { status, message } }),
    
    setCurrentAssistantMessage: (message, traceId = null) => 
        set({ currentAssistantMessage: message, currentAssistantTraceId: traceId }),
    
    appendToCurrentAssistantMessage: (content) => 
        set((state) => ({ 
            currentAssistantMessage: state.currentAssistantMessage + content 
        })),
    
    addMessage: (content, sender = SENDER_TYPES.USER, messageType = MESSAGE_SUBTYPES.MESSAGE, className = '', traceId = null) => 
        set((state) => ({
            messages: [...state.messages, {
                id: Date.now() + Math.random(),
                content,
                sender,
                messageType,
                className,
                traceId,
                timestamp: new Date().toISOString()
            }]
        })),
    
    loadHistory: (historyMessages) => {
        const transformedMessages = historyMessages.map((msg, index) => {
            const baseId = Date.now() + index;
            
            switch (msg.type) {
                case 'human_message':
                    return {
                        id: baseId,
                        content: msg.content,
                        sender: SENDER_TYPES.USER,
                        messageType: MESSAGE_SUBTYPES.MESSAGE,
                        className: '',
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
                case 'ai_message':
                    return {
                        id: baseId,
                        content: msg.content,
                        sender: SENDER_TYPES.ASSISTANT,
                        messageType: MESSAGE_SUBTYPES.MESSAGE,
                        className: '',
                        traceId: msg.trace_id || null,
                        timestamp: new Date().toISOString()
                    };
                case 'tool_call':
                    return {
                        id: baseId,
                        content: `🔧 Tool call: ${msg.name}(${JSON.stringify(msg.args)})`,
                        sender: SENDER_TYPES.ASSISTANT,
                        messageType: MESSAGE_SUBTYPES.TOOL_CALL,
                        className: CSS_CLASSES.TOOL_CALL,
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
                case 'tool_result':
                    return {
                        id: baseId,
                        content: `🔧 ${msg.tool_name}: ${msg.content}`,
                        sender: SENDER_TYPES.ASSISTANT,
                        messageType: MESSAGE_SUBTYPES.TOOL_RESULT,
                        className: CSS_CLASSES.TOOL_CALL,
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
                default:
                    return {
                        id: baseId,
                        content: msg.content || '',
                        sender: SENDER_TYPES.SYSTEM,
                        messageType: MESSAGE_SUBTYPES.MESSAGE,
                        className: '',
                        traceId: null,
                        timestamp: new Date().toISOString()
                    };
            }
        });
        
        set({ messages: transformedMessages });
    },
    
    finalizeAssistantMessage: () => {
        const { currentAssistantMessage, currentAssistantTraceId } = get();
        if (currentAssistantMessage) {
            set((state) => ({
                messages: [...state.messages, {
                    id: Date.now() + Math.random(),
                    content: currentAssistantMessage,
                    sender: SENDER_TYPES.ASSISTANT,
                    messageType: MESSAGE_SUBTYPES.MESSAGE,
                    className: '',
                    traceId: currentAssistantTraceId,
                    timestamp: new Date().toISOString()
                }],
                currentAssistantMessage: '',
                currentAssistantTraceId: null
            }));
        }
    },
    
    clearInput: () => set({ input: '' }),
    
    clearCurrentAssistantMessage: () => set({ currentAssistantMessage: '', currentAssistantTraceId: null }),
    
    reset: () => set({
        messages: [],
        input: '',
        isLoading: false,
        isSending: false,
        connectionStatus: {
            status: STATUSES.DISCONNECTED,
            message: MESSAGES.READY
        },
        currentAssistantMessage: '',
        currentAssistantTraceId: null
    })
})); 