import { useState } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex items-center gap-3 bg-gradient-to-r from-surface-container-lowest to-surface-container-low rounded-2xl border-2 transition-all duration-300 px-5 py-3 ${
        isFocused 
          ? 'border-primary shadow-lg shadow-primary/20 bg-white' 
          : 'border-outline-variant/30 hover:border-primary/30'
      }`}
    >
      <span className={`material-symbols-outlined transition-colors duration-200 ${isFocused ? 'text-primary' : 'text-secondary'}`}>
        message
      </span>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder="Type your request here..."
        disabled={disabled}
        className="flex-1 bg-transparent border-none focus:ring-0 text-body-md text-on-surface placeholder:text-secondary/50 outline-none disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="bg-gradient-to-r from-primary to-primary-container text-white p-3 rounded-xl hover:shadow-lg hover:shadow-primary/30 hover:scale-110 transition-all duration-200 active:scale-95 flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 border-2 border-primary-fixed/30"
      >
        <span className="material-symbols-outlined text-lg">send</span>
      </button>
    </form>
  )
}
