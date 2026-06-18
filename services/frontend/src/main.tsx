/**
 * @file main.tsx
 * @description Punto de entrada principal (Entry Point) de la aplicación React.
 * Inicializa el árbol de componentes inyectando los estilos globales.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
