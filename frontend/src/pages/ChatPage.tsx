import { FormEvent, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FaPaperclip, FaTimes } from 'react-icons/fa'
import { agricultureApi } from '../api'
import { useLanguage } from '../LanguageContext'
import '../feature.css'

type Message = { role: string; content: string; attachment?: string | null }

const ACCEPTED_FILES = '.txt,.md,.csv,.pdf,.docx,.xlsx'
const MAX_FILE_BYTES = 10 * 1024 * 1024

export default function ChatPage() {
  const { language, t } = useLanguage()
  const [messages, setMessages] = useState<Message[]>([])
  const [message, setMessage] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    agricultureApi.history().then((response) => setMessages(response.data)).catch(() => setMessages([]))
  }, [])

  const chooseFile = (file?: File) => {
    setError('')
    if (!file) return
    if (file.size > MAX_FILE_BYTES) {
      setError(t('Files must be 10 MB or smaller.'))
      setSelectedFile(null)
      if (fileInput.current) fileInput.current.value = ''
      return
    }
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!extension || !['txt', 'md', 'csv', 'pdf', 'docx', 'xlsx'].includes(extension)) {
      setError(t('Choose a TXT, MD, CSV, PDF, DOCX, or XLSX file.'))
      setSelectedFile(null)
      if (fileInput.current) fileInput.current.value = ''
      return
    }
    setSelectedFile(file)
  }

  const removeFile = () => {
    setSelectedFile(null)
    if (fileInput.current) fileInput.current.value = ''
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const text = message.trim()
    const file = selectedFile
    if ((!text && !file) || loading) return

    setError('')
    setLoading(true)
    try {
      const response = file
        ? await agricultureApi.uploadChat(text, file, language)
        : await agricultureApi.chat(text, language)
      const userMessage = response.data.user_message ?? { role: 'user', content: text }
      setMessages((current) => [...current, userMessage, { role: 'assistant', content: response.data.answer }])
      setMessage('')
      removeFile()
    } catch (cause: any) {
      setError(t(cause.response?.data?.detail ?? 'Could not send your message. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="feature chat">
      <Link className="back" to="/dashboard">← {t('Overview')}</Link>
      <p className="eyebrow">{t('AGRICULTURE ASSISTANT')}</p>
      <h1>{t('Ask your farm question')}</h1>
      <div className="conversation" aria-live="polite">
        {messages.length ? messages.map((item, index) => (
          <div className={`bubble ${item.role}`} key={`${index}-${item.role}`}>
            {item.attachment && <span className="chat-attachment-label"><FaPaperclip /> {item.attachment}</span>}
            {item.content}
          </div>
        )) : <div className="result-empty">{t('Ask about crop selection, fertilizer, irrigation, plant health, weather, yields, or market timing. You can also attach a document for the assistant to read.')}</div>}
        {loading && <div className="bubble assistant">{selectedFile ? t('Reading your file…') : t('Thinking…')}</div>}
      </div>
      <form className="chat-form" onSubmit={submit}>
        <input
          className="chat-file-input"
          ref={fileInput}
          type="file"
          accept={ACCEPTED_FILES}
          onChange={(event) => chooseFile(event.target.files?.[0])}
          aria-label={t('Choose a file to attach')}
        />
        {selectedFile && (
          <div className="chat-selected-file">
            <span><FaPaperclip /> {selectedFile.name} <small>({(selectedFile.size / 1024).toFixed(0)} KB)</small></span>
            <button type="button" onClick={removeFile} aria-label={t('Remove attachment')}><FaTimes /></button>
          </div>
        )}
        {error && <p className="error chat-error" role="alert">{error}</p>}
        <div className="chat-input-row">
          <button className="chat-attach" type="button" onClick={() => fileInput.current?.click()} disabled={loading} aria-label={t('Attach a file')} title={t('Attach a file')}>
            <FaPaperclip />
          </button>
          <input value={message} onChange={(event) => setMessage(event.target.value)} placeholder={t(selectedFile ? 'Ask a question about this file (optional)' : 'How should I schedule irrigation this week?')} />
          <button disabled={loading || (!message.trim() && !selectedFile)}>{loading ? t('Reading…') : t('Send')}</button>
        </div>
        <p className="chat-help">{t('Attach TXT, MD, CSV, PDF, DOCX, or XLSX files up to 10 MB.')}</p>
      </form>
    </main>
  )
}
