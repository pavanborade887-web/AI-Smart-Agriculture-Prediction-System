import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FaArrowRight, FaLeaf } from 'react-icons/fa'
import { useAuth } from '../AuthContext'
import { useLanguage } from '../LanguageContext'

export default function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { t } = useLanguage()
  const register = mode === 'register'
  const auth = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setPending(true)
    try {
      if (register) await auth.register(name, email, password)
      else await auth.login(email, password)
      navigate('/dashboard')
    } catch (cause: any) {
      setError(t(cause.response?.data?.detail ?? 'Unable to authenticate. Please try again.'))
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="brand">
        <div className="brand-mark"><FaLeaf /></div>
        <p className="eyebrow">{t('SMART AGRICULTURE')}</p>
        <h1>{t('Grow with')}<br /><i>{t('confidence.')}</i></h1>
        <p>{t('Clear, AI-informed decisions for every season.')}</p>
      </section>
      <motion.section className="auth-card" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
        <h2>{t(register ? 'Create your account' : 'Welcome back')}</h2>
        <p className="sub">{t(register ? 'Start building a stronger harvest today.' : 'Sign in to your farm intelligence hub.')}</p>
        <form onSubmit={submit}>
          {register && <label>{t('Full name')}<input required minLength={2} value={name} onChange={(event) => setName(event.target.value)} placeholder={t('Your full name')} /></label>}
          <label>{t('Email address')}<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></label>
          <label>{t('Password')}<input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder={t('At least 8 characters')} /></label>
          {!register && <Link className="muted-link" to="/forgot-password">{t('Forgot password?')}</Link>}
          {error && <p className="error">{error}</p>}
          <button disabled={pending}>{pending ? t('Please wait…') : t(register ? 'Create account' : 'Sign in')} <FaArrowRight /></button>
        </form>
        <p className="switch">{t(register ? 'Already have an account?' : 'New to AgriSense?')} <Link to={register ? '/login' : '/register'}>{t(register ? 'Sign in' : 'Create account')}</Link></p>
      </motion.section>
    </main>
  )
}
