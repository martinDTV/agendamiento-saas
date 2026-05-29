import '../global.css';

import { Stack, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { QueryProvider } from '@/providers/QueryProvider';
import { useAuth } from '@/stores/auth';

SplashScreen.preventAutoHideAsync().catch(() => {});

function AuthGate() {
  const status = useAuth((s) => s.status);
  const bootstrap = useAuth((s) => s.bootstrap);
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    bootstrap().finally(() => SplashScreen.hideAsync().catch(() => {}));
  }, [bootstrap]);

  useEffect(() => {
    if (status === 'loading') return;
    const inAuth = segments[0] === '(auth)';
    // La pantalla de activación (deep-link desde el email) es accesible sin
    // auth — no la mandamos al login.
    const inActivate = segments[0] === 'activate';
    if (status === 'guest' && !inAuth && !inActivate) {
      router.replace('/(auth)/login');
    } else if (status === 'authenticated' && inAuth) {
      router.replace('/(tabs)');
    }
  }, [status, segments, router]);

  return null;
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryProvider>
          <AuthGate />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(tabs)" />
            <Stack.Screen
              name="doctor/[id]"
              options={{ headerShown: true, title: 'Doctor', headerBackTitle: 'Atrás' }}
            />
            <Stack.Screen
              name="booking/select-service"
              options={{ headerShown: true, title: 'Servicio', headerBackTitle: 'Atrás' }}
            />
            <Stack.Screen
              name="booking/select-slot"
              options={{ headerShown: true, title: 'Fecha y hora', headerBackTitle: 'Atrás' }}
            />
            <Stack.Screen
              name="booking/confirm"
              options={{ headerShown: true, title: 'Confirmar', headerBackTitle: 'Atrás' }}
            />
            <Stack.Screen
              name="booking/success"
              options={{ headerShown: false, gestureEnabled: false }}
            />
            <Stack.Screen
              name="activate"
              options={{ headerShown: false, gestureEnabled: false }}
            />
            <Stack.Screen
              name="profile/edit"
              options={{ headerShown: true, title: 'Editar perfil', headerBackTitle: 'Atrás' }}
            />
            <Stack.Screen
              name="appointment/[id]"
              options={{ headerShown: true, title: 'Detalle de cita', headerBackTitle: 'Atrás' }}
            />
            <Stack.Screen
              name="appointment/reschedule"
              options={{ headerShown: true, title: 'Reagendar', headerBackTitle: 'Atrás' }}
            />
            <Stack.Screen
              name="doctor/review"
              options={{ headerShown: true, title: 'Dejar reseña', headerBackTitle: 'Atrás' }}
            />
          </Stack>
          <StatusBar style="dark" />
        </QueryProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
