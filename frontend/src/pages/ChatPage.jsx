import { useState, useRef, useEffect, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { v4 as uuidv4 } from 'uuid'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import ProductCard from '../components/ProductCard'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const INITIAL_MESSAGE = {
  role: 'assistant',
  text: "Hello! I'm your Personal Shopping Agent. Paste a Shopify store URL above and tell me what you're looking for. I'll curate the best products just for you.",
}

function getOrCreateUserId() {
  let userId = localStorage.getItem('shopify_assistant_user_id')
  if (!userId) {
    userId = uuidv4()
    localStorage.setItem('shopify_assistant_user_id', userId)
  }
  return userId
}

function getOrCreateSessionId() {
  let sessionId = localStorage.getItem('shopify_assistant_last_session_id')
  if (!sessionId) {
    sessionId = uuidv4()
  }
  return sessionId
}

export default function ChatPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const initialStoreUrl = location.state?.storeUrl || ''

  const [storeUrl, setStoreUrl] = useState(initialStoreUrl)
  const [storeName, setStoreName] = useState('Your Store')
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [userId] = useState(() => getOrCreateUserId())
  const [sessionId, setSessionId] = useState(() => getOrCreateSessionId())
  const [sessions, setSessions] = useState([])
  const [showStoreModal, setShowStoreModal] = useState(false)
  const [modalStoreUrl, setModalStoreUrl] = useState('')
  const [selectedSessionForIndex, setSelectedSessionForIndex] = useState(null)
  const [isLoadingLastSession, setIsLoadingLastSession] = useState(true)
  const chatEndRef = useRef(null)

  // Create session on backend when sessionId changes (only if store info is available)
  useEffect(() => {
    const createSession = async () => {
      // Don't create session yet if we're just about to index a store
      if (showStoreModal && !storeUrl) return
      
      try {
        await fetch(`${API_URL}/chat/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            session_id: sessionId,
            store_url: storeUrl || null,
            store_domain: storeName !== 'Your Store' ? storeName : null,
          }),
        })
      } catch (err) {
        console.error('Failed to create session:', err)
      }
    }
    createSession()
  }, [sessionId, userId, storeUrl, storeName, showStoreModal])

  // Load user's sessions
  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/chat/sessions?user_id=${userId}`)
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
      }
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }, [userId])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // Load messages for current session
  const loadSessionMessages = useCallback(async (sid) => {
    try {
      const res = await fetch(`${API_URL}/chat/sessions/${sid}/messages`)
      if (!res.ok) return
      const data = await res.json()
      if (data.length > 0) {
        const loaded = data.map((m) => ({
          role: m.role,
          text: m.content,
          products: m.products_json || undefined,
        }))
        setMessages(loaded)
        // Set latest products if any
        const lastAssistant = [...data].reverse().find((m) => m.role === 'assistant')
        if (lastAssistant?.products_json?.length) {
          setProducts(lastAssistant.products_json)
        }
      } else {
        setMessages([INITIAL_MESSAGE])
        setProducts([])
      }
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }, [])

  // Load last session on mount if it exists
  useEffect(() => {
    const loadLastSession = async () => {
      const lastSessionId = localStorage.getItem('shopify_assistant_last_session_id')
      if (!lastSessionId) {
        setIsLoadingLastSession(false)
        return
      }
      
      try {
        // Fetch the session details
        const res = await fetch(`${API_URL}/chat/sessions?user_id=${userId}`)
        if (res.ok) {
          const allSessions = await res.json()
          const lastSession = allSessions.find(s => s.session_id === lastSessionId)
          if (lastSession) {
            setSessionId(lastSessionId)
            setStoreUrl(lastSession.store_url || '')
            setStoreName(lastSession.store_domain || 'Your Store')
            await loadSessionMessages(lastSessionId)
          }
        }
      } catch (err) {
        console.error('Failed to load last session:', err)
      } finally {
        setIsLoadingLastSession(false)
      }
    }
    
    loadLastSession()
  }, [userId, loadSessionMessages])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleNewSession = () => {
    const newSessionId = uuidv4()
    setSessionId(newSessionId)
    setSelectedSessionForIndex(newSessionId)
    setShowStoreModal(true)
    setModalStoreUrl('')
  }

  const handleSwitchSession = (sid) => {
    setSessionId(sid)
    localStorage.setItem('shopify_assistant_last_session_id', sid)
    loadSessionMessages(sid)
  }

  const handleIndexAndSwitch = async () => {
    if (!modalStoreUrl.trim()) return
    setIngesting(true)
    try {
      const res = await fetch(`${API_URL}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ store: modalStoreUrl.trim() }),
      })
      if (!res.ok) throw new Error('Failed to index store')
      const data = await res.json()
      const storeDomain = data.store_domain || modalStoreUrl.trim()
      
      setStoreUrl(modalStoreUrl.trim())
      setStoreName(storeDomain)
      setShowStoreModal(false)
      setModalStoreUrl('')
      
      setMessages([
        {
          role: 'assistant',
          text: `Great! I've indexed **${storeDomain}**. I found ${data.total_products_received} products. What would you like to find?`,
        },
      ])
      setProducts([])
      
      // Create/update session with store info and store domain as the name
      await fetch(`${API_URL}/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          session_id: selectedSessionForIndex,
          store_url: modalStoreUrl.trim(),
          store_domain: storeDomain,
        }),
      })
      
      // Save session ID to localStorage for next page load
      localStorage.setItem('shopify_assistant_last_session_id', selectedSessionForIndex)
      
      // Reload sessions to show the updated session with new name
      loadSessions()
    } catch (err) {
      alert(`Error: ${err.message}`)
    } finally {
      setIngesting(false)
    }
  }

  const handleDeleteSession = async (e, sid) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this session?')) return
    try {
      const res = await fetch(`${API_URL}/chat/sessions/${sid}`, {
        method: 'DELETE',
      })
      if (!res.ok) throw new Error('Failed to delete session')
      setSessions((prev) => prev.filter((s) => s.session_id !== sid))
      if (sid === sessionId) {
        handleNewSession()
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  const handleIndexStore = async () => {
    if (!storeUrl.trim()) return
    setIngesting(true)
    try {
      const res = await fetch(`${API_URL}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ store: storeUrl.trim() }),
      })
      if (!res.ok) throw new Error('Failed to index store')
      const data = await res.json()
      setStoreName(data.store_domain || storeUrl.trim())
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Great! I've indexed **${data.store_domain}**. I found ${data.total_products_received} products. What would you like to find?`,
        },
      ])
      // Update session with store info
      await fetch(`${API_URL}/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          store_url: storeUrl.trim(),
          store_domain: data.store_domain,
        }),
      })
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Sorry, I couldn't index that store: ${err.message}` },
      ])
    } finally {
      setIngesting(false)
    }
  }

  const handleSend = async (text) => {
    setMessages((prev) => [...prev, { role: 'user', text }])
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: userId,
          session_id: sessionId,
        }),
      })
      if (!res.ok) throw new Error('Failed to get response')
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', text: data.response }])
      if (data.products && data.products.length > 0) {
        setProducts(data.products)
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Oops, something went wrong: ${err.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-white">
      <style>{`
        @keyframes slideInLeft {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        .animate-slideInLeft {
          animation: slideInLeft 0.5s ease-out forwards;
        }
        .animate-slideInRight {
          animation: slideInRight 0.5s ease-out forwards;
        }
        .animate-fadeIn {
          animation: fadeIn 0.6s ease-out forwards;
        }
      `}</style>

      {/* Fixed Left Sidebar Navigation (w-72) */}
      <aside className="fixed left-0 top-0 h-full w-72 flex flex-col bg-white border-r border-neutral-200 shadow-[20px_0_40px_-15px_rgba(0,0,0,0.08)] z-40 animate-slideInLeft">
        {/* Header */}
        <div className="p-6 border-b border-neutral-200">
          <button
            onClick={handleNewSession}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-primary-container text-white rounded-lg font-label-md active:scale-[0.97] transition-transform duration-150 ease-out hover:shadow-lg shadow-primary/20 mb-4"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Session
          </button>
          <p className="text-label-md font-bold text-neutral-400 uppercase tracking-wider">Sessions</p>
        </div>

        {/* Sessions List */}
        <nav className="flex-1 overflow-y-auto py-4">
          <div className="px-3">
            <p className="px-3 mb-2 text-[11px] font-bold text-neutral-400 uppercase tracking-wider">Sessions</p>
            <ul className="space-y-1">
              {sessions.length === 0 ? (
                <li className="px-3 py-2 text-body-sm text-neutral-400 text-center">No sessions yet</li>
              ) : (
                sessions.map((s) => (
                  <li
                    key={s.session_id}
                    onClick={() => handleSwitchSession(s.session_id)}
                    className="group flex items-center justify-between px-3 py-2 rounded-lg text-neutral-500 hover:bg-neutral-50 transition-all cursor-pointer"
                  >
                    <span className="text-body-sm truncate pr-2">{s.store_domain || s.store_url || 'New Session'}</span>
                    <button
                      onClick={(e) => handleDeleteSession(e, s.session_id)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-error transition-opacity"
                    >
                      <span className="material-symbols-outlined text-[16px]">delete</span>
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>
        </nav>
      </aside>

      {/* Main Content Area - Offset for fixed sidebar */}
      <main className="ml-72 flex w-full h-screen overflow-hidden">
        {/* Left: Chat Interface (50%) */}
        <section className="w-1/2 flex flex-col bg-white border-r border-neutral-200 animate-fadeIn">
          {/* Header/Status */}
          <div className="h-16 px-6 flex items-center justify-between border-b border-neutral-100">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary-container text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  smart_toy
                </span>
              </div>
              <div>
                <p className="text-label-md font-bold text-on-surface">Shopping Concierge AI</p>
                <p className="text-[11px] text-primary flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></span>
                  Online & Ready to Help
                </p>
              </div>
            </div>
            <button className="p-2 hover:bg-neutral-50 rounded-lg text-neutral-400 transition-colors">
              <span className="material-symbols-outlined">more_horiz</span>
            </button>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, idx) => (
              <div key={idx} style={{ animation: `slideInLeft 0.3s ease-out ${idx * 50}ms forwards`, opacity: 0 }}>
                {msg.role === 'assistant' ? (
                  <div className="flex gap-4 max-w-[90%]">
                    <div className="h-8 w-8 rounded-full bg-emerald-50 shrink-0 flex items-center justify-center border border-emerald-100">
                      <span className="material-symbols-outlined text-primary-container text-[18px]">auto_awesome</span>
                    </div>
                    <div className="bg-[#F0F8F5] p-4 rounded-2xl rounded-tl-none border border-emerald-50 shadow-sm max-w-[85%]">
                      <p className="text-body-md text-on-surface leading-relaxed">{msg.text}</p>
                      <span className="text-[10px] text-neutral-400 mt-2 block font-medium uppercase tracking-tighter">
                        Assistant • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-4 max-w-[90%] ml-auto flex-row-reverse">
                    <div className="h-8 w-8 rounded-full bg-neutral-900 shrink-0 flex items-center justify-center overflow-hidden">
                      <span className="material-symbols-outlined text-white text-[18px]">account_circle</span>
                    </div>
                    <div className="bg-white p-4 rounded-2xl rounded-tr-none border border-neutral-200 shadow-sm max-w-[85%]">
                      <p className="text-body-md text-on-surface leading-relaxed">{msg.text}</p>
                      <span className="text-[10px] text-neutral-400 mt-2 block font-medium uppercase tracking-tighter text-right">
                        You • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-4 max-w-[90%] animate-slideInLeft">
                <div className="h-8 w-8 rounded-full bg-emerald-50 shrink-0 flex items-center justify-center border border-emerald-100">
                  <span className="material-symbols-outlined text-primary-container text-[18px]">auto_awesome</span>
                </div>
                <div className="bg-[#F0F8F5] p-4 rounded-2xl rounded-tl-none border border-emerald-50 shadow-sm">
                  <div className="flex gap-2">
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-6 bg-white border-t border-neutral-100">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                const input = e.target.querySelector('textarea')
                if (input.value.trim()) {
                  handleSend(input.value.trim())
                  input.value = ''
                }
              }}
              className="flex items-end gap-3 bg-white border border-neutral-300 rounded-xl p-2.5 focus-within:border-primary-container focus-within:ring-1 focus-within:ring-primary-container transition-all shadow-sm"
            >
              <button type="button" className="p-2 hover:bg-neutral-50 rounded-lg text-neutral-400 transition-colors">
                <span className="material-symbols-outlined">attach_file</span>
              </button>
              <textarea
                placeholder="Ask me to find anything..."
                rows="1"
                disabled={loading}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    const value = e.currentTarget.value.trim()
                    if (value) {
                      handleSend(value)
                      e.currentTarget.value = ''
                    }
                  }
                }}
                className="flex-1 border-none focus:ring-0 resize-none py-2 px-1 text-body-md bg-transparent placeholder-neutral-400 outline-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading}
                className="h-10 w-10 bg-primary-container text-white rounded-lg flex items-center justify-center active:scale-[0.95] transition-transform shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined">send</span>
              </button>
            </form>
          </div>
        </section>

        {/* Right: Recommendations Grid (50%) */}
        <section className="w-1/2 flex flex-col bg-surface overflow-y-auto animate-slideInRight">
          <div className="p-8">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="font-h2 text-on-surface mb-1">Curated Recommendations</h2>
                <p className="text-body-sm text-secondary">
                  {products.length > 0
                    ? `Based on your recent request`
                    : 'Products will appear here'}
                </p>
              </div>
              {products.length > 0 && (
                <div className="flex gap-2">
                  <button className="p-2 bg-white border border-neutral-200 rounded-lg shadow-sm hover:bg-neutral-50 transition-colors">
                    <span className="material-symbols-outlined text-[20px]">tune</span>
                  </button>
                  <button className="p-2 bg-white border border-neutral-200 rounded-lg shadow-sm hover:bg-neutral-50 transition-colors">
                    <span className="material-symbols-outlined text-[20px]">grid_view</span>
                  </button>
                </div>
              )}
            </div>

            {products.length > 0 ? (
              <div className="grid grid-cols-2 gap-6">
                {/* Large Featured Card */}
                {products.length > 0 && (
                  <a
                    key={`featured-${products[0].id}`}
                    href={products[0].link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="col-span-2 group bg-white rounded-xl border border-neutral-200 overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer block"
                  >
                    <div className="relative h-72 overflow-hidden bg-neutral-100">
                      <img
                        src={products[0].image || 'https://via.placeholder.com/400x400'}
                        alt={products[0].title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                      <div className="absolute top-4 left-4 bg-primary-container text-white text-[10px] font-bold px-2 py-1 rounded tracking-widest uppercase">
                        Best Match
                      </div>
                    </div>
                    <div className="p-5 flex justify-between items-end">
                      <div>
                        <p className="text-[11px] text-primary-container font-bold uppercase tracking-widest mb-1">
                          {products[0].vendor || 'Brand'}
                        </p>
                        <h3 className="font-h3 text-on-surface mb-1">{products[0].title}</h3>
                        <p className="text-body-sm text-secondary line-clamp-1">{products[0].description || 'Premium product'}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-h3 font-bold text-on-surface">${products[0].price || '0.00'}</p>
                        <span className="mt-2 flex items-center justify-center text-primary-container group-hover:text-primary transition-colors text-2xl">
                          <span className="material-symbols-outlined">arrow_outward</span>
                        </span>
                      </div>
                    </div>
                  </a>
                )}

                {/* Regular Product Cards */}
                {products.slice(1).map((product, idx) => (
                  <a
                    key={product.id}
                    href={product.link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group bg-white rounded-xl border border-neutral-200 overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer block"
                    style={{ animation: `fadeIn 0.4s ease-out ${(idx + 1) * 100}ms forwards`, opacity: 0 }}
                  >
                    <div className="relative h-48 overflow-hidden bg-neutral-100">
                      <img
                        src={product.image || 'https://via.placeholder.com/400x300'}
                        alt={product.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    </div>
                    <div className="p-4">
                      <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-widest mb-1">
                        {product.vendor || 'Brand'}
                      </p>
                      <h3 className="text-label-md font-bold text-on-surface truncate">{product.title}</h3>
                      <div className="flex items-center justify-between mt-3">
                        <p className="text-body-md font-bold">${product.price || '0.00'}</p>
                        <span className="text-primary-container group-hover:text-primary transition-colors text-2xl">
                          <span className="material-symbols-outlined">arrow_outward</span>
                        </span>
                      </div>
                    </div>
                  </a>
                ))}

              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-24 text-secondary">
                <span className="material-symbols-outlined text-7xl mb-4 opacity-30 animate-pulse">shopping_bag</span>
                <p className="font-body-lg font-semibold">No products yet</p>
                <p className="text-body-sm mt-3 text-center opacity-75">Start a conversation to see curated products here</p>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Store URL Modal */}
      {showStoreModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 animate-fadeIn">
            <h2 className="text-h3 font-bold text-on-surface mb-2">Add Store URL</h2>
            <p className="text-body-sm text-secondary mb-6">Enter your Shopify store URL to index and start shopping</p>
            
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleIndexAndSwitch()
              }}
            >
              <div className="mb-6">
                <label className="block text-label-md text-on-surface font-semibold mb-2">Store URL</label>
                <input
                  type="url"
                  value={modalStoreUrl}
                  onChange={(e) => setModalStoreUrl(e.target.value)}
                  placeholder="https://your-store.myshopify.com"
                  className="w-full px-4 py-3 border-2 border-neutral-200 rounded-lg focus:border-primary-container focus:ring-2 focus:ring-primary-container/20 outline-none transition-all"
                  autoFocus
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowStoreModal(false)
                    setModalStoreUrl('')
                  }}
                  className="flex-1 px-4 py-3 border-2 border-neutral-200 text-on-surface rounded-lg font-label-md hover:bg-neutral-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={ingesting || !modalStoreUrl.trim()}
                  className="flex-1 px-4 py-3 bg-primary-container text-white rounded-lg font-label-md hover:shadow-lg transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {ingesting ? (
                    <>
                      <span className="material-symbols-outlined animate-spin">sync</span>
                      Indexing...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined">cloud_upload</span>
                      Index Store
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

