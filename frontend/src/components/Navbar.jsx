import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const location = useLocation()
  const isChat = location.pathname === '/chat'

  return (
    <header className="bg-white border-b border-surface-container-high shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07)] sticky top-0 z-50">
      <nav className="flex justify-between items-center w-full max-w-container-max mx-auto px-6 h-16">
        <Link to="/" className="text-xl font-extrabold tracking-tight text-primary-container font-display">
          Shopify Assistant
        </Link>
        <div className="hidden md:flex items-center gap-8 font-body-md text-sm font-medium">
          <Link
            to="/"
            className={`pb-1 transition-colors duration-200 ${
              !isChat
                ? 'text-primary-container border-b-2 border-primary-container'
                : 'text-secondary hover:text-primary-container'
            }`}
          >
            Discover
          </Link>
          <Link
            to="/chat"
            className={`pb-1 transition-colors duration-200 ${
              isChat
                ? 'text-primary-container border-b-2 border-primary-container'
                : 'text-secondary hover:text-primary-container'
            }`}
          >
            My Lists
          </Link>
          <span className="text-secondary hover:text-primary-container transition-colors duration-200 cursor-pointer">
            Activity
          </span>
        </div>
        <div className="flex items-center gap-4 text-primary-container">
          <button className="p-2 hover:text-primary transition-transform active:scale-95">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="p-2 hover:text-primary transition-transform active:scale-95">
            <span className="material-symbols-outlined">account_circle</span>
          </button>
        </div>
      </nav>
    </header>
  )
}
