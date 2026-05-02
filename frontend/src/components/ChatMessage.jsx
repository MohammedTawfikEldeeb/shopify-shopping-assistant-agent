export default function ChatMessage({ role, text, avatar }) {
  const isUser = role === 'user'

  return (
    <div className={`flex items-start gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden ${
        isUser ? 'bg-secondary-container' : 'bg-primary-container/10'
      }`}>
        {isUser ? (
          <span className="material-symbols-outlined text-secondary">person</span>
        ) : (
          <img
            src={avatar || '/assistant-avatar.png'}
            alt="Assistant"
            className="w-full h-full rounded-full object-cover"
            onError={(e) => {
              e.target.onerror = null
              e.target.src = 'https://ui-avatars.com/api/?name=AI&background=00654b&color=fff'
            }}
          />
        )}
      </div>
      <div className={`max-w-[85%] p-4 rounded-xl shadow-sm ${
        isUser
          ? 'bg-surface-container-high rounded-tr-none'
          : 'bg-[#F0F8F5] rounded-tl-none'
      }`}>
        <p className="font-body-md text-on-surface whitespace-pre-wrap">{text}</p>
      </div>
    </div>
  )
}
