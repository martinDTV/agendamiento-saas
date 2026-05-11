export function useApi() {
  const { $api } = useNuxtApp()

  async function apiFetch<T>(path: string, options: {
    method?: string
    body?: unknown
    params?: Record<string, unknown>
  } = {}): Promise<T> {
    const { method = 'GET', body, params } = options
    const res = await $api.request<T>({
      url: path,
      method,
      data: body,
      params
    })
    return res.data
  }

  return { apiFetch }
}
