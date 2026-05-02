import { useState } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-3 bg-surface-container-low rounded-xl border border-outline-variant/50 px-4 py-2 focus-within:border-primary-container focus-within:ring-1 focus-within:ring-primary-container transition-all"
    >
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type your request here..."
        disabled={disabled}
        className="flex-1 bg-transparent border-none focus:ring-0 text-body-md text-on-surface placeholder:text-secondary outline-none"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="bg-primary text-white p-2 rounded-lg hover:bg-primary-container transition-colors active:scale-95 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="material-symbols-outlined">send</span>
      </button>
    </form>
  )
}
