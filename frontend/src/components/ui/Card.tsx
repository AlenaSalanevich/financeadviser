import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
}

export function Card({ children, className = '', title }: CardProps) {
  return (
    <div className={`rounded-xl bg-white shadow-sm border border-slate-200 ${className}`}>
      {title && (
        <div className="border-b border-slate-100 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-800">{title}</h2>
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}
