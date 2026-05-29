import { Redirect } from 'expo-router';

import { useAuth } from '@/stores/auth';

export default function Index() {
  const status = useAuth((s) => s.status);
  if (status === 'loading') return null;
  return status === 'authenticated' ? <Redirect href="/(tabs)" /> : <Redirect href="/(auth)/login" />;
}
