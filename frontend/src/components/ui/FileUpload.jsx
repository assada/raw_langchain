import React, { useState, useRef } from 'react';

const FileUpload = ({ id, label, accept = [], placeholder = "Choose a file...", multiple = false }) => {
    const [dragOver, setDragOver] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    };

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    };

    const handleFiles = (files) => {
        const validFiles = files.filter(file => {
            if (accept.length === 0) return true;
            return accept.some(type => {
                if (type.startsWith('.')) {
                    return file.name.toLowerCase().endsWith(type.toLowerCase());
                }
                return file.type === type;
            });
        });

        if (multiple) {
            setSelectedFiles(prev => [...prev, ...validFiles]);
        } else {
            setSelectedFiles(validFiles.slice(0, 1));
        }
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;

        setUploading(true);
        
        try {
            const formData = new FormData();
            selectedFiles.forEach((file, index) => {
                formData.append(multiple ? `files[${index}]` : 'file', file);
            });

            const response = await fetch('/api/v1/files/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': 'Bearer ' + (localStorage.getItem('authToken') || 'eyJ1c2VyX2lkIjogIjE0MzdhZGUzNzM1OTQ4OGU5NWMwNzI3YTFjZGYxNzg2ZDI0ZWRjZTMiLCAiZW1haWwiOiAidGVzdEBnbWFpbC5jb20ifQ==')
                }
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Upload successful:', result);
                setSelectedFiles([]);
                if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                }
            } else {
                console.error('Upload failed:', response.statusText);
            }
        } catch (error) {
            console.error('Upload error:', error);
        } finally {
            setUploading(false);
        }
    };

    const removeFile = (index) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const acceptString = accept.join(',');

    return (
        <div className="file-upload-container">
            <div className="file-upload-header">
                <h3>{label}</h3>
            </div>
            
            <div 
                className={`file-upload-zone ${dragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={acceptString}
                    multiple={multiple}
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                />
                
                <div className="file-upload-content">
                    <div className="file-upload-icon">📁</div>
                    <p className="file-upload-text">
                        {placeholder}
                    </p>
                    <p className="file-upload-hint">
                        Drag and drop files here or click to select
                    </p>
                    {accept.length > 0 && (
                        <p className="file-upload-types">
                            Supported types: {accept.join(', ')}
                        </p>
                    )}
                </div>
            </div>

            {selectedFiles.length > 0 && (
                <div className="selected-files">
                    <h4>Selected files:</h4>
                    <ul>
                        {selectedFiles.map((file, index) => (
                            <li key={index} className="selected-file">
                                <span className="file-name">{file.name}</span>
                                <span className="file-size">({Math.round(file.size / 1024)} KB)</span>
                                <button 
                                    className="remove-file-btn"
                                    onClick={() => removeFile(index)}
                                    type="button"
                                >
                                    ×
                                </button>
                            </li>
                        ))}
                    </ul>
                    
                    <button 
                        className="upload-btn"
                        onClick={handleUpload}
                        disabled={uploading}
                    >
                        {uploading ? 'Uploading...' : 'Upload Files'}
                    </button>
                </div>
            )}
        </div>
    );
};

export default FileUpload; 