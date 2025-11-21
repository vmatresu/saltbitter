import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Profile } from './pages/Profile';
import { Matches } from './pages/Matches';
import { Messages } from './pages/Messages';
import { Settings } from './pages/Settings';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/signup',
    element: <Signup />,
  },
  {
    path: '/profile/edit',
    element: <Profile />,
  },
  {
    path: '/matches',
    element: <Matches />,
  },
  {
    path: '/messages',
    element: <Messages />,
  },
  {
    path: '/messages/:userId',
    element: <Messages />,
  },
  {
    path: '/settings',
    element: <Settings />,
  },
  {
    path: '/subscription',
    element: <Settings />, // For now, redirect to settings
  },
  {
    path: '/transparency',
    element: <Settings />, // For now, redirect to settings
  },
  {
    path: '/ai-companions',
    element: <Settings />, // For now, redirect to settings
  },
  {
    path: '*',
    element: <Navigate to="/login" replace />,
  },
]);

export default router;
