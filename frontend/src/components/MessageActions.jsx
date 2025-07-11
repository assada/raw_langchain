import React, { useState, useCallback } from 'react';
import { FiCopy, FiThumbsUp, FiThumbsDown } from 'react-icons/fi';

export const MessageActions = ({ content, messageId }) => {
    const [copied, setCopied] = useState(false);
    const [rating, setRating] = useState(null);

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }, [content]);

    const handleRating = useCallback((ratingValue) => {
        setRating(ratingValue);
        console.log(`Message ${messageId} rated: ${ratingValue}`);
    }, [messageId]);

    return (
        <div className="message-actions">
            <button 
                className="action-button copy-button"
                onClick={handleCopy}
                title="Copy"
            >
                <FiCopy />
                {copied && <span className="action-tooltip">Copied!</span>}
            </button>
            
            <button 
                className={`action-button rating-button ${rating === 'good' ? 'active' : ''}`}
                onClick={() => handleRating('good')}
                title="Good response"
            >
                <FiThumbsUp />
            </button>
            
            <button 
                className={`action-button rating-button ${rating === 'bad' ? 'active' : ''}`}
                onClick={() => handleRating('bad')}
                title="Bad response"
            >
                <FiThumbsDown />
            </button>
        </div>
    );
}; 