export default defineNuxtPlugin(async () => {
  const auth = usePlatformAuthStore()
  auth.hydrate()
  if (auth.access && !auth.user) {
    await auth.fetchMe()
  }
})
