import { Link, useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, Image, KeyboardAvoidingView, Platform, Text, View } from 'react-native';

import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Screen } from '@/components/Screen';
import { describeApiError } from '@/lib/api';
import { useAuth } from '@/stores/auth';

export default function RegisterScreen() {
  const register = useAuth((s) => s.register);
  const router = useRouter();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    if (!firstName.trim() || !email || !password) {
      setError('Nombre, correo y contraseña son obligatorios.');
      return;
    }
    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await register({
        email: email.trim().toLowerCase(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim() || undefined,
        phone: phone.trim() || undefined,
      });
      Alert.alert(
        'Revisa tu correo',
        'Te enviamos un enlace de activación a tu correo. Ábrelo desde tu celular para activar tu cuenta. Una vez activada, regresa para iniciar sesión.',
        [{ text: 'Entendido', onPress: () => router.replace('/(auth)/login') }],
      );
    } catch (e) {
      setError(describeApiError(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen scroll>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} className="gap-6">
        <View className="items-center pt-2">
          <Image
            source={require('../../assets/brand/isotipo.png')}
            resizeMode="contain"
            style={{ width: 72, height: 64 }}
            accessibilityLabel="NexoSoftDev"
          />
        </View>
        <View className="gap-2">
          <Text className="text-2xl font-bold text-slate-900">Crea tu cuenta</Text>
          <Text className="text-base text-slate-500">
            Te enviaremos un correo para activar tu acceso.
          </Text>
        </View>

        <View className="gap-4">
          <Input label="Nombre" autoCapitalize="words" value={firstName} onChangeText={setFirstName} />
          <Input label="Apellido" autoCapitalize="words" value={lastName} onChangeText={setLastName} />
          <Input
            label="Correo"
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
            value={email}
            onChangeText={setEmail}
          />
          <Input
            label="Teléfono (opcional)"
            keyboardType="phone-pad"
            placeholder="+52 55 1234 5678"
            value={phone}
            onChangeText={setPhone}
          />
          <Input
            label="Contraseña"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            hint="Mínimo 8 caracteres."
            error={error ?? undefined}
          />
          <Button label="Crear cuenta" loading={submitting} onPress={onSubmit} fullWidth size="lg" />
        </View>

        <View className="flex-row items-center justify-center gap-1.5">
          <Text className="text-sm text-slate-600">¿Ya tienes cuenta?</Text>
          <Link href="/(auth)/login" className="text-sm font-semibold text-brand-600">
            Inicia sesión
          </Link>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}
