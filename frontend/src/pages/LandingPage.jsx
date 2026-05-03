import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function LandingPage() {
  const [storeUrl, setStoreUrl] = useState('')
  const [focusedInput, setFocusedInput] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const handleStart = async () => {
    const url = storeUrl.trim()
    if (!url) {
      navigate('/chat')
      return
    }

    setIsLoading(true)
    try {
      const res = await fetch(`${API_URL}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ store: url }),
      })
      if (!res.ok) throw new Error('Failed to index store')
      const data = await res.json()
      navigate('/chat', { state: { storeUrl: url, storeDomain: data.store_domain, totalProducts: data.total_products_received } })
    } catch (err) {
      console.error('Index error:', err)
      alert(`Error indexing store: ${err.message}`)
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-[#f9f9fa] via-[#f0f8f5] to-[#f9f9fa] flex flex-col items-center justify-center relative overflow-hidden">
      <style>{`
        @keyframes float-up {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes fadeInScale {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        .animate-float {
          animation: float-up 6s ease-in-out infinite;
        }
        .animate-fadeInScale {
          animation: fadeInScale 0.8s ease-out forwards;
        }
        .card-shadow {
          box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.06);
        }
      `}</style>

      <main className="w-full max-w-6xl px-8 flex flex-col items-center justify-center space-y-16 relative z-10">
        {/* Brand Identity Component */}
        <div className="flex flex-col items-center space-y-4 text-center animate-fadeInScale">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-3 bg-primary-container rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300">
              <span className="material-symbols-outlined text-on-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                shopping_basket
              </span>
            </div>
            <span className="font-h3 text-h3 text-primary-container font-bold tracking-tight">
              Shopify Assistant
            </span>
          </div>
          <h1 className="font-display text-display text-on-surface max-w-3xl leading-tight font-bold">
            Shopify Personal Shopping Agent
          </h1>
          <p className="font-body-lg text-body-lg text-secondary max-w-2xl leading-relaxed">
            Paste a store URL to start your curated shopping experience.
          </p>
        </div>

        {/* Input Section */}
        <div className={`w-full max-w-2xl bg-surface-container-lowest p-8 rounded-2xl border-2 transition-all duration-300 card-shadow ${
          focusedInput 
            ? 'border-primary shadow-2xl shadow-primary/20' 
            : 'border-neutral-200'
        }`}>
          <div className="flex flex-col space-y-6">
            {/* URL Input */}
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                <span className={`material-symbols-outlined transition-colors duration-300 ${
                  focusedInput ? 'text-primary' : 'text-outline'
                }`}>
                  link
                </span>
              </div>
              <input
                value={storeUrl}
                onChange={(e) => setStoreUrl(e.target.value)}
                onFocus={() => setFocusedInput(true)}
                onBlur={() => setFocusedInput(false)}
                onKeyDown={(e) => e.key === 'Enter' && handleStart()}
                className="w-full pl-14 pr-4 py-4 bg-white text-on-surface font-body-md rounded-xl border-2 border-outline-variant hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all outline-none"
                placeholder="https://your-favorite-store.myshopify.com"
                type="url"
              />
            </div>

            {/* Action Row */}
            <div className="flex flex-col md:flex-row items-center gap-6">
              <button
                onClick={handleStart}
                disabled={isLoading}
                className="w-full md:w-auto px-8 py-4 bg-gradient-to-r from-primary-container to-primary-container/90 text-on-primary font-label-md rounded-xl hover:shadow-lg hover:shadow-primary/30 hover:scale-105 transition-all duration-200 active:scale-95 disabled:opacity-60 disabled:hover:scale-100 flex items-center justify-center gap-2 border-2 border-primary-fixed/30"
              >
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                  chat_bubble
                </span>
                {isLoading ? 'Loading...' : 'Chat'}
              </button>

              <div className="hidden md:block flex-1 border-t-2 border-outline-variant/30"></div>

              <span className="text-label-sm font-label-sm text-secondary uppercase tracking-widest">
                Ready to assist
              </span>
            </div>
          </div>
        </div>

        {/* Secondary Visual Anchor (Features) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl opacity-90 mt-8">
          <div className="bg-white rounded-2xl p-6 flex items-start gap-4 border-2 border-outline-variant/20 hover:border-primary/30 hover:shadow-lg transition-all duration-300 group cursor-pointer animate-fadeInScale" style={{ animationDelay: '100ms' }}>
            <div className="p-3 bg-primary-fixed/10 rounded-lg group-hover:bg-primary-fixed/20 transition-colors">
              <span className="material-symbols-outlined text-primary text-2xl">inventory_2</span>
            </div>
            <div>
              <h4 className="font-label-md text-label-md text-on-surface font-bold">Inventory Search</h4>
              <p className="font-body-sm text-body-sm text-secondary mt-1">Real-time stock across any Shopify store.</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 flex items-start gap-4 border-2 border-outline-variant/20 hover:border-primary/30 hover:shadow-lg transition-all duration-300 group cursor-pointer animate-fadeInScale" style={{ animationDelay: '200ms' }}>
            <div className="p-3 bg-primary-fixed/10 rounded-lg group-hover:bg-primary-fixed/20 transition-colors">
              <span className="material-symbols-outlined text-primary text-2xl">auto_awesome</span>
            </div>
            <div>
              <h4 className="font-label-md text-label-md text-on-surface font-bold">Curated Style</h4>
              <p className="font-body-sm text-body-sm text-secondary mt-1">AI-driven recommendations based on preference.</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 flex items-start gap-4 border-2 border-outline-variant/20 hover:border-primary/30 hover:shadow-lg transition-all duration-300 group cursor-pointer animate-fadeInScale" style={{ animationDelay: '300ms' }}>
            <div className="p-3 bg-primary-fixed/10 rounded-lg group-hover:bg-primary-fixed/20 transition-colors">
              <span className="material-symbols-outlined text-primary text-2xl">verified</span>
            </div>
            <div>
              <h4 className="font-label-md text-label-md text-on-surface font-bold">Secure Checkout</h4>
              <p className="font-body-sm text-body-sm text-secondary mt-1">Direct integration for seamless transactions.</p>
            </div>
          </div>
        </div>
      </main>

      {/* Contextual Aesthetic Background Elements */}
      <div className="fixed bottom-0 left-0 w-full h-80 overflow-hidden -z-0 opacity-40 pointer-events-none">
        <div className="flex justify-between items-end h-full px-8 gap-6">
          {/* Card 1 - Watch */}
          <div className="w-64 h-80 bg-white rounded-t-3xl shadow-2xl transform translate-y-16 rotate-3 border-2 border-neutral-100 flex flex-col p-4 space-y-2 hover:translate-y-12 transition-transform duration-500 animate-float">
            <div className="w-full h-40 bg-surface-container-high rounded-2xl overflow-hidden">
              <img
                className="w-full h-full object-cover grayscale opacity-60 hover:grayscale-0 hover:opacity-80 transition-all duration-500"
                alt="Premium minimalist watch"
                src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop"
              />
            </div>
            <div className="h-4 w-3/4 bg-surface-container-high rounded-lg"></div>
            <div className="h-4 w-1/2 bg-surface-container-high rounded-lg"></div>
          </div>

          {/* Card 2 - Headphones */}
          <div className="hidden lg:flex w-72 h-96 bg-white rounded-t-3xl shadow-2xl transform translate-y-8 -rotate-2 border-2 border-neutral-100 flex-col p-4 space-y-2 hover:translate-y-2 transition-transform duration-500 animate-float" style={{ animationDelay: '1s' }}>
            <div className="w-full h-56 bg-surface-container-high rounded-2xl overflow-hidden">
              <img
                className="w-full h-full object-cover grayscale opacity-60 hover:grayscale-0 hover:opacity-80 transition-all duration-500"
                alt="Modern high-fidelity headphones"
                src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop"
              />
            </div>
            <div className="h-4 w-2/3 bg-surface-container-high rounded-lg"></div>
            <div className="h-4 w-1/3 bg-surface-container-high rounded-lg"></div>
          </div>

          {/* Card 3 - Sneaker */}
          <div className="w-60 h-72 bg-white rounded-t-3xl shadow-2xl transform translate-y-24 rotate-6 border-2 border-neutral-100 flex flex-col p-4 space-y-2 hover:translate-y-16 transition-transform duration-500 animate-float" style={{ animationDelay: '2s' }}>
            <div className="w-full h-32 bg-surface-container-high rounded-2xl overflow-hidden">
              <img
                className="w-full h-full object-cover grayscale opacity-60 hover:grayscale-0 hover:opacity-80 transition-all duration-500"
                alt="Vibrant red sports sneaker"
                src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop"
              />
            </div>
            <div className="h-4 w-4/5 bg-surface-container-high rounded-lg"></div>
            <div className="h-4 w-1/4 bg-surface-container-high rounded-lg"></div>
          </div>
        </div>
      </div>

      {/* Decorative gradient blur elements */}
      <div className="fixed top-0 right-0 w-96 h-96 bg-primary-fixed/10 rounded-full blur-3xl -z-20 opacity-60"></div>
      <div className="fixed bottom-0 left-0 w-96 h-96 bg-primary-container/5 rounded-full blur-3xl -z-20 opacity-60"></div>
    </div>
  )
}
