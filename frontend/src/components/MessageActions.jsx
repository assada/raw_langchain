import React, { useState, useCallback } from 'react';
import { FiCopy, FiThumbsUp, FiThumbsDown } from 'react-icons/fi';
import { useSSE } from '../hooks/index.js';

export const MessageActions = ({ content, messageId, traceId }) => {
    const [copied, setCopied] = useState(false);
    const [rating, setRating] = useState(null);
    const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
    const { getUserId, getThreadId } = useSSE();

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }, [content]);

    const submitFeedback = useCallback(async (feedbackValue) => {
        if (!traceId || isSubmittingFeedback) return;
        
        setIsSubmittingFeedback(true);
        
        try {
            const authToken = localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogMTAzLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==';
            const userId = getUserId();
            const threadId = getThreadId();
            
            const response = await fetch(`/api/v1/chat/${userId}/thread/${threadId}/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                body: JSON.stringify({
                    feedback: feedbackValue,
                    trace_id: traceId
                })
            });
            
            if (response.ok) {
                console.log(`Feedback submitted successfully: ${feedbackValue} for trace ${traceId}`);
            } else {
                console.error('Failed to submit feedback:', response.statusText);
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
        } finally {
            setIsSubmittingFeedback(false);
        }
    }, [traceId, getUserId, getThreadId, isSubmittingFeedback]);

    const handleRating = useCallback(async (ratingValue) => {
        if (rating === ratingValue) return; // Don't submit if already rated with same value
        
        setRating(ratingValue);
        
        const feedbackValue = ratingValue === 'good' ? 1 : 0;
        await submitFeedback(feedbackValue);
    }, [rating, submitFeedback]);

    // Don't render if no trace_id
    if (!traceId) {
        return null;
    }

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
                disabled={isSubmittingFeedback}
            >
                <FiThumbsUp />
            </button>
            
            <button 
                className={`action-button rating-button ${rating === 'bad' ? 'active' : ''}`}
                onClick={() => handleRating('bad')}
                title="Bad response"
                disabled={isSubmittingFeedback}
            >
                <FiThumbsDown />
            </button>
        </div>
    );
}; 