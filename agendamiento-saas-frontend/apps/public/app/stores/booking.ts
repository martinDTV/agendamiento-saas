import { defineStore } from 'pinia'
import type { Doctor, Service, Slot } from '@agendamiento/shared'

interface BookingState {
  step: 1 | 2 | 3
  service: Service | null
  doctor: Doctor | null
  date: string | null
  slot: Slot | null
  patientName: string
  patientEmail: string
  patientPhone: string
  appointmentId: string | null
}

export const useBookingStore = defineStore('booking', {
  state: (): BookingState => ({
    step: 1,
    service: null,
    doctor: null,
    date: null,
    slot: null,
    patientName: '',
    patientEmail: '',
    patientPhone: '',
    appointmentId: null
  }),

  getters: {
    canGoToStep2: state => !!state.service && !!state.doctor && !!state.date && !!state.slot,
    canConfirm: state => !!state.patientName && !!state.patientEmail
  },

  actions: {
    selectService(service: Service) {
      // Cambiar de servicio invalida doctor/slot si el doctor no ofrece el nuevo servicio.
      if (this.doctor && !service.doctor_ids?.includes(this.doctor.id)) {
        this.doctor = null
      }
      this.service = service
      this.slot = null
    },
    selectDoctor(doctor: Doctor) { this.doctor = doctor; this.slot = null },
    selectDate(date: string) { this.date = date; this.slot = null },
    selectSlot(slot: Slot) { this.slot = slot },

    goTo(step: 1 | 2 | 3) { this.step = step },

    reset() {
      this.$patch({
        step: 1, service: null, doctor: null, date: null, slot: null,
        patientName: '', patientEmail: '', patientPhone: '', appointmentId: null
      })
    }
  }
})
