import React from 'react';
import { createRoot } from 'react-dom/client';
import { ChatApp } from './components/index.js';
import './styles.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<ChatApp />); 