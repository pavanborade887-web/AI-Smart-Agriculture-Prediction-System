import { FormEvent, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { agricultureApi } from '../api'
import { translateValue, useLanguage } from '../LanguageContext'
import '../feature.css'

type Field = [string, string, string]
type Config = { title: string; description: string; submit: string; fields: Field[]; run: (data: Record<string, unknown>) => Promise<any> }
type FertilizerProduct = { name: string; quantity_kg_per_hectare: number; purpose: string }
type FertilizerResult = {
  recommended_fertilizers: FertilizerProduct[]
  deficiency_analysis: { nitrogen: number; phosphorus: number; potassium: number }
  organic_alternatives: string[]
  ph_guidance: string
}
type CropPredictionResult = {
  best_crop: string
  confidence: number
  alternatives: { crop: string; suitability: number }[]
  expected_income_inr_per_hectare?: number
  expected_profit_inr_per_hectare?: number
  basis?: string
}
type WeatherResult = {
  location: string
  observed_at: string
  temperature: number
  humidity: number
  pressure: number
  wind_speed: number
  description: string
  forecast: { date: string; temperature: number; humidity: number; rainfall_mm: number; description: string }[]
  advice?: string[]
  provider?: string
  attribution_url?: string
}
const numeric = (name: string) => !['state', 'district', 'soil_type', 'crop', 'city', 'country_code'].includes(name)
const configs: Record<string, Config> = {
  crop: { title: 'Crop prediction', description: 'Match crop suitability to your soil nutrients, pH, rainfall, and climate.', submit: 'Find suitable crops', fields: [['state','State','Maharashtra'],['district','District','Pune'],['soil_type','Soil type','Loamy'],['nitrogen','Nitrogen (kg/ha)','90'],['phosphorus','Phosphorus (kg/ha)','40'],['potassium','Potassium (kg/ha)','40'],['temperature','Temperature (°C)','26'],['humidity','Humidity (%)','65'],['rainfall','Rainfall (mm)','800'],['ph','pH','6.5']], run: agricultureApi.crop },
  fertilizer: { title: 'Fertilizer recommendation', description: 'Get a simple fertilizer plan based on your crop and soil information.', submit: 'Get Fertilizer Recommendation', fields: [['crop','Crop','Maize'],['nitrogen','Nitrogen (kg/ha)','70'],['phosphorus','Phosphorus (kg/ha)','30'],['potassium','Potassium (kg/ha)','35'],['ph','pH','6.5'],['moisture','Moisture (%)','35']], run: agricultureApi.fertilizer },
  yield: { title: 'Yield prediction', description: 'Estimate production and income from field, weather, and input conditions.', submit: 'Estimate yield', fields: [['crop','Crop','Wheat'],['area_hectares','Area (hectares)','2'],['rainfall','Rainfall (mm)','650'],['temperature','Temperature (°C)','22'],['fertilizer_kg','Fertilizer applied (kg)','160'],['soil_type','Soil type','Loamy'],['historical_yield_tonnes_per_hectare','Historical yield (t/ha)','3.2']], run: agricultureApi.yield },
  soil: { title: 'Soil health analysis', description: 'Score the foundations of your next harvest and get practical improvements.', submit: 'Analyze soil health', fields: [['nitrogen','Nitrogen (kg/ha)','85'],['phosphorus','Phosphorus (kg/ha)','38'],['potassium','Potassium (kg/ha)','42'],['organic_carbon','Organic carbon (%)','0.7'],['moisture','Moisture (%)','32'],['ph','pH','6.6']], run: agricultureApi.soil },
  irrigation: { title: 'Smart irrigation', description: 'Balance measured moisture, heat stress, and forecast rainfall.', submit: 'Get irrigation plan', fields: [['crop','Crop','Maize'],['soil_moisture','Soil moisture (%)','24'],['temperature','Temperature (°C)','31'],['humidity','Humidity (%)','52'],['rainfall_forecast_mm','Forecast rain (mm)','0'],['area_hectares','Area (hectares)','1.5']], run: agricultureApi.irrigation },
  market: { title: 'Market price prediction', description: 'Use your verified recent prices to identify the strongest selling window.', submit: 'Forecast prices', fields: [['crop','Crop','Tomato'],['current_price','Current price (₹/quintal)','1800'],['historical_prices','Historical prices, comma-separated','1500,1600,1580,1700,1750,1800'],['days_ahead','Forecast days','7']], run: (data) => agricultureApi.market({ ...data, historical_prices: String(data.historical_prices).split(',').map(Number) }) },
  weather: { title: 'Weather analysis', description: 'Retrieve current conditions and a seven-day field-work forecast.', submit: 'Check weather', fields: [['city','City','Pune'],['country_code','Country code','IN']], run: agricultureApi.weather },
}

const cropChoices = [
  ['Maize', '🌽'], ['Rice', '🌾'], ['Wheat', '🌾'], ['Cotton', '☁️'], ['Chickpea', '🫘'], ['Sugarcane', '🎋'], ['Other', '🌱'],
]
const fertilizerFieldGuides: Record<string, { title: string; helper: string; example: string; unit?: string }> = {
  crop: { title: 'Select Your Crop', helper: 'Choose the crop you are growing.', example: '' },
  nitrogen: { title: 'Nitrogen (N)', helper: 'Enter the Nitrogen value from your Soil Test Report.', example: 'Example: 70 kg/ha', unit: 'kg/ha' },
  phosphorus: { title: 'Phosphorus (P)', helper: 'Enter the Phosphorus value from your Soil Test Report.', example: 'Example: 30 kg/ha', unit: 'kg/ha' },
  potassium: { title: 'Potassium (K)', helper: 'Enter the Potassium value from your Soil Test Report.', example: 'Example: 35 kg/ha', unit: 'kg/ha' },
  ph: { title: 'Soil pH', helper: 'Enter the pH value shown in your Soil Test Report.', example: 'Example: 6.5' },
  moisture: { title: 'Soil Moisture', helper: 'Enter the current moisture level of your soil.', example: 'Example: 35%', unit: '%' },
}

function FertilizerResultView({ result, values, t }: { result: FertilizerResult; values: Record<string, unknown>; t: (text: string, vars?: Record<string, string | number>) => string }) {
  const analysis = result.deficiency_analysis
  const nutrientRows = [
    ['Nitrogen needed', analysis?.nitrogen], ['Phosphorus needed', analysis?.phosphorus], ['Potassium needed', analysis?.potassium],
  ] as const
  return <div className="fert-result">
    <div className="fert-success"><span aria-hidden="true">✓</span><div><strong>{t('Recommendation ready')}</strong><small>{t('Use recent soil test values for a more accurate plan.')}</small></div></div>
    <section className="fert-summary"><h2>🌾 {t('Your Crop')}</h2><p>{t(String(values.crop ?? 'Maize'))} <span>{cropChoices.find(([crop]) => crop === values.crop)?.[1] ?? '🌱'}</span></p></section>
    <section className="fert-summary"><h2>🧪 {t('Soil Condition')}</h2>
      <div className="fert-nutrient-grid">{nutrientRows.map(([label, gap]) => <div className="fert-nutrient" key={label}>
        <strong>{t(label)}</strong><span className={gap > 0 ? 'fert-status-low' : 'fert-status-good'}>{gap > 0 ? t('Additional {amount} kg/ha', { amount: gap }) : `🟢 ${t('Adequate')}`}</span>
      </div>)}</div>
      <p className="fert-condition-line"><strong>{t('pH guidance')}:</strong> {t(result.ph_guidance)}</p>
      <p className="fert-condition-line"><strong>💧 {t('Moisture')}:</strong> {String(values.moisture)}%</p>
    </section>
    <section className="fert-summary"><h2>🌱 {t('Recommended Fertilizer')}</h2>
      {result.recommended_fertilizers?.map((product, index) => <div className="fert-product" key={`${product.name}-${index}`}>
        <strong>🌱 {t(product.name)}</strong><span>{product.quantity_kg_per_hectare > 0 ? `${product.quantity_kg_per_hectare} kg/ha` : t('No corrective mineral fertilizer')}</span><small>{t(product.purpose)}</small>
      </div>)}
    </section>
    {result.organic_alternatives?.length > 0 && <section className="fert-summary"><h2>🌿 {t('Organic Alternatives')}</h2><ul className="fert-organic-list">{result.organic_alternatives.map((item, index) => <li key={index}>{t(item)}</li>)}</ul></section>}
    <aside className="fert-important"><strong>{t('Important')}</strong><p>{t('Use the recommendation as guidance. For the most accurate fertilizer application, follow your Soil Test Report and consult a local agriculture expert.')}</p></aside>
  </div>
}

function CropPredictionResultView({ result, t, language }: { result: CropPredictionResult; t: (text: string) => string; language: string }) {
  const locale = language === 'mr' ? 'mr-IN' : language === 'hi' ? 'hi-IN' : 'en-IN'
  const money = (amount: number) => new Intl.NumberFormat(locale, { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
  return <div className="crop-result">
    <div className="crop-match-card">
      <span className="crop-match-icon" aria-hidden="true">🌱</span>
      <div><small>{t('Best match for your field')}</small><h2>{t(result.best_crop)}</h2></div>
      <strong className="crop-confidence">{Math.round(result.confidence * 100)}%<small>{t('Confidence')}</small></strong>
    </div>
    {result.alternatives?.length > 0 && <section className="crop-result-section"><h3>🌾 {t('Other suitable crops')}</h3>
      <div className="crop-alternatives">{result.alternatives.map((item, index) => <div className="crop-alternative" key={`${item.crop}-${index}`}><strong>{t(item.crop)}</strong><span>{item.suitability}% {t('suitability')}</span></div>)}</div>
    </section>}
    {(result.expected_income_inr_per_hectare !== undefined || result.expected_profit_inr_per_hectare !== undefined) && <section className="crop-result-section"><h3>💰 {t('Estimated field returns')}</h3>
      <div className="crop-returns">
        {result.expected_income_inr_per_hectare !== undefined && <div><small>{t('Estimated income/ha')}</small><strong>{money(result.expected_income_inr_per_hectare)}</strong></div>}
        {result.expected_profit_inr_per_hectare !== undefined && <div><small>{t('Estimated profit/ha')}</small><strong>{money(result.expected_profit_inr_per_hectare)}</strong></div>}
      </div>
    </section>}
    {result.basis && <p className="crop-result-basis"><strong>{t('How this was matched')}:</strong> {t(result.basis)}</p>}
    <p className="crop-result-note">{t('Crop suitability is an estimate based on the field details you entered. Confirm variety, season, and local conditions with an agriculture expert.')}</p>
  </div>
}

function WeatherResultView({ result, t, language }: { result: WeatherResult; t: (text: string) => string; language: string }) {
  const locale = language === 'mr' ? 'mr-IN' : language === 'hi' ? 'hi-IN' : 'en-IN'
  const date = (value: string) => new Intl.DateTimeFormat(locale, { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' }).format(new Date(`${value}T12:00:00Z`))
  return <div className="weather-result">
    <div className="weather-current-card">
      <div><small>{t('Current conditions')}</small><h2>{result.location}</h2><span>{t(result.description)}</span></div>
      <strong>{Math.round(result.temperature)}°<small>C</small></strong>
    </div>
    <div className="weather-stats">
      <div><span>💧 {t('Humidity')}</span><strong>{Math.round(result.humidity)}%</strong></div>
      <div><span>🌬️ {t('Wind')}</span><strong>{result.wind_speed} m/s</strong></div>
      <div><span>🧭 {t('Pressure')}</span><strong>{result.pressure} hPa</strong></div>
    </div>
    {result.advice?.length ? <section className="weather-advice"><h3>🌿 {t('Farm advice')}</h3><ul>{result.advice.map((item, index) => <li key={index}>{t(item)}</li>)}</ul></section> : null}
    {result.forecast?.length ? <section className="weather-forecast"><h3>📅 {t('7-day forecast')}</h3><div className="weather-forecast-list">{result.forecast.map(day => <div className="weather-day" key={day.date}>
      <strong>{date(day.date)}</strong><span>{t(day.description)}</span><b>{Math.round(day.temperature)}°C</b><small>💧 {Math.round(day.humidity)}% · {day.rainfall_mm} mm</small>
    </div>)}</div></section> : null}
    {result.attribution_url && <small className="weather-source">{t('Weather data by')} <a href={result.attribution_url} target="_blank" rel="noreferrer">{result.provider ?? 'Open-Meteo'}</a></small>}
  </div>
}

export default function FeaturePage() {
  const { t, language } = useLanguage()
  const { feature = '' } = useParams()
  const config = configs[feature]
  const initial = useMemo(() => Object.fromEntries(config?.fields.map(([key,,value]) => [key, value]) ?? []), [config])
  const [values, setValues] = useState<Record<string, unknown>>(initial)
  const [result, setResult] = useState<unknown>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [noSoilReport, setNoSoilReport] = useState(false)
  const [customCrop, setCustomCrop] = useState('')

  if (!config) return <main className="feature"><Link to="/dashboard">← {t('Overview')}</Link><h1>{t('Feature not found')}</h1></main>
  const isFertilizer = feature === 'fertilizer'
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (isFertilizer && values.crop === 'Other' && customCrop.trim().length < 2) { setError(t('Enter crop name')); return }
    setLoading(true); setError('')
    try {
      const payload = Object.fromEntries(Object.entries(values).map(([key,value]) => [key, numeric(key) ? Number(value) : value]))
      if (isFertilizer && values.crop === 'Other') payload.crop = customCrop.trim()
      const response = await config.run(payload)
      setResult(response.data.result ?? response.data)
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(t(typeof detail === 'string' ? detail : 'Unable to complete this analysis.'))
    } finally { setLoading(false) }
  }

  return <main className="feature">
    <Link className="back" to="/dashboard">← {t('Dashboard')}</Link>
    <p className="eyebrow">{t('FARM TOOLS')}</p>
    <h1>{t(config.title)}</h1>
    <p className="intro">{t(config.description)}</p>
    <div className={`feature-grid${isFertilizer ? ' fertilizer-grid' : ''}`}>
      <form className={`tool-form${isFertilizer ? ' fertilizer-form' : ''}`} onSubmit={submit}>
        {isFertilizer && <aside className="soil-report-help"><strong>📋 {t("Don't know these values?")}</strong><p>{t('You can find Nitrogen, Phosphorus, Potassium and pH values in your Soil Test Report.')}</p><small>{t('Recommended: Use a recent Soil Test Report for more accurate fertilizer recommendations.')}</small></aside>}
        {config.fields.map(([key,label,defaultValue]) => {
          if (isFertilizer) {
            const guide = fertilizerFieldGuides[key]
            return <label className="guided-field" key={key}>
              <span className="guided-field-title">{key === 'crop' ? '🌾 ' : key === 'ph' ? '🧪 ' : key === 'moisture' ? '💧 ' : '🌱 '}{t(guide.title)}</span>
              <small>{t(guide.helper)}</small>
              {key === 'crop' ? <>
                <select aria-label={t(guide.title)} value={String(values[key] ?? defaultValue)} onChange={event => { setValues({ ...values, [key]: event.target.value }); setResult(null); setError('') }}>
                  {cropChoices.map(([crop, icon]) => <option key={crop} value={crop}>{icon} {t(crop === 'Other' ? 'Other (enter manually)' : crop)}</option>)}
                </select>
                {values.crop === 'Other' && <input aria-label={t('Enter crop name')} type="text" maxLength={80} minLength={2} required value={customCrop} placeholder={t('Enter crop name')} onChange={event => { setCustomCrop(event.target.value); setResult(null) }} />}
              </> : <div className="fert-input-wrap">
                <input aria-label={t(guide.title)} type="number" min={key === 'ph' ? 0 : 0} max={key === 'ph' ? 14 : key === 'moisture' ? 100 : key === 'phosphorus' ? 200 : 300} step="any" required value={String(values[key] ?? '')} placeholder={t(guide.example)} onChange={event => { setValues({ ...values, [key]: event.target.value }); setResult(null) }} />
                {guide.unit && <span aria-hidden="true">{guide.unit}</span>}
                {key === 'ph' && <span className="ph-tooltip" tabIndex={0} aria-label={t('pH shows whether your soil is acidic or alkaline.')} title={t('pH shows whether your soil is acidic or alkaline.')}>ⓘ</span>}
              </div>}
            </label>
          }
          return <label key={key}>{t(label)}<input value={String(values[key] ?? '')} onChange={event => setValues({ ...values, [key]: event.target.value })} required /></label>
        })}
        {isFertilizer && <div className="no-report-option"><label><input type="checkbox" checked={noSoilReport} onChange={event => setNoSoilReport(event.target.checked)} /><span>{t("I don't have a Soil Test Report")}</span></label>{noSoilReport && <p role="status">{t("That's okay! You can still continue, but recommendations may be less accurate. For better results, get your soil tested.")} {t('The shown numbers are starting examples; replace them with your best estimates where possible.')}</p>}</div>}
        <button className={isFertilizer ? 'fert-submit' : ''} disabled={loading}>{loading ? t('Analyzing…') : isFertilizer ? `🌱 ${t(config.submit)}` : t(config.submit)}</button>
        {error && <p className="error" role="alert">{error}</p>}
      </form>
      <article className={`result-panel${isFertilizer ? ' fertilizer-result-panel' : feature === 'crop' ? ' crop-result-panel' : feature === 'weather' ? ' weather-result-panel' : ''}`}>
        <p className="eyebrow">{t('RESULT')}</p>
        {feature === 'weather' && result ? <WeatherResultView result={result as WeatherResult} t={t} language={language} /> : feature === 'crop' && result ? <CropPredictionResultView result={{
          ...(result as CropPredictionResult),
          best_crop: t((result as CropPredictionResult).best_crop),
          alternatives: (result as CropPredictionResult).alternatives?.map(item => ({ ...item, crop: t(item.crop) })),
          basis: (result as CropPredictionResult).basis ? t((result as CropPredictionResult).basis!) : undefined,
        }} t={t} language={language} /> : isFertilizer && result ? <FertilizerResultView result={{
          ...(result as FertilizerResult),
          recommended_fertilizers: (result as FertilizerResult).recommended_fertilizers?.map(product => ({ ...product, name: t(product.name), purpose: t(product.purpose) })),
          organic_alternatives: (result as FertilizerResult).organic_alternatives?.map(item => t(item)),
          ph_guidance: t((result as FertilizerResult).ph_guidance),
        }} values={{ ...values, crop: values.crop === 'Other' ? customCrop.trim() : values.crop }} t={t} /> : result ? <pre>{JSON.stringify(translateValue(result, t), null, 2)}</pre> : <div className="result-empty">{isFertilizer ? <><strong>🌱 {t('Your fertilizer recommendation will appear here.')}</strong><p>{t("Fill in your crop and soil information, then click 'Get Fertilizer Recommendation'.")}</p></> : feature === 'weather' ? t('Weather forecast will appear here after you check a city.') : t('Enter your field information for a transparent, saved recommendation.')}</div>}
      </article>
    </div>
  </main>
}
