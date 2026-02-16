import React from 'react';

export function PuzzleIcon({ className }: { className?: string }) {
  return (
    <svg 
      viewBox="0 0 100 100" 
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* 4-Piece Puzzle Logic */}
      
      {/* Top Left: Yellow Piece */}
      <path d="M10 10 H50 V30 A10 10 0 0 1 50 50 V50 H30 A10 10 0 0 0 10 50 V10" fill="#F4D03F" />

      {/* Top Right: Blue Piece */}
      <path d="M50 10 H90 V50 H70 A10 10 0 0 1 50 50 V30 A10 10 0 0 0 50 10" fill="#3498DB" />

      {/* Bottom Right: Red Piece */}
      <path d="M50 50 H70 A10 10 0 0 0 90 50 V90 H50 V70 A10 10 0 0 1 50 50" fill="#E74C3C" />

      {/* Bottom Left: Green Piece */}
      <path d="M10 50 H30 A10 10 0 0 1 50 50 V90 H10 V50" fill="#2ECC71" />
      
      {/* Center detail */}
      <circle cx="50" cy="50" r="4" fill="rgba(0,0,0,0.1)" />
      
      {/* Border outline for clarity */}
      <path d="M10 10 H90 V90 H10 Z" stroke="rgba(255,255,255,0.2)" strokeWidth="2" fill="none" rx="4" />
    </svg>
  );
}
