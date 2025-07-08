import React, { useEffect, useLayoutEffect, useRef, useCallback } from 'react';
import { useChatStore } from '../store/index.js';
import { useSSE } from '../hooks/index.js';
import { Message } from './Message.jsx';
import { ConnectionStatus } from './ConnectionStatus.jsx';
import { MESSAGES, MESSAGE_TYPES, CSS_CLASSES } from '../constants/constants.js';

export const ChatApp = () => {
    const {
        messages,
        input,
        isLoading,
        isSending,
        connectionStatus,
        currentAssistantMessage,
        setInput,
        addMessage,
        clearInput
    } = useChatStore();

    const { sendMessage, closeConnection } = useSSE();
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    useLayoutEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages.length, currentAssistantMessage]);

    useEffect(() => {
        inputRef.current?.focus();
        
        return () => {
            closeConnection();
        };
    }, [closeConnection]);

    const handleSendMessage = useCallback(async () => {
        if (!input.trim() || isSending) return;

        addMessage(input, MESSAGE_TYPES.USER);
        const messageToSend = input;
        clearInput();
        
        await sendMessage(messageToSend);
    }, [input, isSending, addMessage, clearInput, sendMessage]);

    const handleKeyPress = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    }, [handleSendMessage]);

    const handleInputChange = useCallback((e) => {
        setInput(e.target.value);
    }, [setInput]);

    return (
        <div className="chat-container">
            <h1>LangChain Chat Assistant</h1>
            
            <div className="chat-messages">
                {messages.map((message) => (
                    <Message
                        key={message.id}
                        message={message}
                    />
                ))}
                
                {currentAssistantMessage && (
                    <Message
                        message={{
                            id: 'current-assistant',
                            content: currentAssistantMessage,
                            type: MESSAGE_TYPES.ASSISTANT,
                            className: ''
                        }}
                    />
                )}
                
                {isLoading && (
                    <Message
                        message={{
                            id: 'loading',
                            content: MESSAGES.THINKING,
                            type: MESSAGE_TYPES.LOADING,
                            className: CSS_CLASSES.LOADING
                        }}
                    />
                )}
                
                <div ref={messagesEndRef} />
            </div>
            
            <div className="input-container">
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter your message..."
                    disabled={isSending}
                    className="chat-input"
                />
                <button
                    onClick={handleSendMessage}
                    disabled={isSending || !input.trim()}
                    className="send-button"
                >
                    {isSending ? 'Sending...' : 'Send'}
                </button>
            </div>
            
            <ConnectionStatus 
                status={connectionStatus.status} 
                message={connectionStatus.message} 
            />
        </div>
    );
}; 