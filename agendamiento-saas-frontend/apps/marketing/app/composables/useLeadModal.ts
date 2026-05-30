/**
 * Shared state for the lead/contact modal.
 *
 * Any component can call `openLead('profesional')` to open the modal with a
 * preselected plan. The modal itself (LeadModal.vue, mounted once in app.vue)
 * reads this state.
 */
const isOpen = ref(false)
const selectedPlan = ref('')

export function useLeadModal() {
  const open = (plan = '') => {
    selectedPlan.value = plan
    isOpen.value = true
  }
  const close = () => {
    isOpen.value = false
  }
  return { isOpen, selectedPlan, open, close }
}
