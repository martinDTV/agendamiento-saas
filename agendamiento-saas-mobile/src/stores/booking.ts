import { create } from 'zustand';

/**
 * Estado del wizard de reserva. Sobrevive a navegación entre pantallas
 * pero se resetea al confirmar o al salir del flujo (`reset()`).
 */

interface BookingDraft {
  // IDs son UUID strings — los modelos del backend usan UUIDField como PK.
  doctorId: string | null;
  serviceId: string | null;
  date: string | null; // YYYY-MM-DD
  startTime: string | null; // HH:mm
  patientName: string;
  patientEmail: string;
  patientPhone: string;
  notes: string;
}

const empty: BookingDraft = {
  doctorId: null,
  serviceId: null,
  date: null,
  startTime: null,
  patientName: '',
  patientEmail: '',
  patientPhone: '',
  notes: '',
};

interface BookingState extends BookingDraft {
  set: (patch: Partial<BookingDraft>) => void;
  reset: () => void;
}

export const useBooking = create<BookingState>((set) => ({
  ...empty,
  set: (patch) => set((s) => ({ ...s, ...patch })),
  reset: () => set({ ...empty }),
}));
