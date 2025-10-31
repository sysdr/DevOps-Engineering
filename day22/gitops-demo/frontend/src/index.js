import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2C3E50',
      dark: '#1A252F',
      light: '#34495E',
    },
    secondary: {
      main: '#16A085',
      dark: '#138D75',
      light: '#1ABC9C',
    },
    background: {
      default: '#F5F7FA',
      paper: '#FFFFFF',
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
