import React from 'react';
import { CSS_CLASSES } from '../constants/constants.js';

export const ConnectionStatus = ({ status, message }) => (
    <div className={`${CSS_CLASSES.CONNECTION_STATUS} ${status}`}>
        {message}
    </div>
); 