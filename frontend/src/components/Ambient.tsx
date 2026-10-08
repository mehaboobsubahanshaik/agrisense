import { useMemo } from 'react'

type Leaf = {
  left: string
  delay: string
  duration: string
  flutter: string
  scale: number
  opacity: number
  shape: number
  tint: string
}

/** Three silhouettes so the fall does not look like one sprite repeated. */
const SHAPES = [
  'M4 20c0-8 6-14 16-16 0 10-6 16-16 16z',                       // classic leaf
  'M12 2c5 4 7 9 5 14-2 4-6 6-10 5 0-8 2-14 5-19z',              // narrow blade
  'M12 21c-5-3-8-8-7-13 5-2 10 0 13 4 2 3 1 7-2 9-1 1-3 1-4 0z', // broad leaf
]

/**
 * Falling leaves.
 *
 * Two layers: a translateY drift on the wrapper and a translateX flutter on the
 * inner element, so leaves sway as they fall instead of dropping in a straight
 * line. The scale sits on a third element - putting it on the animated node
 * silently did nothing, because keyframe transforms override an inline one, which
 * is why the leaves used to render tiny and almost invisible.
 *
 * Switched off entirely for reduced-motion users by the global query in index.css.
 */
export function FloatingLeaves({ count = 16 }: { count?: number }) {
  const leaves = useMemo<Leaf[]>(
    () =>
      Array.from({ length: count }, (_, i) => ({
        left: `${(i * 61) % 96 + 2}%`,
        delay: `-${(i * 3.1) % 18}s`,          // negative: some are mid-fall on load
        duration: `${16 + (i % 6) * 4}s`,
        flutter: `${4 + (i % 4) * 1.5}s`,
        scale: 0.75 + (i % 5) * 0.22,
        opacity: 0.3 + (i % 4) * 0.07,
        shape: i % SHAPES.length,
        tint: ['text-leaf', 'text-leaf-light', 'text-leaf-dark', 'text-grain'][i % 4],
      })),
    [count]
  )

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {leaves.map((l, i) => (
        <span
          key={i}
          className="absolute top-0 block animate-drift"
          style={{ left: l.left, animationDelay: l.delay, animationDuration: l.duration }}
        >
          <span
            className="block animate-flutter"
            style={{ animationDuration: l.flutter, animationDelay: l.delay }}
          >
            <svg
              viewBox="0 0 24 24"
              className={`h-8 w-8 ${l.tint} drop-shadow-sm`}
              style={{ transform: `scale(${l.scale})`, opacity: l.opacity }}
            >
              <path fill="currentColor" d={SHAPES[l.shape]} />
              <path
                stroke="currentColor" strokeWidth="0.9" fill="none" opacity="0.55"
                d="M4 20C8 16 12 10 20 4"
              />
            </svg>
          </span>
        </span>
      ))}
    </div>
  )
}

/** Rain overlay shown on the weather card when rain is in the forecast. */
export function RainOverlay({ intensity = 12 }: { intensity?: number }) {
  const drops = Array.from({ length: intensity }, (_, i) => i)
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
      {drops.map((i) => (
        <span
          key={i}
          className="absolute top-0 block h-5 w-px animate-rain bg-white/60"
          style={{ left: `${(i * 100) / intensity + 2}%`, animationDelay: `${(i % 7) * 0.15}s` }}
        />
      ))}
    </div>
  )
}
