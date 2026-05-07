import { useState } from 'react'

export default function ProductCard({ product }) {
  const {
    title = 'Untitled Product',
    image,
    images = [],
    price,
    vendor,
    available_sizes = [],
    link,
  } = product

  const [currentImgIndex, setCurrentImgIndex] = useState(0)
  const displayImages = images.length > 0 ? images : (image ? [image] : ['https://via.placeholder.com/400x400?text=No+Image'])

  const handleNext = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setCurrentImgIndex((prev) => (prev + 1) % displayImages.length)
  }

  const handlePrev = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setCurrentImgIndex((prev) => (prev - 1 + displayImages.length) % displayImages.length)
  }

  return (
    <a
      href={link || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="bg-white rounded-2xl border-2 border-outline-variant/30 overflow-hidden flex flex-col hover:border-primary/40 hover:shadow-2xl hover:shadow-primary/15 transition-all duration-300 group hover:-translate-y-2 cursor-pointer block relative"
    >
      <div className="h-64 relative overflow-hidden border-b-2 border-outline-variant/20 bg-gradient-to-br from-surface-container-lowest to-surface-container-low group/carousel">
        <img
          src={displayImages[currentImgIndex]}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
        
        {displayImages.length > 1 && (
          <>
            <button 
              onClick={handlePrev}
              className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 backdrop-blur-sm p-1.5 rounded-full text-neutral-800 opacity-60 group-hover/carousel:opacity-100 hover:bg-white transition-all shadow-sm z-10"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_left</span>
            </button>
            <button 
              onClick={handleNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 backdrop-blur-sm p-1.5 rounded-full text-neutral-800 opacity-60 group-hover/carousel:opacity-100 hover:bg-white transition-all shadow-sm z-10"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
            <div className="absolute bottom-3 left-0 right-0 flex justify-center gap-1.5 z-10 opacity-60 group-hover/carousel:opacity-100 transition-opacity">
              {displayImages.map((_, idx) => (
                <div 
                  key={idx} 
                  className={`h-1.5 rounded-full transition-all ${idx === currentImgIndex ? 'w-4 bg-white' : 'w-1.5 bg-white/50'}`}
                />
              ))}
            </div>
          </>
        )}

        {available_sizes.length > 0 && (
          <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm px-3 py-2 rounded-lg text-label-sm font-bold uppercase tracking-wider text-primary shadow-lg border-2 border-primary/20 z-10 pointer-events-none">
            {available_sizes.length} sizes
          </div>
        )}
      </div>
      <div className="p-6 flex flex-col gap-4 flex-grow">
        <div>
          <h4 className="font-h3 text-body-lg text-on-surface line-clamp-2 group-hover:text-primary transition-colors">{title}</h4>
          <p className="text-body-sm text-secondary mt-2">{vendor || 'Shopify Store'}</p>
        </div>
        <div className="flex items-center justify-between pt-4 border-t-2 border-outline-variant/20">
          <span className="font-h2 text-h3 text-primary font-bold">
            {price !== undefined && price !== null ? `$${Number(price).toFixed(2)}` : ''}
          </span>
          <span className="text-primary-container group-hover:text-primary transition-colors text-2xl">
            <span className="material-symbols-outlined">arrow_outward</span>
          </span>
        </div>
      </div>
    </a>
  )
}
