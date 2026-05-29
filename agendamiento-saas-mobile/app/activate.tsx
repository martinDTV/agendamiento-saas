/**
 * Pantalla de activación de cuenta — se abre desde el deep-link del email:
 *   agendamiento://activate?token=<uuid>
 *
 * Configurada en app.json con `"scheme": "agendamiento"`.
 */
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';

import { Button } from '@/components/Button';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { activatePatient } from '@/lib/queries';

export default function ActivateScreen() {
  const { token } = useLocalSearchParams<{ token?: string }>();
  const router = useRouter();
  const [state, setState] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    if (!token) {
      setState('error');
      setMessage('Falta el token de activación en el enlace.');
      return;
    }
    (async () => {
      try {
        const res = await activatePatient({ token });
        setMessage(res.email);
        setState('success');
      } catch (e) {
        setMessage(describeApiError(e));
        setState('error');
      }
    })();
  }, [token]);

  return (
    <Screen scroll={false}>
      <View className="flex-1 items-center justify-center px-6 gap-6">
        {state === 'loading' ? (
          <>
            <ActivityIndicator size="large" color={COLORS.brand} />
            <Text className="text-base text-slate-600">Activando tu cuenta…</Text>
          </>
        ) : state === 'success' ? (
          <>
            <View className="size-24 items-center justify-center rounded-full bg-emerald-100">
              <Ionicons name="checkmark-circle" size={64} color="#10B981" />
            </View>
            <View className="items-center gap-2">
              <Text className="text-2xl font-bold text-slate-900">Cuenta activada</Text>
              <Text className="text-center text-base text-slate-500">
                Tu cuenta <Text className="font-semibold">{message}</Text> está lista. Inicia sesión para empezar.
              </Text>
            </View>
            <Button
              label="Iniciar sesión"
              size="lg"
              fullWidth
              onPress={() => router.replace('/(auth)/login')}
            />
          </>
        ) : (
          <>
            <View className="size-24 items-center justify-center rounded-full bg-red-100">
              <Ionicons name="alert-circle" size={64} color="#DC2626" />
            </View>
            <View className="items-center gap-2">
              <Text className="text-2xl font-bold text-slate-900">No pudimos activar</Text>
              <Text className="text-center text-base text-slate-500">{message}</Text>
            </View>
            <Button
              label="Volver al inicio"
              variant="ghost"
              fullWidth
              onPress={() => router.replace('/(auth)/login')}
            />
          </>
        )}
      </View>
    </Screen>
  );
}
