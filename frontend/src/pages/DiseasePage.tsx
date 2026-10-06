import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { agricultureApi } from '../api'
import { useLanguage } from '../LanguageContext'
import '../feature.css'

type DiseaseResult = {
  disease_name?: string
  confidence?: number
  symptoms?: string
  treatment?: string[] | string
  fertilizer_advice?: string
  organic_treatment?: string
  expected_recovery?: string
}

function AdviceList({ value }: { value?: string[] | string }) {
  if (!value) return null
  const items = Array.isArray(value) ? value : [value]
  return <ul className="diagnosis-list">{items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
}

export default function DiseasePage() {
  const { t } = useLanguage()
  const [file, setFile] = useState<File | null>(null)
  const [crop, setCrop] = useState('')
  const [result, setResult] = useState<DiseaseResult | null>(null)
  const [error, setError] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!file) { setError(t('Choose a leaf image first.')); return }
    try {
      const response = await agricultureApi.disease(file, crop)
      setResult(response.data)
      setError('')
    } catch (err: any) {
      setError(t(err.response?.data?.detail ?? 'Image analysis failed.'))
    }
  }

  const localized = result ? {
    ...result,
    disease_name: result.disease_name ? t(result.disease_name) : undefined,
    symptoms: result.symptoms ? t(result.symptoms) : undefined,
    treatment: Array.isArray(result.treatment) ? result.treatment.map(item => t(item)) : result.treatment ? t(result.treatment) : undefined,
    fertilizer_advice: result.fertilizer_advice ? t(result.fertilizer_advice) : undefined,
    organic_treatment: result.organic_treatment ? t(result.organic_treatment) : undefined,
    expected_recovery: result.expected_recovery ? t(result.expected_recovery) : undefined,
  } : null
  return <main className="feature">
    <Link className="back" to="/dashboard">← {t('Dashboard')}</Link>
    <p className="eyebrow">{t('PLANT HEALTH')}</p>
    <h1>{t('Disease detection')}</h1>
    <p className="intro">{t('Upload a clear close-up of one leaf in natural light. The analyzer measures visible stress patterns and provides safe next steps.')}</p>
    <div className="feature-grid">
      <form className="tool-form" onSubmit={submit}>
        <label>{t('Crop (optional)')}<input value={crop} onChange={event => setCrop(event.target.value)} placeholder={t('Tomato')} /></label>
        <label>{t('Leaf image')}<input type="file" accept="image/jpeg,image/png,image/webp" onChange={event => setFile(event.target.files?.[0] ?? null)} required /></label>
        <button>{t('Analyze leaf')}</button>
        {error && <p className="error">{error}</p>}
      </form>
      <article className="result-panel diagnosis-result">
        <p className="eyebrow">{t('DIAGNOSIS')}</p>
        {localized ? <>
          <h2>{localized.disease_name ?? t('Analysis complete')}</h2>
          {typeof localized.confidence === 'number' && <p className="diagnosis-confidence">{t('Confidence')}: {Math.round(localized.confidence * 100)}%</p>}
          {localized.symptoms && <section><h3>{t('What we noticed')}</h3><p>{localized.symptoms}</p></section>}
          {localized.treatment && <section><h3>{t('What to do')}</h3><AdviceList value={localized.treatment} /></section>}
          {localized.fertilizer_advice && <section className="diagnosis-fertilizer"><h3>{t('Fertilizer guidance')}</h3><p>{localized.fertilizer_advice}</p></section>}
          {localized.organic_treatment && <section><h3>{t('Organic care')}</h3><p>{localized.organic_treatment}</p></section>}
          {localized.expected_recovery && <section><h3>{t('Follow-up')}</h3><p>{localized.expected_recovery}</p></section>}
          <p className="diagnosis-note">{t('This is an image-based screening, not a laboratory diagnosis. Confirm serious or spreading symptoms with a local agricultural expert.')}</p>
        </> : <div className="result-empty">{t('Your result will include confidence, symptoms, treatment, organic care, and recovery guidance.')}</div>}
      </article>
    </div>
  </main>
}
