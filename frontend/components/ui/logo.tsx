"use client"

import React from 'react'

interface LogoProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function Logo({ className = '', size = 'md' }: LogoProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8', 
    lg: 'w-12 h-12'
  }
  
  return (
    <img 
      src="/logo.png" 
      alt="Craefto Automation" 
      className={`${sizeClasses[size]} object-contain ${className}`}
    />
  )
}

// Alternative implementations you can use:

// For image logo:
// export function Logo({ className = '', size = 'md' }: LogoProps) {
//   const sizeClasses = {
//     sm: 'w-6 h-6',
//     md: 'w-8 h-8', 
//     lg: 'w-12 h-12'
//   }
//   
//   return (
//     <img 
//       src="/logo.png" 
//       alt="Craefto Automation" 
//       className={`${sizeClasses[size]} ${className}`}
//     />
//   )
// }

// For SVG logo:
// export function Logo({ className = '', size = 'md' }: LogoProps) {
//   const sizeClasses = {
//     sm: 'w-6 h-6',
//     md: 'w-8 h-8', 
//     lg: 'w-12 h-12'
//   }
//   
//   return (
//     <svg 
//       className={`${sizeClasses[size]} ${className}`} 
//       viewBox="0 0 24 24" 
//       fill="currentColor"
//     >
//       {/* Your SVG path here */}
//       <path d="..." />
//     </svg>
//   )
// }
