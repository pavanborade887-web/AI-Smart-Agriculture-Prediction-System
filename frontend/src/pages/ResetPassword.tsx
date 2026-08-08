import { FormEvent, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../api'

export default function ResetPassword() {
  const [params] = useSearchParams(), navigate = useNavigate()
  const [password, setPassword] = useState(''), [confirm, setConfirm] = useState(''), [error, setError] = useState(''), [pending, setPending] = useState(false)
  const token = params.get('token') ?? ''
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    if (!token) return setError('This password reset link is incomplete.')
    if (password !== confirm) return setError('Passwords do not match.')
    setPending(true)
    try { await authApi.reset(token, password); navigate('/login', { state: { reset: true } }) }
    catch (err: any) { setError(err.response?.data?.detail ?? 'This link has expired or is invalid.') }
    finally { setPending(false) }
  }
  return <main className="auth-shell"><section className="brand"><p className="eyebrow">ACCOUNT RECOVERY</p><h1>Create a new<br/><i>password.</i></h1></section><section className="auth-card"><h2>Set new password</h2><p className="sub">Use at least 8 characters and keep it somewhere safe.</p><form onSubmit={submit}><label>New password<input required minLength={8} type="password" value={password} onChange={e => setPassword(e.target.value)} /></label><label>Confirm password<input required minLength={8} type="password" value={confirm} onChange={e => setConfirm(e.target.value)} /></label>{error && <p className="error">{error}</p>}<button disabled={pending}>{pending ? 'Saving…' : 'Update password'}</button></form><p className="switch"><Link to="/login">Back to sign in</Link></p></section></main>
}
