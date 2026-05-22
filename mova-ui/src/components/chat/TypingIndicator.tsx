import { motion } from 'framer-motion'

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="flex items-start gap-3 px-4 py-2"
    >
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
        <span className="text-xs">🚌</span>
      </div>
      <div className="flex items-center gap-1 bg-muted/50 rounded-2xl rounded-tl-sm px-4 py-3 border">
        <motion.span
          className="w-2 h-2 bg-primary/60 rounded-full"
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0 }}
        />
        <motion.span
          className="w-2 h-2 bg-primary/60 rounded-full"
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0.15 }}
        />
        <motion.span
          className="w-2 h-2 bg-primary/60 rounded-full"
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0.3 }}
        />
      </div>
    </motion.div>
  )
}
