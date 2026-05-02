import { useState, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import ProductCard from '../components/ProductCard'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const INITIAL_MESSAGE = {
  role: 'assistant',
  text: "Hello! I'm your Personal Shopping Agent. Paste a Shopify store URL above and tell me what you're looking for. I'll curate the best products just for you.",
}

export default function ChatPage() {
  const location = useLocation()
  const initialStoreUrl = location.state?.storeUrl || ''

  const [storeUrl, setStoreUrl] = useState(initialStoreUrl)
  const [storeName, setStoreName] = useState('Your Store')
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
        body: JSON.stringify({ message: text }),
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
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Secondary Header: Store Context */}
      <section className="bg-surface-container-low border-b border-outline-variant/30">
        <div className="max-w-container-max mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center text-white">
              <span className="material-symbols-outlined">store</span>
            </div>
            <div>
              <p className="text-label-sm text-secondary uppercase tracking-widest">Assistant active</p>
              <h2 className="font-h2 text-h2 text-on-surface">
                Browsing: <span className="text-primary">{storeName}</span>
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white rounded-lg border border-outline-variant/50 px-3 py-2">
              <span className="material-symbols-outlined text-outline text-sm">link</span>
              <input
                type="text"
                value={storeUrl}
                onChange={(e) => setStoreUrl(e.target.value)}
                placeholder="https://store.myshopify.com"
                className="bg-transparent border-none focus:ring-0 text-body-sm text-on-surface placeholder:text-secondary outline-none w-56"
              />
            </div>
            <button
              onClick={handleIndexStore}
              disabled={ingesting || !storeUrl.trim()}
              className="bg-primary-container text-on-primary px-4 py-2 rounded-lg font-label-md hover:bg-primary transition-colors active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {ingesting ? (
                <>
                  <span className="material-symbols-outlined animate-spin text-sm">sync</span>
                  Indexing...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-sm">cloud_upload</span>
                  Index Store
                </>
              )}
            </button>
            <span className="inline-flex items-center px-3 py-1 rounded-full bg-primary-fixed text-on-primary-fixed text-label-sm">
              <span className="w-2 h-2 rounded-full bg-primary mr-2"></span>
              AI Shopping Agent Live
            </span>
          </div>
        </div>
      </section>

      <main className="max-w-container-max mx-auto h-[calc(100vh-144px)] flex overflow-hidden">
        {/* Left Pane: AI Chat (40%) */}
        <aside className="w-[40%] flex flex-col border-r border-outline-variant/20 bg-white relative">
          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, idx) => (
              <ChatMessage key={idx} role={msg.role} text={msg.text} />
            ))}
            {loading && (
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-primary-container/10 flex items-center justify-center flex-shrink-0">
                  <img
                    src="https://ui-avatars.com/api/?name=AI&background=00654b&color=fff"
                    alt="Assistant"
                    className="w-full h-full rounded-full object-cover"
                  />
                </div>
                <div className="max-w-[85%] bg-[#F0F8F5] p-4 rounded-xl rounded-tl-none shadow-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Message Input */}
          <div className="p-6 border-t border-outline-variant/30 bg-white">
            <ChatInput onSend={handleSend} disabled={loading} />
          </div>
        </aside>

        {/* Right Pane: Recommendations (60%) */}
        <section className="w-[60%] bg-surface flex flex-col">
          <div className="p-8 overflow-y-auto">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h3 className="font-h3 text-h3 text-on-surface">Curated Picks</h3>
                <p className="text-body-sm text-secondary">
                  {products.length > 0
                    ? `${products.length} products found based on your request`
                    : 'Products will appear here after you search'}
                </p>
              </div>
              {products.length > 0 && (
                <button className="flex items-center gap-2 text-label-md text-primary hover:underline">
                  <span className="material-symbols-outlined text-sm">tune</span>
                  Filter Results
                </button>
              )}
            </div>

            {products.length > 0 ? (
              <div className="grid grid-cols-2 gap-gutter">
                {products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-secondary">
                <span className="material-symbols-outlined text-6xl mb-4 opacity-40">shopping_bag</span>
                <p className="font-body-lg text-body-lg">No products yet</p>
                <p className="text-body-sm mt-2">Start a conversation to see curated products here</p>
              </div>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
