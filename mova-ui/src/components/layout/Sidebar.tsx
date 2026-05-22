import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore } from '@/stores/chatStore'
import { useUiStore } from '@/stores/uiStore'
import { cn, formatTime, truncate } from '@/lib/utils'
import {
  MessageSquarePlus,
  MessageSquareText,
  Trash2,
  PanelLeftClose,
  PanelLeft,
  Bus,
  History,
} from 'lucide-react'

export function Sidebar() {
  const {
    sessions,
    activeSessionId,
    createSession,
    deleteSession,
    setActiveSession,
  } = useChatStore()

  const { sidebarOpen, mobileNavOpen, toggleSidebar, setMobileNavOpen } =
    useUiStore()

  const isOpen = sidebarOpen || mobileNavOpen

  const handleNewChat = () => {
    createSession()
    if (mobileNavOpen) setMobileNavOpen(false)
  }

  const handleSelectSession = (id: string) => {
    setActiveSession(id)
    if (mobileNavOpen) setMobileNavOpen(false)
  }

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <>
          {/* Mobile overlay */}
          {mobileNavOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm lg:hidden"
              onClick={() => setMobileNavOpen(false)}
            />
          )}

          <motion.aside
            initial={mobileNavOpen ? { x: '-100%' } : { width: 0, opacity: 0 }}
            animate={
              mobileNavOpen
                ? { x: 0 }
                : { width: sidebarOpen ? 280 : 0, opacity: 1 }
            }
            exit={
              mobileNavOpen
                ? { x: '-100%' }
                : { width: 0, opacity: 0 }
            }
            transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
            className={cn(
              'flex flex-col h-full bg-sidebar border-r border-sidebar-border shrink-0 overflow-hidden',
              mobileNavOpen &&
                'fixed left-0 top-0 z-50 w-[280px] lg:relative lg:z-auto',
            )}
          >
            {/* Sidebar header */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-sidebar-border shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Bus className="w-4 h-4 text-primary" />
                </div>
                <span className="font-semibold text-sm">MOVA</span>
              </div>
              <button
                onClick={toggleSidebar}
                className="w-7 h-7 rounded-lg hover:bg-muted flex items-center justify-center transition-colors lg:flex hidden"
              >
                <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
              </button>
              <button
                onClick={() => setMobileNavOpen(false)}
                className="w-7 h-7 rounded-lg hover:bg-muted flex items-center justify-center transition-colors lg:hidden"
              >
                <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>

            {/* New chat button */}
            <div className="px-3 pt-3 pb-2 shrink-0">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 text-sm font-medium shadow-sm active:scale-[0.98]"
              >
                <MessageSquarePlus className="w-4 h-4" />
                New conversation
              </button>
            </div>

            {/* Session list */}
            <div className="flex-1 overflow-y-auto scrollbar-thin px-2 py-2 space-y-0.5">
              {sessions.length === 0 && (
                <div className="flex flex-col items-center justify-center py-12 text-center px-4">
                  <History className="w-8 h-8 text-muted-foreground/30 mb-3" />
                  <p className="text-xs text-muted-foreground/50">
                    No conversations yet
                  </p>
                </div>
              )}

              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={cn(
                    'group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-200 text-sm',
                    session.id === activeSessionId
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-sidebar-foreground hover:bg-muted/60',
                  )}
                  onClick={() => handleSelectSession(session.id)}
                >
                  <MessageSquareText className="w-4 h-4 shrink-0 opacity-60" />
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm">
                      {truncate(session.title, 28)}
                    </p>
                    <p className="text-[11px] text-muted-foreground/50 mt-0.5">
                      {formatTime(session.updatedAt)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteSession(session.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 w-6 h-6 rounded-lg hover:bg-destructive/10 flex items-center justify-center transition-all duration-200"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-destructive/60 hover:text-destructive" />
                  </button>
                </div>
              ))}
            </div>

            {/* Sidebar footer */}
            <div className="px-4 py-3 border-t border-sidebar-border shrink-0">
              <p className="text-[11px] text-muted-foreground/40 text-center">
                MOVA · Transport &amp; Mobility AI
              </p>
            </div>
          </motion.aside>
        </>
      )}

      {/* Collapsed trigger */}
      {!isOpen && (
        <button
          onClick={toggleSidebar}
          className="absolute top-4 left-4 z-30 w-9 h-9 rounded-xl bg-background border shadow-sm hover:bg-muted flex items-center justify-center transition-all duration-200"
        >
          <PanelLeft className="w-4 h-4 text-muted-foreground" />
        </button>
      )}
    </AnimatePresence>
  )
}
