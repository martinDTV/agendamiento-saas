import { Ionicons } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, Text, View } from 'react-native';

import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { formatLongDate, formatTime } from '@/lib/format';
import { createAppointment, fetchMyProfile } from '@/lib/queries';
import { useAuth } from '@/stores/auth';
import { useBooking } from '@/stores/booking';

/**
 * Pantalla de confirmación de reserva — versión con dos modos:
 *
 * Modo "Para mí" (default si estás logueado):
 *   Muestra un card con tus datos del perfil pre-llenados. Solo bot�n
 *   "Confirmar reserva". Opcional: toggle "Usar otro correo" si quieres que
 *   los recordatorios lleguen a otra dirección distinta a la de tu cuenta.
 *
 * Modo "Para alguien más":
 *   Despliega el formulario completo (nombre, correo, teléfono del paciente
 *   real). Útil para reservar la cita de un hijo/padre.
 *
 * Si NO estás logueado (booking público anónimo), siempre muestra el
 * formulario completo (no hay datos para pre-llenar).
 */
export default function ConfirmBookingScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useAuth((s) => s.user);
  const isAuthenticated = !!user;
  const booking = useBooking();

  // Cargamos el perfil del paciente para tener el teléfono normalizado y
  // todos los datos de contacto. Solo si está logueado.
  const profileQuery = useQuery({
    queryKey: ['my-profile'],
    queryFn: fetchMyProfile,
    enabled: isAuthenticated,
    retry: false,
  });
  const profile = profileQuery.data;

  // Estado de UI: ¿reservo para mí (modo "self") o para alguien más?
  const [mode, setMode] = useState<'self' | 'other'>(isAuthenticated ? 'self' : 'other');
  // Toggle del correo alternativo cuando reservas para ti
  const [useAltEmail, setUseAltEmail] = useState(false);
  const [altEmail, setAltEmail] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Pre-llenar el booking store con datos del perfil cuando lleguen
  useEffect(() => {
    if (!isAuthenticated || !profile) return;
    booking.set({
      patientName: profile.full_name || `${profile.first_name} ${profile.last_name}`.trim() || profile.email,
      patientEmail: profile.email,
      patientPhone: profile.phone || '',
    });
  }, [isAuthenticated, profile?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const mutation = useMutation({
    mutationFn: createAppointment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-appointments'] });
      router.replace('/booking/success');
    },
    onError: (e) => setError(describeApiError(e)),
  });

  function onSubmit() {
    setError(null);
    if (!booking.doctorId || !booking.serviceId || !booking.date || !booking.startTime) {
      setError('Faltan datos de la reserva.');
      return;
    }

    // Construir payload según el modo
    let patientName: string;
    let patientEmail: string;
    let patientPhone: string;

    if (mode === 'self' && profile) {
      // Para mí: usar datos del perfil. Correo opcional alternativo.
      patientName =
        profile.full_name || `${profile.first_name} ${profile.last_name}`.trim() || profile.email;
      patientEmail = useAltEmail && altEmail.trim() ? altEmail.trim().toLowerCase() : profile.email;
      patientPhone = profile.phone || '';
      if (!patientPhone) {
        setError('Tu perfil no tiene teléfono. Agrégalo desde Perfil → Editar perfil.');
        return;
      }
    } else {
      // Para alguien más / anónimo: usar campos del formulario
      patientName = booking.patientName.trim();
      patientEmail = booking.patientEmail.trim().toLowerCase();
      patientPhone = booking.patientPhone.trim();
      if (!patientName || !patientEmail || !patientPhone) {
        setError('Completa nombre, correo y teléfono.');
        return;
      }
    }

    mutation.mutate({
      doctor: booking.doctorId,
      service: booking.serviceId,
      date: booking.date,
      start_time: booking.startTime,
      patient_name: patientName,
      patient_email: patientEmail,
      patient_phone: patientPhone,
      notes: booking.notes.trim() || undefined,
    });
  }

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} className="gap-5">
        {/* ── Resumen de la cita ─────────────────────────────────────── */}
        <Card className="gap-2">
          <Text className="text-sm font-semibold text-slate-800">Resumen</Text>
          <SummaryRow icon="calendar" text={booking.date ? formatLongDate(booking.date) : '—'} />
          <SummaryRow icon="time-outline" text={booking.startTime ? formatTime(booking.startTime) : '—'} />
        </Card>

        {/* ── Modo self (paciente logueado, reservando para sí) ──────── */}
        {mode === 'self' && profile ? (
          <View className="gap-3">
            <Text className="text-sm font-semibold text-slate-800">¿Quién asistirá a la cita?</Text>
            <Card className="gap-3">
              <View className="flex-row items-start gap-3">
                <View className="size-10 items-center justify-center rounded-full bg-brand-100">
                  <Ionicons name="person" size={20} color={COLORS.brand} />
                </View>
                <View className="flex-1 gap-1">
                  <Text className="text-base font-semibold text-slate-900">
                    {profile.full_name ||
                      `${profile.first_name} ${profile.last_name}`.trim() ||
                      profile.email}
                  </Text>
                  <Text className="text-sm text-slate-500">{profile.email}</Text>
                  {profile.phone ? (
                    <Text className="text-sm text-slate-500">{profile.phone}</Text>
                  ) : (
                    <Text className="text-sm text-amber-700">
                      ⚠ Falta tu teléfono — agrégalo en Perfil
                    </Text>
                  )}
                </View>
              </View>
            </Card>

            {/* Correo alternativo */}
            <Pressable
              onPress={() => setUseAltEmail((v) => !v)}
              className="flex-row items-center gap-2 px-1"
            >
              <Ionicons
                name={useAltEmail ? 'checkbox' : 'square-outline'}
                size={20}
                color={COLORS.brand}
              />
              <Text className="text-sm text-slate-700">
                Enviar confirmación a otro correo
              </Text>
            </Pressable>
            {useAltEmail ? (
              <Input
                label="Correo alternativo"
                value={altEmail}
                onChangeText={setAltEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                placeholder="contacto@correo.com"
              />
            ) : null}

            {/* Notas */}
            <Input
              label="Notas para el doctor (opcional)"
              value={booking.notes}
              onChangeText={(v) => booking.set({ notes: v })}
              multiline
              numberOfLines={3}
              placeholder="Motivo de consulta, alergias…"
            />

            {/* Cambiar a modo "para alguien más" */}
            <Pressable onPress={() => setMode('other')} className="items-center pt-1">
              <Text className="text-sm font-medium text-brand-700">
                Reservar para alguien más →
              </Text>
            </Pressable>
          </View>
        ) : (
          /* ── Modo other (paciente anónimo o reservando para tercero) ── */
          <View className="gap-3">
            <View className="flex-row items-center justify-between">
              <Text className="text-sm font-semibold text-slate-800">
                {isAuthenticated ? 'Datos del paciente' : 'Tus datos'}
              </Text>
              {isAuthenticated ? (
                <Pressable onPress={() => setMode('self')}>
                  <Text className="text-sm font-medium text-brand-700">← Reservar para mí</Text>
                </Pressable>
              ) : null}
            </View>
            <Input
              label="Nombre completo"
              value={booking.patientName}
              onChangeText={(v) => booking.set({ patientName: v })}
              autoCapitalize="words"
            />
            <Input
              label="Correo"
              value={booking.patientEmail}
              onChangeText={(v) => booking.set({ patientEmail: v })}
              keyboardType="email-address"
              autoCapitalize="none"
            />
            <Input
              label="Teléfono"
              value={booking.patientPhone}
              onChangeText={(v) => booking.set({ patientPhone: v })}
              keyboardType="phone-pad"
              placeholder="+52 55 1234 5678"
            />
            <Input
              label="Notas (opcional)"
              value={booking.notes}
              onChangeText={(v) => booking.set({ notes: v })}
              multiline
              numberOfLines={3}
              placeholder="Motivo de consulta, alergias…"
            />
          </View>
        )}

        {error ? (
          <Card className="border-red-100 bg-red-50">
            <Text className="text-sm text-red-700">{error}</Text>
          </Card>
        ) : null}

        <Button
          label="Confirmar reserva"
          size="lg"
          fullWidth
          loading={mutation.isPending}
          onPress={onSubmit}
        />
      </KeyboardAvoidingView>
    </Screen>
  );
}

function SummaryRow({
  icon,
  text,
}: {
  icon: keyof typeof import('@expo/vector-icons/build/Ionicons').default.glyphMap;
  text: string;
}) {
  return (
    <View className="flex-row items-center gap-2">
      <Ionicons name={icon} size={16} color={COLORS.brand} />
      <Text className="text-sm text-slate-700">{text}</Text>
    </View>
  );
}
