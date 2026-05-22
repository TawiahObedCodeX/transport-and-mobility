import { create } from 'zustand'

interface UiState {
  sidebarOpen: boolean
  mobileNavOpen: boolean
  mounted: boolean

  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setMobileNavOpen: (open: boolean) => void
  setMounted: (mounted: boolean) => void
}

export const useUiStore = create<UiState>()((set) => ({
  sidebarOpen: true,
  mobileNavOpen: false,
  mounted: false,

  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),

  setMobileNavOpen: (open: boolean) => set({ mobileNavOpen: open }),

  setMounted: (mounted: boolean) => set({ mounted }),
}))
