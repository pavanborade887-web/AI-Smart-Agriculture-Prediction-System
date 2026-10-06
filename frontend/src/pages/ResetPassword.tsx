import { FormEvent, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../api'
import { useLanguage } from '../LanguageContext'

export default function ResetPassword() {
  const { t } = useLanguage()
  const [params] = useSearchParams(), navigate = useNavigate()
  const [password, setPassword] = useState(''), [confirm, setConfirm] = useState(''), [error, setError] = useState(''), [pending, setPending] = useState(false)
  const token = params.get('token') ?? ''
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    if (!token) return setError(t('This password reset link is incomplete.'))
    if (password !== confirm) return setError(t('Passwords do not match.'))
    setPending(true)
    try { await authApi.reset(token, password); navigate('/login', { state: { reset: true } }) }
    catch (err: any) { setError(t(err.response?.data?.detail ?? 'This link has expired or is invalid.')) }
    finally { setPending(false) }
  }
  return <main className="auth-shell"><section className="brand"><p className="eyebrow">{t('ACCOUNT RECOVERY')}</p><h1>{t('Create a new')}<br/><i>{t('password.')}</i></h1></section><section className="auth-card"><h2>{t('Set new password')}</h2><p className="sub">{t('Use at least 8 characters and keep it somewhere safe.')}</p><form onSubmit={submit}><label>{t('New password')}<input required minLength={8} type="password" value={password} onChange={e => setPassword(e.target.value)} /></label><label>{t('Confirm password')}<input required minLength={8} type="password" value={confirm} onChange={e => setConfirm(e.target.value)} /></label>{error && <p className="error">{error}</p>}<button disabled={pending}>{pending ? t('Saving…') : t('Update password')}</button></form><p className="switch"><Link to="/login">{t('Back to sign in')}</Link></p></section></main>
}
