export default function ChatMessage({ role, text, avatar }) {
  const isUser = role === 'user'

  return (
    <div className={`flex items-start gap-4 ${isUser ? 'flex-row-reverse' : ''} animate-slideInLeft`}>
      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden border-2 shadow-md ${
        isUser 
          ? 'bg-gradient-to-br from-primary-fixed to-primary-fixed/70 border-primary/30' 
          : 'bg-gradient-to-br from-surface-container-lowest to-surface-container-low border-outline-variant/30'
      }`}>
        {isUser ? (
          <span className="material-symbols-outlined text-on-primary">person</span>
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
      <div className={`max-w-[85%] p-4 rounded-2xl shadow-md transition-all duration-200 hover:shadow-lg ${
        isUser
          ? 'bg-gradient-to-br from-primary-fixed to-primary-fixed/80 text-on-primary rounded-br-none border-2 border-primary/30'
          : 'bg-gradient-to-br from-[#F0F8F5] to-primary-fixed/5 text-on-surface rounded-bl-none border-2 border-primary/10 hover:border-primary/30'
      }`}>
        <p className="font-body-md whitespace-pre-wrap leading-relaxed">{text}</p>
      </div>
    </div>
  )
}
