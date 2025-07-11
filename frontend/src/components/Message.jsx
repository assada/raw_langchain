import React from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageActions } from './MessageActions.jsx';
import { CSS_CLASSES, SENDER_TYPES, MESSAGE_SUBTYPES } from '../constants/constants.js';

export const Message = ({ message, showActions = true }) => {
    const { id, content, sender, messageType, className = '' } = message;
    
    const isUser = sender === SENDER_TYPES.USER;
    const isAssistant = sender === SENDER_TYPES.ASSISTANT;
    const isCurrentAssistant = id === 'current-assistant';
    const isRegularMessage = messageType === MESSAGE_SUBTYPES.MESSAGE;
    
    const baseClass = isUser 
        ? `${CSS_CLASSES.MESSAGE} ${CSS_CLASSES.USER_MESSAGE}`
        : `${CSS_CLASSES.MESSAGE} ${CSS_CLASSES.ASSISTANT_MESSAGE}`;
    
    const finalClassName = className ? `${baseClass} ${className}` : baseClass;
    
    return (
        <div className={finalClassName}>
            {isAssistant && isRegularMessage ? (
                <ReactMarkdown>{content}</ReactMarkdown>
            ) : (
                content
            )}
            {isAssistant && !isCurrentAssistant && isRegularMessage && showActions && (
                <MessageActions content={content} messageId={id} />
            )}
        </div>
    );
}; 