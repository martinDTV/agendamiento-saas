export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  auth.hydrate()
  // Await so the user object is populated before any middleware or page renders
  if (auth.access && !auth.user) {
    await auth.fetchMe()
  }
})
