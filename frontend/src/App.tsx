import { Navigate, Route, Routes } from 'react-router-dom'
import type { ReactElement } from 'react'
import { useAuth } from './AuthContext'
import AuthPage from './pages/AuthPage'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Dashboard from './pages/Dashboard'
import FeaturePage from './pages/FeaturePage'
import DiseasePage from './pages/DiseasePage'
import ChatPage from './pages/ChatPage'
import ReportsPage from './pages/ReportsPage'
import AdminPage from './pages/AdminPage'
function Protected({ children }: { children: ReactElement }) { return useAuth().user ? children : <Navigate to="/login" replace /> }
export default function App() { return <Routes><Route path="/login" element={<AuthPage mode="login"/>}/><Route path="/register" element={<AuthPage mode="register"/>}/><Route path="/forgot-password" element={<ForgotPassword/>}/><Route path="/reset-password" element={<ResetPassword/>}/><Route path="/dashboard" element={<Protected><Dashboard/></Protected>}/><Route path="/tools/:feature" element={<Protected><FeaturePage/></Protected>}/><Route path="/disease" element={<Protected><DiseasePage/></Protected>}/><Route path="/assistant" element={<Protected><ChatPage/></Protected>}/><Route path="/reports" element={<Protected><ReportsPage/></Protected>}/><Route path="/admin" element={<Protected><AdminPage/></Protected>}/><Route path="*" element={<Navigate to="/dashboard" replace/>}/></Routes> }
