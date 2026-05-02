export default function ProductCard({ product }) {
  const {
    title = 'Untitled Product',
    image,
    price,
    vendor,
    available_sizes = [],
    link,
  } = product

  return (
    <div className="bg-white rounded-lg border border-outline-variant/20 overflow-hidden flex flex-col hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.08)] transition-shadow group">
      <div className="h-64 relative overflow-hidden border-b border-outline-variant/20">
        <img
          src={image || 'https://via.placeholder.com/400x400?text=No+Image'}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        {available_sizes.length > 0 && (
          <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm px-2 py-1 rounded text-label-sm font-bold uppercase tracking-wider text-primary">
            {available_sizes.length} sizes
          </div>
        )}
      </div>
      <div className="p-6 flex flex-col gap-4 flex-grow">
        <div>
          <h4 className="font-h3 text-body-lg text-on-surface line-clamp-1">{title}</h4>
          <p className="text-body-sm text-secondary mt-1">{vendor || 'Shopify Store'}</p>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-h2 text-h2 text-primary">
            {price !== undefined && price !== null ? `$${Number(price).toFixed(2)}` : ''}
          </span>
          <a
            href={link || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-surface-container-low text-on-surface px-4 py-2 rounded-lg font-label-md hover:bg-secondary-container transition-colors active:scale-95"
          >
            View Product
          </a>
        </div>
      </div>
    </div>
  )
}
