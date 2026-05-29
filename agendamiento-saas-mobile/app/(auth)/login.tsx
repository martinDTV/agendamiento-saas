import { Link, useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, Image, KeyboardAvoidingView, Platform, Text, View } from 'react-native';

import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Screen } from '@/components/Screen';
import { describeApiError } from '@/lib/api';
import { useAuth } from '@/stores/auth';

export default function LoginScreen() {
  const router = useRouter();
  const login = useAuth((s) => s.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    if (!email || !password) {
      setError('Ingresa tu correo y contraseña.');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await login({ email: email.trim().toLowerCase(), password });
      router.replace('/(tabs)');
    } catch (e) {
      setError(describeApiError(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen scroll={false}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        className="flex-1 px-5 pt-8"
      >
        <View className="flex-1 justify-center gap-6">
          <View className="items-center gap-3">
            <Image
              source={require('../../assets/brand/logo.png')}
              resizeMode="contain"
              style={{ width: 220, height: 80 }}
              accessibilityLabel="NexoSoftDev"
            />
            <Text className="text-3xl font-bold text-slate-900">Bienvenido</Text>
            <Text className="text-center text-base text-slate-500">
              Agenda tus citas médicas en segundos.
            </Text>
          </View>

          <View className="gap-4">
            <Input
              label="Correo"
              autoCapitalize="none"
              autoComplete="email"
              keyboardType="email-address"
              placeholder="tu@correo.com"
              value={email}
              onChangeText={setEmail}
              returnKeyType="next"
            />
            <Input
              label="Contraseña"
              secureTextEntry
              autoComplete="password"
              placeholder="••••••••"
              value={password}
              onChangeText={setPassword}
              returnKeyType="done"
              onSubmitEditing={onSubmit}
              error={error ?? undefined}
            />
            <Button label="Iniciar sesión" loading={submitting} onPress={onSubmit} fullWidth size="lg" />
          </View>

          <View className="flex-row items-center justify-center gap-1.5">
            <Text className="text-sm text-slate-600">¿No tienes cuenta?</Text>
            <Link href="/(auth)/register" className="text-sm font-semibold text-brand-600">
              Regístrate
            </Link>
          </View>

          <Text
            onPress={() => Alert.alert('Modo invitado', 'Próximamente podrás reservar sin cuenta.')}
            className="text-center text-sm text-slate-400 underline"
          >
            Continuar como invitado
          </Text>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}
