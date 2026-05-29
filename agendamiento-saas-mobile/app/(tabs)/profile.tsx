import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
import { ActivityIndicator, Alert, Linking, Text, View } from 'react-native';

import { Button } from '@/components/Button';
import { Card, PressableCard } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { ENV } from '@/config/env';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { fetchMyProfile } from '@/lib/queries';
import { useAuth } from '@/stores/auth';

/**
 * Pantalla de perfil del paciente.
 *
 * Estructura:
 *   1. Avatar + nombre + email
 *   2. Resumen clínico (teléfono, tipo sangre, alergias) — datos del Patient
 *   3. CTA Editar perfil
 *   4. Sección Ayuda (Términos, Privacidad, Contacto, Versión)
 *   5. (solo en __DEV__) Info técnica (tenant slug, URL del backend) para debugging
 *   6. Cerrar sesión
 */

// URLs placeholder hasta que tengas dominio/páginas legales reales.
// Cuando NexoSoftDev tenga sitio público estos pasan a `https://nexosoftdev.com/...`.
const HELP_LINKS = {
  terms: 'https://nexosoftdev.com/terminos',
  privacy: 'https://nexosoftdev.com/privacidad',
  support: 'mailto:soporte@nexosoftdev.com',
};

const APP_VERSION = (Constants.expoConfig?.version as string | undefined) ?? '0.1.0';

export default function ProfileScreen() {
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  const profile = useQuery({
    queryKey: ['my-profile'],
    queryFn: fetchMyProfile,
    retry: false,
  });

  function onLogout() {
    Alert.alert('Cerrar sesión', '¿Seguro que quieres salir?', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Cerrar sesión', style: 'destructive', onPress: () => logout() },
    ]);
  }

  async function openLink(url: string) {
    const ok = await Linking.canOpenURL(url);
    if (ok) {
      Linking.openURL(url);
    } else {
      Alert.alert('No disponible', 'Pronto tendremos esta sección lista.');
    }
  }

  const fullName =
    profile.data?.full_name ||
    (user ? `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim() || user.email : 'Tu perfil');

  return (
    <Screen>
      {/* ── Avatar + identidad ──────────────────────────────────────────── */}
      <View className="items-center gap-3 pt-4">
        <View className="size-20 items-center justify-center rounded-full bg-brand-100">
          <Ionicons name="person" size={36} color={COLORS.brand} />
        </View>
        <Text className="text-xl font-bold text-slate-900">{fullName}</Text>
        {profile.data?.email ? (
          <Text className="text-sm text-slate-500">{profile.data.email}</Text>
        ) : user?.email ? (
          <Text className="text-sm text-slate-500">{user.email}</Text>
        ) : null}
      </View>

      {/* ── Resumen clínico ─────────────────────────────────────────────── */}
      {profile.isLoading ? (
        <View className="py-8 items-center">
          <ActivityIndicator color={COLORS.brand} />
        </View>
      ) : profile.isError ? (
        <Card className="border-amber-100 bg-amber-50">
          <Text className="text-sm text-amber-800">
            No pudimos cargar tu perfil clínico. {describeApiError(profile.error)}
          </Text>
        </Card>
      ) : profile.data ? (
        <Card className="gap-3">
          <Row icon="call-outline" label="Teléfono" value={profile.data.phone || '—'} />
          <Row
            icon="water-outline"
            label="Tipo de sangre"
            value={profile.data.blood_type || 'Sin especificar'}
          />
          <Row
            icon="alert-circle-outline"
            label="Alergias"
            value={profile.data.allergies || 'Sin especificar'}
          />
        </Card>
      ) : null}

      {/* ── Editar perfil ───────────────────────────────────────────────── */}
      <PressableCard onPress={() => router.push('/profile/edit')}>
        <View className="flex-row items-center gap-3">
          <Ionicons name="create-outline" size={22} color={COLORS.brand} />
          <Text className="flex-1 text-base font-medium text-slate-800">Editar perfil</Text>
          <Ionicons name="chevron-forward" size={20} color="#94A3B8" />
        </View>
      </PressableCard>

      {/* ── Ayuda ───────────────────────────────────────────────────────── */}
      <View className="gap-2">
        <Text className="px-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Ayuda
        </Text>
        <Card className="gap-0 p-0 overflow-hidden">
          <LinkRow
            icon="help-circle-outline"
            label="Contactar soporte"
            onPress={() => openLink(HELP_LINKS.support)}
          />
          <Separator />
          <LinkRow
            icon="document-text-outline"
            label="Términos y condiciones"
            onPress={() => openLink(HELP_LINKS.terms)}
          />
          <Separator />
          <LinkRow
            icon="shield-checkmark-outline"
            label="Política de privacidad"
            onPress={() => openLink(HELP_LINKS.privacy)}
          />
          <Separator />
          <View className="flex-row items-center gap-3 px-4 py-3.5">
            <Ionicons name="information-circle-outline" size={20} color={COLORS.brand} />
            <Text className="flex-1 text-base text-slate-800">Versión</Text>
            <Text className="text-sm text-slate-500">{APP_VERSION}</Text>
          </View>
        </Card>
      </View>

      {/* ── Info técnica (solo en desarrollo) ───────────────────────────── */}
      {__DEV__ ? (
        <View className="gap-2">
          <Text className="px-1 text-xs font-semibold uppercase tracking-wider text-amber-600">
            Debug (solo dev)
          </Text>
          <Card className="gap-3 border-amber-200 bg-amber-50">
            {/* La app es cross-clínica ahora, así que NO hay "tenant activo"
                — el paciente ve doctores de TODAS las clínicas. */}
            <Row icon="server-outline" label="Backend" value={ENV.apiBaseUrl} />
            <Row icon="globe-outline" label="Modo" value="Cross-clínica" />
          </Card>
        </View>
      ) : null}

      {/* ── Cerrar sesión ───────────────────────────────────────────────── */}
      <Button label="Cerrar sesión" variant="danger" onPress={onLogout} fullWidth />
    </Screen>
  );
}

// ── Sub-componentes ────────────────────────────────────────────────────────

function Row({
  icon,
  label,
  value,
}: {
  icon: keyof typeof import('@expo/vector-icons/build/Ionicons').default.glyphMap;
  label: string;
  value: string;
}) {
  return (
    <View className="flex-row items-center gap-3">
      <Ionicons name={icon} size={20} color={COLORS.brand} />
      <View className="flex-1">
        <Text className="text-xs text-slate-500">{label}</Text>
        <Text className="text-sm font-medium text-slate-800">{value}</Text>
      </View>
    </View>
  );
}

function LinkRow({
  icon,
  label,
  onPress,
}: {
  icon: keyof typeof import('@expo/vector-icons/build/Ionicons').default.glyphMap;
  label: string;
  onPress: () => void;
}) {
  return (
    <PressableCard
      onPress={onPress}
      className="rounded-none border-0 bg-transparent p-0 active:bg-slate-100"
    >
      <View className="flex-row items-center gap-3 px-4 py-3.5">
        <Ionicons name={icon} size={20} color={COLORS.brand} />
        <Text className="flex-1 text-base text-slate-800">{label}</Text>
        <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
      </View>
    </PressableCard>
  );
}

function Separator() {
  return <View className="h-px bg-slate-100 mx-4" />;
}
