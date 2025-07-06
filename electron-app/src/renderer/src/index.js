import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import FloatingApp from './FloatingApp';

// Determine which app to render based on the current URL
const isFloatingWindow = window.location.pathname.includes('floating') || 
                        window.location.search.includes('floating');

const root = ReactDOM.createRoot(
  document.getElementById(isFloatingWindow ? 'floating-root' : 'root')
);

if (isFloatingWindow) {
  root.render(
    <React.StrictMode>
      <FloatingApp />
    </React.StrictMode>
  );
} else {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
