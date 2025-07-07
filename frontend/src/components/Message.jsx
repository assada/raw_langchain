import React from 'react';
import { CSS_CLASSES, MESSAGE_TYPES } from '../constants/constants.js';

export const Message = ({ message }) => {
    const { content, type, className = '' } = message;
    
    const isUser = type === MESSAGE_TYPES.USER;
    const baseClass = isUser 
        ? `${CSS_CLASSES.MESSAGE} ${CSS_CLASSES.USER_MESSAGE}`
        : `${CSS_CLASSES.MESSAGE} ${CSS_CLASSES.ASSISTANT_MESSAGE}`;
    
    const finalClassName = className ? `${baseClass} ${className}` : baseClass;
    
    return (
        <div className={finalClassName}>
            {content}
        </div>
    );
}; 