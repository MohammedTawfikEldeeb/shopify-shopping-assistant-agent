import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const FEATURED_PRODUCTS = [
  {
    id: 1,
    title: 'Minimalist Chronos Watch',
    image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop',
    price: 249.0,
    vendor: 'Chronos Co.',
  },
  {
    id: 2,
    title: 'Velocity Runner Pro',
    image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop',
    price: 185.0,
    vendor: 'Velocity Sports',
  },
  {
    id: 3,
    title: 'Acoustic Pure Headset',
    image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop',
    price: 320.0,
    vendor: 'Acoustic Labs',
  },
  {
    id: 4,
    title: 'Classic Silhouette Shades',
    image: 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&fit=crop',
    price: 145.0,
    vendor: 'Silhouette Eyewear',
  },
]

export default function LandingPage() {
  const [storeUrl, setStoreUrl] = useState('')
  const navigate = useNavigate()

  const handleStart = () => {
    const url = storeUrl.trim()
    if (url) {
      navigate('/chat', { state: { storeUrl: url } })
    } else {
      navigate('/chat')
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden pt-xl pb-xl px-margin">
          <div className="max-w-container-max mx-auto text-center relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-on-primary-container text-primary text-label-sm mb-md">
              <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                auto_awesome
              </span>
              Next-Gen Personal Shopping Assistant
            </div>
            <h1 className="font-display text-display text-on-background mb-sm max-w-3xl mx-auto">
              Find exactly what you need in any Shopify store
            </h1>
            <p className="font-body-lg text-body-lg text-secondary mb-lg max-w-2xl mx-auto">
              Paste a store URL and let our AI assistant help you shop. From discovery to checkout, we curate the best products based on your personal style.
            </p>
            <div className="max-w-xl mx-auto bg-white p-sm rounded-xl border border-outline-variant shadow-lg flex items-center gap-sm">
              <div className="flex-grow flex items-center gap-2 pl-2">
                <span className="material-symbols-outlined text-outline">link</span>
                <input
                  type="text"
                  value={storeUrl}
                  onChange={(e) => setStoreUrl(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleStart()}
                  placeholder="https://store-name.myshopify.com"
                  className="w-full border-none focus:ring-0 font-body-md text-on-surface bg-transparent outline-none"
                />
              </div>
              <button
                onClick={handleStart}
                className="bg-primary-container text-on-primary font-label-md px-lg py-3 rounded-lg hover:bg-primary transition-colors flex items-center gap-2"
              >
                Chat
                <span className="material-symbols-outlined text-sm">send</span>
              </button>
            </div>
          </div>
          <div className="absolute top-0 right-0 -z-10 translate-x-1/4 -translate-y-1/4 opacity-20">
            <div className="w-[600px] h-[600px] rounded-full bg-gradient-to-br from-primary-fixed to-surface-bright blur-3xl"></div>
          </div>
        </section>

        {/* Bento Features Section */}
        <section className="py-xl px-margin bg-surface-container-low">
          <div className="max-w-container-max mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
              {/* Large Bento Card */}
              <div className="md:col-span-8 bg-white rounded-xl p-lg border border-outline-variant relative overflow-hidden flex flex-col justify-between">
                <div className="relative z-10 max-w-md">
                  <h2 className="font-h2 text-h2 mb-sm">Smart Search Reimagined</h2>
                  <p className="font-body-md text-body-md text-secondary">
                    No more endless scrolling. Our AI indexes the entire catalog instantly to find that specific item you're looking for, even if you can't describe it perfectly.
                  </p>
                </div>
                <div className="mt-lg">
                  <img
                    className="w-full h-64 object-cover rounded-lg border border-outline-variant"
                    src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&h=400&fit=crop"
                    alt="Smart search interface"
                  />
                </div>
              </div>

              {/* Small Bento Card 1 */}
              <div className="md:col-span-4 bg-primary text-on-primary rounded-xl p-lg flex flex-col justify-between border border-transparent shadow-md">
                <div className="w-12 h-12 rounded-lg bg-primary-fixed text-on-primary-fixed flex items-center justify-center mb-md">
                  <span className="material-symbols-outlined text-3xl">bolt</span>
                </div>
                <div>
                  <h3 className="font-h3 text-h3 mb-xs">Instant Recommendations</h3>
                  <p className="font-body-sm text-body-sm opacity-90">
                    Get curated lists of products based on your browsing history and style preferences in seconds.
                  </p>
                </div>
              </div>

              {/* Small Bento Card 2 */}
              <div className="md:col-span-4 bg-white rounded-xl p-lg border border-outline-variant flex flex-col justify-between">
                <div className="w-12 h-12 rounded-lg bg-surface-container-highest text-secondary flex items-center justify-center mb-md">
                  <span className="material-symbols-outlined text-3xl">person_search</span>
                </div>
                <div>
                  <h3 className="font-h3 text-h3 mb-xs text-on-background">Personalized Experience</h3>
                  <p className="font-body-sm text-body-sm text-secondary">
                    Your shopper learns from your feedback, refining results to match your unique aesthetic over time.
                  </p>
                </div>
              </div>

              {/* Mid Bento Card */}
              <div className="md:col-span-8 bg-[#F0F8F5] rounded-xl p-lg border border-primary/10 flex flex-col md:flex-row items-center gap-lg">
                <div className="flex-grow">
                  <h3 className="font-h3 text-h3 mb-xs text-primary">Chat with Any Store</h3>
                  <p className="font-body-md text-body-md text-on-surface-variant">
                    Whether it's high-fashion, electronics, or home decor, our assistant adapts to the brand's language and inventory effortlessly.
                  </p>
                </div>
                <div className="shrink-0 flex -space-x-4">
                  <div className="w-16 h-16 rounded-full border-4 border-white bg-surface-container-highest overflow-hidden">
                    <img
                      src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face"
                      alt="Consultant"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="w-16 h-16 rounded-full border-4 border-white bg-primary-container flex items-center justify-center text-on-primary text-2xl font-bold">
                    AI
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Social Proof */}
        <section className="py-xl px-margin border-t border-outline-variant">
          <div className="max-w-container-max mx-auto">
            <p className="font-label-sm text-label-sm text-center text-outline mb-lg uppercase tracking-widest">
              Trusted by power shoppers globally
            </p>
            <div className="flex flex-wrap justify-center items-center gap-xl opacity-40 grayscale">
              <div className="font-display text-h1">VOGUE</div>
              <div className="font-display text-h1">Hypebeast</div>
              <div className="font-display text-h1">GQ</div>
              <div className="font-display text-h1">Complex</div>
            </div>
          </div>
        </section>

        {/* Product Highlight Card Row */}
        <section className="py-xl px-margin">
          <div className="max-w-container-max mx-auto">
            <div className="flex justify-between items-end mb-lg">
              <div>
                <h2 className="font-h2 text-h2 mb-xs">Featured Discoveries</h2>
                <p className="font-body-md text-body-md text-secondary">
                  Items found for users today across various Shopify merchants.
                </p>
              </div>
              <button className="text-primary font-label-md flex items-center gap-1 hover:underline underline-offset-4">
                View All Activity <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter">
              {FEATURED_PRODUCTS.map((product) => (
                <div
                  key={product.id}
                  className="group bg-white rounded-lg border border-outline-variant overflow-hidden flex flex-col"
                >
                  <div className="h-64 relative overflow-hidden border-b border-outline-variant">
                    <img
                      src={product.image}
                      alt={product.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute top-2 right-2">
                      <button className="w-8 h-8 rounded-full bg-white/90 shadow-sm flex items-center justify-center text-secondary hover:text-primary transition-colors">
                        <span className="material-symbols-outlined text-sm">favorite</span>
                      </button>
                    </div>
                  </div>
                  <div className="p-md flex-grow">
                    <h3 className="font-h3 text-body-md mb-xs">{product.title}</h3>
                    <div className="flex justify-between items-center">
                      <span className="font-body-sm text-secondary">${product.price.toFixed(2)}</span>
                      <button className="bg-surface-container-low p-2 rounded hover:bg-secondary-container transition-colors">
                        <span className="material-symbols-outlined text-sm">add_shopping_cart</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-xl px-margin bg-on-background text-inverse-on-surface text-center">
          <div className="max-w-container-max mx-auto">
            <h2 className="font-display text-display mb-sm">Ready to shop smarter?</h2>
            <p className="font-body-lg text-body-lg opacity-70 mb-lg max-w-xl mx-auto">
              Join thousands of users who let AI handle the searching while they enjoy the finding.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-md">
              <button
                onClick={() => navigate('/chat')}
                className="bg-primary-container text-on-primary px-lg py-4 rounded-lg font-label-md hover:bg-primary transition-transform active:scale-95"
              >
                Get Started Free
              </button>
              <button className="border border-outline text-white px-lg py-4 rounded-lg font-label-md hover:bg-white/10 transition-transform active:scale-95">
                Book a Demo
              </button>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
