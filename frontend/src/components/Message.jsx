import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'
import { MessageActions } from './MessageActions.jsx';
import UIMessage from './UIMessage.jsx';
import { CSS_CLASSES, SENDER_TYPES, MESSAGE_SUBTYPES } from '../constants/constants.js';

export const Message = ({ message, showActions = true }) => {
    const { id, content, sender, messageType, className = '', traceId } = message;
    
    const isUser = sender === SENDER_TYPES.USER;
    const isAssistant = sender === SENDER_TYPES.ASSISTANT;
    const isCurrentAssistant = id === 'current-assistant';
    const isRegularMessage = messageType === MESSAGE_SUBTYPES.MESSAGE;
    const isUIMessage = messageType === MESSAGE_SUBTYPES.UI;
    
    const baseClass = isUser 
        ? `${CSS_CLASSES.MESSAGE} ${CSS_CLASSES.USER_MESSAGE}`
        : `${CSS_CLASSES.MESSAGE} ${CSS_CLASSES.ASSISTANT_MESSAGE}`;
    
    const finalClassName = className ? `${baseClass} ${className}` : baseClass;
    
    return (
        <div className={finalClassName}>
            {isUIMessage ? (
                <UIMessage message={content} />
            ) : isAssistant && isRegularMessage ? (
                <ReactMarkdown remarkPlugins={[[remarkGfm, {singleTilde: false}]]}>{content}</ReactMarkdown>
            ) : (
                content
            )}
            {isAssistant && !isCurrentAssistant && isRegularMessage && showActions && traceId && (
                <MessageActions content={content} messageId={id} traceId={traceId} />
            )}
        </div>
    );
}; 