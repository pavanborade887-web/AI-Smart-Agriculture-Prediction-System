import { useLanguage } from './LanguageContext'

export default function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage()
  return (
    <label className="language-switcher">
      <span>{t('Language')}</span>
      <select aria-label={t('Language')} value={language} onChange={(event) => setLanguage(event.target.value as 'en' | 'mr' | 'hi')}>
        <option value="en">English</option>
        <option value="mr">मराठी</option>
        <option value="hi">हिंदी</option>
      </select>
    </label>
  )
}
