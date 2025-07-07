import { create } from 'zustand';
import { STATUSES, MESSAGES, MESSAGE_TYPES } from '../constants/constants.js';

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
    
    setInput: (input) => set({ input }),
    
    setLoading: (isLoading) => set({ isLoading }),
    
    setSending: (isSending) => set({ isSending }),
    
    setConnectionStatus: (status, message) => 
        set({ connectionStatus: { status, message } }),
    
    setCurrentAssistantMessage: (message) => 
        set({ currentAssistantMessage: message }),
    
    appendToCurrentAssistantMessage: (content) => 
        set((state) => ({ 
            currentAssistantMessage: state.currentAssistantMessage + content 
        })),
    
    addMessage: (content, type = MESSAGE_TYPES.USER, className = '') => 
        set((state) => ({
            messages: [...state.messages, {
                id: Date.now() + Math.random(),
                content,
                type,
                className,
                timestamp: new Date().toISOString()
            }]
        })),
    
    finalizeAssistantMessage: () => {
        const { currentAssistantMessage } = get();
        if (currentAssistantMessage) {
            set((state) => ({
                messages: [...state.messages, {
                    id: Date.now() + Math.random(),
                    content: currentAssistantMessage,
                    type: MESSAGE_TYPES.ASSISTANT,
                    className: '',
                    timestamp: new Date().toISOString()
                }],
                currentAssistantMessage: ''
            }));
        }
    },
    
    clearInput: () => set({ input: '' }),
    
    clearCurrentAssistantMessage: () => set({ currentAssistantMessage: '' }),
    
    reset: () => set({
        messages: [],
        input: '',
        isLoading: false,
        isSending: false,
        connectionStatus: {
            status: STATUSES.DISCONNECTED,
            message: MESSAGES.READY
        },
        currentAssistantMessage: ''
    })
})); 