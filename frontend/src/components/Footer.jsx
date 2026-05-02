export default function Footer() {
  return (
    <footer className="bg-surface-container-low border-t border-surface-container-high py-12">
      <div className="flex flex-col md:flex-row justify-between items-center w-full max-w-container-max mx-auto px-8">
        <div className="flex flex-col gap-2 mb-6 md:mb-0">
          <div className="font-bold text-on-surface text-lg font-display">Shopify Concierge</div>
          <div className="text-label-sm text-secondary">
            &copy; {new Date().getFullYear()} Shopify Concierge. Curated Efficiency.
          </div>
        </div>
        <div className="flex flex-wrap justify-center gap-8">
          <a className="text-label-sm text-secondary hover:underline decoration-primary underline-offset-4 opacity-80 hover:opacity-100 transition-opacity" href="#">Privacy</a>
          <a className="text-label-sm text-secondary hover:underline decoration-primary underline-offset-4 opacity-80 hover:opacity-100 transition-opacity" href="#">Terms</a>
          <a className="text-label-sm text-secondary hover:underline decoration-primary underline-offset-4 opacity-80 hover:opacity-100 transition-opacity" href="#">Support</a>
          <a className="text-label-sm text-secondary hover:underline decoration-primary underline-offset-4 opacity-80 hover:opacity-100 transition-opacity" href="#">API</a>
        </div>
      </div>
    </footer>
  )
}
