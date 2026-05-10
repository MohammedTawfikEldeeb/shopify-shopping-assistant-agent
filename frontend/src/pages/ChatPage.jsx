import { useState, useRef, useEffect, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const INITIAL_MESSAGE = {
  role: 'assistant',
  text: "Hey there! What can I help you find today?",
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
    localStorage.setItem('shopify_assistant_last_session_id', sessionId)
  }
  return sessionId
}

function useTypewriter(text, speed = 12) {
  const [displayed, setDisplayed] = useState('')
  const indexRef = useRef(0)
  const textRef = useRef(text)

  useEffect(() => {
    textRef.current = text
    indexRef.current = 0
    setDisplayed('')
    if (!text) return

    const timer = setInterval(() => {
      indexRef.current += 1
      setDisplayed(textRef.current.slice(0, indexRef.current))
      if (indexRef.current >= textRef.current.length) {
        clearInterval(timer)
      }
    }, speed)

    return () => clearInterval(timer)
  }, [text, speed])

  return displayed
}

function AssistantMessage({ text, animate }) {
  const typed = useTypewriter(text, 10)
  const displayed = animate ? typed : text

  // Render markdown images ![alt](url)
  const safeText = displayed || '';
  const parts = safeText.split(/(!\[.*?\]\(.*?\))/g);

  return (
    <div className="text-body-md text-on-surface leading-relaxed space-y-2">
      {parts.map((part, i) => {
        const match = part.match(/!\[(.*?)\]\((.*?)\)/);
        if (match) {
          return (
            <img 
              key={i} 
              src={match[2]} 
              alt={match[1]} 
              className="max-w-full rounded-xl border border-outline-variant/30 my-2 shadow-sm"
              loading="lazy"
            />
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </div>
  )
}

function CurrentStepIndicator({ steps, isGenerating }) {
  if (!steps || steps.length === 0) return null;

  // Get the most recent step
  const currentStep = steps[steps.length - 1];
  
  let icon = 'build';
  let label = currentStep.tool;
  
  if (currentStep.tool === 'product_retriever') {
    icon = 'search';
    label = currentStep.status === 'searching' ? 'Searching products...' : 'Retrieved products';
  } else if (currentStep.tool === 'reranker') {
    icon = 'auto_awesome';
    label = currentStep.status === 'reranking' ? 'Reranking best matches...' : 'Reranked matches';
  } else if (currentStep.tool === 'validator') {
    icon = 'verified';
    label = currentStep.status === 'done' ? 'Validated results' : 'Validating...';
  } else if (currentStep.tool === 'sql_query') {
    icon = 'query_stats';
    label = currentStep.status === 'running' ? 'Querying database...' : 'Queried database';
  }

  const isDone = currentStep.status === 'done' || currentStep.status === 'error';

  return (
    <div className="flex items-center gap-2 mb-3 mt-1 ml-1 text-[13px] font-medium text-primary animate-pulse">
      <span className="material-symbols-outlined text-[18px]">
        {currentStep.status === 'error' ? 'error' : isDone ? 'check_circle' : icon}
      </span>
      <span>{label}</span>
    </div>
  );
}

function TracePanel({ steps, forceExpanded, hideToggle }) {
  const [expanded, setExpanded] = useState(false)
  if (!steps || steps.length === 0) return null

  const isExpanded = forceExpanded || expanded;

  const getStepIcon = (tool) => {
    if (tool === 'product_retriever') return 'search'
    if (tool === 'reranker') return 'auto_awesome'
    if (tool === 'sql_query') return 'query_stats'
    return 'build'
  }

  const getStepColor = (status) => {
    if (status === 'done') return 'text-emerald-600 bg-emerald-50 border-emerald-200'
    if (status === 'error') return 'text-red-600 bg-red-50 border-red-200'
    if (status === 'running' || status === 'reranking' || status === 'searching') return 'text-amber-600 bg-amber-50 border-amber-200'
    return 'text-neutral-600 bg-neutral-50 border-neutral-200'
  }

  const getStatusIcon = (status) => {
    if (status === 'done') return 'check_circle'
    if (status === 'error') return 'error'
    if (status === 'running' || status === 'reranking' || status === 'searching') return 'pending'
    return 'radio_button_unchecked'
  }

  return (
    <div className="mt-2 border-t border-emerald-100 pt-2">
      {!hideToggle && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 text-[10px] text-neutral-400 hover:text-neutral-600 transition-colors"
        >
          <span className="material-symbols-outlined text-[12px]">{isExpanded ? 'expand_less' : 'expand_more'}</span>
          <span className="font-medium uppercase tracking-tighter">
            {isExpanded ? 'Hide trace' : `Trace (${steps.length} steps)`}
          </span>
        </button>
      )}

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {steps.map((step, i) => (
            <div key={i} className={`flex items-start gap-2 p-2 rounded-lg border ${getStepColor(step.status)}`}>
              <span className="material-symbols-outlined text-[14px] mt-0.5">
                {getStatusIcon(step.status)}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[12px]">{getStepIcon(step.tool)}</span>
                  <span className="text-[11px] font-semibold capitalize">{step.tool.replace('_', ' ')}</span>
                  <span className="text-[10px] opacity-60 ml-auto">{step.status}</span>
                </div>
                {step.query && (
                  <p className="text-[10px] mt-1 opacity-80 truncate" title={step.query}>
                    Query: {step.query}
                  </p>
                )}
                {step.candidates !== undefined && (
                  <p className="text-[10px] mt-0.5 opacity-80">
                    Retrieved {step.candidates} candidates
                  </p>
                )}
                {step.returned !== undefined && (
                  <p className="text-[10px] mt-0.5 opacity-80">
                    Returned top {step.returned} after reranking
                  </p>
                )}
                {step.found !== undefined && (
                  <p className="text-[10px] mt-0.5 opacity-80">
                    Found {step.found} products
                  </p>
                )}
                {step.rows !== undefined && (
                  <p className="text-[10px] mt-0.5 opacity-80">
                    Query returned {step.rows} rows
                  </p>
                )}
                {step.error && (
                  <p className="text-[10px] mt-0.5 text-red-500">
                    Error: {step.error}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [products, setProducts] = useState([])
  const [productSets, setProductSets] = useState([])
  const [currentSetIndex, setCurrentSetIndex] = useState(-1)
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState([])
  const [userId] = useState(() => getOrCreateUserId())
  const [sessionId, setSessionId] = useState(() => getOrCreateSessionId())
  const [sessions, setSessions] = useState([])
  const [isLoadingLastSession, setIsLoadingLastSession] = useState(true)
  const chatEndRef = useRef(null)

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

  // Create session on backend
  useEffect(() => {
    const createSession = async () => {
      try {
        await fetch(`${API_URL}/chat/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            session_id: sessionId,
          }),
        })
        loadSessions()
      } catch (err) {
        console.error('Failed to create session:', err)
      }
    }
    createSession()
  }, [sessionId, userId, loadSessions])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // Load messages for a session
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
        const lastAssistant = [...data].reverse().find((m) => m.role === 'assistant')
        if (lastAssistant?.products_json?.length) {
          setProducts(lastAssistant.products_json)
          setProductSets([lastAssistant.products_json])
          setCurrentSetIndex(0)
        } else {
          setProducts([])
          setProductSets([])
          setCurrentSetIndex(-1)
        }
      } else {
        setMessages([INITIAL_MESSAGE])
        setProducts([])
        setProductSets([])
        setCurrentSetIndex(-1)
      }
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }, [])

  // Load last session on mount
  useEffect(() => {
    const loadLastSession = async () => {
      const lastSessionId = localStorage.getItem('shopify_assistant_last_session_id')
      if (!lastSessionId) {
        setIsLoadingLastSession(false)
        return
      }
      try {
        const res = await fetch(`${API_URL}/chat/sessions?user_id=${userId}`)
        if (res.ok) {
          const allSessions = await res.json()
          const lastSession = allSessions.find(s => s.session_id === lastSessionId)
          if (lastSession) {
            setSessionId(lastSessionId)
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
    localStorage.setItem('shopify_assistant_last_session_id', newSessionId)
    setMessages([INITIAL_MESSAGE])
    setProducts([])
    setProductSets([])
    setCurrentSetIndex(-1)
    loadSessions()
  }

  const handleSwitchSession = (sid) => {
    setSessionId(sid)
    localStorage.setItem('shopify_assistant_last_session_id', sid)
    loadSessionMessages(sid)
  }

  const handleDeleteSession = async (e, sid) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this session?')) return
    try {
      const res = await fetch(`${API_URL}/chat/sessions/${sid}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete session')
      setSessions((prev) => {
        const nextSessions = prev.filter((s) => s.session_id !== sid)
        if (sid === sessionId) {
          const nextSession = nextSessions[0]
          if (nextSession) {
            setSessionId(nextSession.session_id)
            localStorage.setItem('shopify_assistant_last_session_id', nextSession.session_id)
            loadSessionMessages(nextSession.session_id)
          } else {
            const newSid = uuidv4()
            setSessionId(newSid)
            localStorage.setItem('shopify_assistant_last_session_id', newSid)
            setMessages([INITIAL_MESSAGE])
            setProducts([])
            setProductSets([])
            setCurrentSetIndex(-1)
          }
        }
        return nextSessions
      })
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  const handleSend = async (text) => {
    setMessages((prev) => [...prev, { role: 'user', text }])
    setLoading(true)
    setSteps([])
    
    const newMessageIndex = messages.length + 1; // Since we just appended user message
    setMessages((prev) => [...prev, { role: 'assistant', text: '', steps: [] }])
    
    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: userId,
          session_id: sessionId,
        }),
      })
      
      if (!response.ok) throw new Error('Failed to get response')
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let done = false;
      let assistantText = '';
      
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunkString = decoder.decode(value, { stream: true });
          const lines = chunkString.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '').trim();
              if (!dataStr) continue;
              
              try {
                const data = JSON.parse(dataStr);
                
                if (data.type === 'chunk') {
                  assistantText += data.content;
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1].text = assistantText;
                    return newMessages;
                  });
                } else if (data.type === 'steps_update') {
                  setSteps(data.steps);
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1].steps = data.steps;
                    return newMessages;
                  });
                } else if (data.type === 'step') {
                  setSteps((prev) => {
                    const newSteps = [...prev, data.step];
                    setMessages((msgs) => {
                      const newMsgs = [...msgs];
                      newMsgs[newMsgs.length - 1].steps = newSteps;
                      return newMsgs;
                    });
                    return newSteps;
                  });
                } else if (data.type === 'products') {
                  const sets = data.product_sets || []
                  setProductSets(sets)
                  if (sets.length > 0) {
                    const latestIndex = sets.length - 1
                    setCurrentSetIndex(latestIndex)
                    setProducts(sets[latestIndex])
                  } else if (data.products && data.products.length > 0) {
                    setProducts(data.products)
                  }
                } else if (data.type === 'error') {
                   setMessages((prev) => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1].text += `\nError: ${data.message}`;
                    return newMessages;
                  });
                } else if (data.type === 'done') {
                  // Streaming finished
                }
              } catch (e) {
                console.error("Error parsing SSE JSON:", e, dataStr);
              }
            }
          }
        }
      }
      
    } catch (err) {
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].text = `Oops, something went wrong: ${err.message}`;
        return newMessages;
      });
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-white">
      <style>{`
        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .animate-slideInLeft { animation: slideInLeft 0.5s ease-out forwards; }
        .animate-slideInRight { animation: slideInRight 0.5s ease-out forwards; }
        .animate-fadeIn { animation: fadeIn 0.6s ease-out forwards; }
      `}</style>

      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-72 flex flex-col bg-white border-r border-neutral-200 shadow-[20px_0_40px_-15px_rgba(0,0,0,0.08)] z-40 animate-slideInLeft">
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

        <nav className="flex-1 overflow-y-auto py-4">
          <div className="px-3">
            <ul className="space-y-1">
              {sessions.length === 0 ? (
                <li className="px-3 py-2 text-body-sm text-neutral-400 text-center">No sessions yet</li>
              ) : (
                sessions.map((s) => (
                  <li
                    key={s.session_id}
                    onClick={() => handleSwitchSession(s.session_id)}
                    className={`group flex items-center justify-between px-3 py-2 rounded-lg transition-all cursor-pointer ${
                      s.session_id === sessionId
                        ? 'bg-emerald-50 text-primary-container font-semibold'
                        : 'text-neutral-500 hover:bg-neutral-50'
                    }`}
                  >
                    <span className="text-body-sm truncate pr-2">
                      {s.store_domain || `Session ${s.session_id.slice(0, 8)}`}
                    </span>
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

      {/* Main Content */}
      <main className="ml-72 flex w-full h-screen overflow-hidden">
        {/* Chat */}
        <section className="w-1/2 flex flex-col bg-white border-r border-neutral-200 animate-fadeIn">
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
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, idx) => (
              <div key={idx} style={{ animation: `slideInLeft 0.3s ease-out ${idx * 50}ms forwards`, opacity: 0 }}>
                {msg.role === 'assistant' ? (
                  <div className="flex gap-4 max-w-[90%]">
                    <div className="h-8 w-8 rounded-full bg-emerald-50 shrink-0 flex items-center justify-center border border-emerald-100">
                      <span className="material-symbols-outlined text-primary-container text-[18px]">auto_awesome</span>
                    </div>
                      <div className="bg-[#F0F8F5] p-4 rounded-2xl rounded-tl-none border border-emerald-50 shadow-sm max-w-[85%] min-w-[200px]">
                        {loading && idx === messages.length - 1 && msg.steps && msg.steps.length > 0 && (
                           <CurrentStepIndicator steps={msg.steps} isGenerating={!!msg.text} />
                        )}
                        {(!msg.text && idx === messages.length - 1 && loading) ? (
                            <div className="flex gap-2 mb-2 mt-1 ml-1">
                              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                            </div>
                        ) : (
                            msg.text && <AssistantMessage text={msg.text} animate={false} />
                        )}
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
            {/* Old loading container removed since loading is rendered within the message itself */}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
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

        {/* Product Grid */}
        <section className="w-1/2 flex flex-col bg-surface overflow-y-auto animate-slideInRight">
          <div className="p-8">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="font-h2 text-on-surface mb-1">Curated Recommendations</h2>
                <p className="text-body-sm text-secondary">
                  {productSets.length > 1
                    ? `Result ${currentSetIndex + 1} of ${productSets.length}`
                    : products.length > 0
                    ? `Based on your recent request`
                    : 'Products will appear here'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {productSets.length > 1 && (
                  <div className="flex items-center gap-1 mr-2">
                    <button
                      onClick={() => {
                        const newIndex = Math.max(0, currentSetIndex - 1)
                        setCurrentSetIndex(newIndex)
                        setProducts(productSets[newIndex])
                      }}
                      disabled={currentSetIndex <= 0}
                      className="p-1.5 rounded-md border border-neutral-200 bg-white hover:bg-neutral-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    >
                      <span className="material-symbols-outlined text-[16px]">arrow_back</span>
                    </button>
                    <span className="text-[11px] text-neutral-500 font-medium min-w-[3rem] text-center">
                      {currentSetIndex + 1} / {productSets.length}
                    </span>
                    <button
                      onClick={() => {
                        const newIndex = Math.min(productSets.length - 1, currentSetIndex + 1)
                        setCurrentSetIndex(newIndex)
                        setProducts(productSets[newIndex])
                      }}
                      disabled={currentSetIndex >= productSets.length - 1}
                      className="p-1.5 rounded-md border border-neutral-200 bg-white hover:bg-neutral-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    >
                      <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                    </button>
                  </div>
                )}
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
            </div>

            {products.length > 0 ? (
              <div className="grid grid-cols-2 gap-6">
                {/* Featured Card */}
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
                      <p className="text-h3 font-bold text-on-surface">{products[0].price ? `${Number(products[0].price).toFixed(2)} EGP` : '0.00 EGP'}</p>
                      <span className="mt-2 flex items-center justify-center text-primary-container group-hover:text-primary transition-colors text-2xl">
                        <span className="material-symbols-outlined">arrow_outward</span>
                      </span>
                    </div>
                  </div>
                </a>

                {/* Regular Cards */}
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
                        <p className="text-body-md font-bold">{product.price ? `${Number(product.price).toFixed(2)} EGP` : '0.00 EGP'}</p>
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
    </div>
  )
}
