import { useEffect, useRef } from 'react'

export function useAutoScroll(deps: unknown[]) {
  const containerRef = useRef<HTMLDivElement>(null)
  const shouldAutoScroll = useRef(true)

  useEffect(() => {
    if (shouldAutoScroll.current) {
      containerRef.current?.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, deps)

  const handleScroll = () => {
    const el = containerRef.current
    if (!el) return
    const threshold = 100
    shouldAutoScroll.current =
      el.scrollHeight - el.scrollTop - el.clientHeight < threshold
  }

  return { containerRef, handleScroll }
}
