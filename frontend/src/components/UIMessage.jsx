import React from 'react';
import FileUpload from './ui/FileUpload.jsx';

const UI_COMPONENTS = {
    file_upload: FileUpload,
};

const UIMessage = ({ message }) => {
    const { component, id, params } = message;
    
    const Component = UI_COMPONENTS[component];
    
    if (!Component) {
        console.warn(`UI Component "${component}" not found`);
        return (
            <div className="ui-message error">
                <p>Unknown component: {component}</p>
            </div>
        );
    }
    
    return (
        <div className="ui-message">
            <Component 
                id={id}
                {...params}
            />
        </div>
    );
};

export default UIMessage; 