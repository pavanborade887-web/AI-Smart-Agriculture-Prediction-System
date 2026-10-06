import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import Plot from 'react-plotly.js'
import { FaArrowRightFromBracket, FaBell, FaChartLine, FaCloudSun, FaDroplet, FaLeaf, FaSprayCan, FaWheatAwn } from 'react-icons/fa6'
import { dashboardApi, type DashboardSummary } from '../api'
import { useAuth } from '../AuthContext'
import { useLanguage } from '../LanguageContext'
import '../dashboard.css'

const names: Record<string, string> = { crop: 'Crop recommendation', fertilizer: 'Fertilizer plan', yield: 'Yield estimate', soil_health: 'Soil health' }
const output = (source: Record<string, unknown> | null, keys: string[]) => keys.map((key) => source?.[key]).find((value) => typeof value === 'string' || typeof value === 'number')

export default function Dashboard() {
  const { t, language } = useLanguage()
  const { user, logout } = useAuth()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    dashboardApi.summary().then(({ data }) => setSummary(data)).catch(() => setError('Unable to load your latest insights. Please refresh and try again.'))
  }, [])

  const crop = output(summary?.stats.latest_crop ?? null, ['crop', 'best_crop', 'prediction'])
  const soil = output(summary?.stats.soil_health ?? null, ['score', 'health_score'])
  const temp = output(summary?.weather ?? null, ['temp', 'temperature'])
  const dateLocale = language === 'mr' ? 'mr-IN' : 'en-IN'
  const day = (value: string) => new Intl.DateTimeFormat(dateLocale, { month: 'short', day: 'numeric' }).format(new Date(value))

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="logo"><FaLeaf /> AgriSense</div>
        <nav>
          <Link className="active" to="/dashboard"><FaChartLine /> {t('Overview')}</Link>
          <Link to="/tools/crop"><FaWheatAwn /> {t('Crop planning')}</Link>
          <Link to="/disease"><FaSprayCan /> {t('Plant care')}</Link>
          <Link to="/tools/irrigation"><FaDroplet /> {t('Water management')}</Link>
          <Link to="/tools/fertilizer"><FaLeaf /> {t('Fertilizer')}</Link>
          <Link to="/tools/weather"><FaCloudSun /> {t('Weather')}</Link>
          <Link to="/assistant"><FaBell /> {t('AI assistant')}</Link>
          <Link to="/reports"><FaChartLine /> {t('Reports')}</Link>
          {user?.role === 'admin' && <Link to="/admin"><FaChartLine /> {t('Admin panel')}</Link>}
        </nav>
        <div className="profile"><span>{user?.full_name[0]}</span><div><strong>{user?.full_name}</strong><small>{t(user?.role ?? 'farmer')}</small></div></div>
      </aside>
      <main className="dash-content">
        <header className="dash-header">
          <div><p className="eyebrow">{t('FARM INTELLIGENCE · TODAY')}</p><h1>{t('Good to see you, {name}.', { name: summary?.user_name?.split(' ')[0] ?? user?.full_name.split(' ')[0] ?? '' })}</h1></div>
          <div className="header-actions"><button className="notify" aria-label={t('Notifications')} title={t('Notifications')}><FaBell />{summary?.stats.unread_notifications ? <b>{summary.stats.unread_notifications}</b> : null}</button><button className="logout" onClick={logout}>{t('Sign out')} <FaArrowRightFromBracket /></button></div>
        </header>
        {error && <p className="error">{t(error)}</p>}
        <section className="stat-grid">
          <Metric icon={<FaCloudSun />} color="amber" label={t('Current weather')} value={temp !== undefined ? `${temp}°` : t('Not synced')} helper={temp !== undefined ? t('Latest weather reading') : t('Available in Module 6')} />
          <Metric icon={<FaWheatAwn />} color="green" label={t('Current crop')} value={crop ? String(crop) : t('No recommendation')} helper={crop ? t('Latest crop prediction') : t('Start a crop analysis')} />
          <Metric icon={<FaDroplet />} color="blue" label={t('Soil health')} value={soil !== undefined ? `${soil}/100` : t('Not assessed')} helper={soil !== undefined ? t('Latest soil analysis') : t('Analyze soil to begin')} />
          <Metric icon={<FaSprayCan />} color="rose" label={t('Disease alerts')} value={t(summary?.stats.disease_status ?? 'All clear')} helper={summary?.stats.disease_status ? t('Latest leaf scan') : t('No scans recorded')} />
        </section>
        <section className="analytics-grid">
          <article className="panel"><div className="heading"><div><p className="eyebrow">{t('ACTIVITY')}</p><h2>{t('Farm intelligence activity')}</h2></div><span className="pill">{t('Last 7 days')}</span></div>
            <Plot data={[{ x: summary?.timeline.map((item) => day(item.date)) ?? [], y: summary?.timeline.map((item) => item.count) ?? [], type: 'scatter', mode: 'lines+markers', line: { color: '#2d7954', width: 3 }, marker: { color: '#b7d95b', size: 8 }, fill: 'tozeroy', fillcolor: 'rgba(183,217,91,.18)' }]} layout={{ autosize: true, height: 230, margin: { l: 28, r: 8, t: 15, b: 30 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', xaxis: { fixedrange: true, showgrid: false }, yaxis: { fixedrange: true, rangemode: 'tozero', dtick: 1, gridcolor: '#e8eee5', zeroline: false }, showlegend: false }} config={{ displayModeBar: false, responsive: true }} />
          </article>
          <article className="panel"><div className="heading"><div><p className="eyebrow">{t('PRIORITIES')}</p><h2>{t('Latest alerts')}</h2></div><span className="pill">{summary?.notifications.length ?? 0}</span></div>
            <div className="alerts">{summary?.notifications.length ? summary.notifications.map((note) => <div className="alert" key={note.id}><i className={note.category} /><div><strong>{t(note.title)}</strong><p>{t(note.message)}</p></div></div>) : <Empty icon={<FaBell />} title={t('You’re all caught up')} text={t('Weather, disease, harvest, and market alerts will appear here.')} />}</div>
          </article>
        </section>
        <section className="panel recent"><div className="heading"><div><p className="eyebrow">{t('HISTORY')}</p><h2>{t('Recent recommendations')}</h2></div><span className="pill">{summary?.stats.total_predictions ?? 0} {t('total')}</span></div>
          {summary?.recent_predictions.length ? <div className="records">{summary.recent_predictions.map((item) => <div className="record" key={item.id}><span><FaLeaf /></span><div><strong>{t(names[item.type] ?? item.type)}</strong><p>{day(item.created_at)}</p></div><small>{item.confidence === null ? t('Saved result') : `${Math.round(item.confidence * 100)}% ${t('confidence')}`}</small></div>)}</div> : <Empty icon={<FaLeaf />} title={t('Your dashboard grows with every insight.')} text={t('Run a prediction to start building farm intelligence history.')} />}
        </section>
      </main>
    </div>
  )
}

function Metric({ icon, color, label, value, helper }: { icon: ReactNode; color: string; label: string; value: string; helper: string }) {
  return <motion.article className="metric" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}><span className={color}>{icon}</span><p>{label}</p><h2>{value}</h2><small>{helper}</small></motion.article>
}

function Empty({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return <div className="empty">{icon}<strong>{title}</strong><p>{text}</p></div>
}
