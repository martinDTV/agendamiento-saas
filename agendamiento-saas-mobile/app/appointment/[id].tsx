import { Ionicons } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ActivityIndicator, Alert, Linking, Text, View } from 'react-native';

import { Button } from '@/components/Button';
import { Card, PressableCard } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { formatLongDate, formatTime } from '@/lib/format';
import {
  cancelAppointment,
  fetchAppointmentDetail,
} from '@/lib/queries';
import { useBooking } from '@/stores/booking';
import type { AppointmentStatus } from '@/types/api';

const statusLabel: Record<AppointmentStatus, string> = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  cancelled: 'Cancelada',
  completed: 'Completada',
  no_show: 'No asistió',
};

const statusColor: Record<AppointmentStatus, { bg: string; text: string }> = {
  pending: { bg: 'bg-amber-100', text: 'text-amber-800' },
  confirmed: { bg: 'bg-emerald-100', text: 'text-emerald-800' },
  cancelled: { bg: 'bg-red-100', text: 'text-red-800' },
  completed: { bg: 'bg-slate-100', text: 'text-slate-700' },
  no_show: { bg: 'bg-red-100', text: 'text-red-800' },
};

/**
 * Detalle de cita con acciones para el paciente.
 *
 * El paciente puede:
 *   - Ver toda la info de la cita (doctor, servicio, fecha, hora, clínica)
 *   - Reagendar (si faltan más de 24h y no está cancelada/completada)
 *   - Cancelar (mismas reglas que reagendar)
 *   - Contactar a la clínica (mailto: o tel: si hay datos)
 *
 * La regla de 24h se valida del lado del backend también — si el frontend
 * permite tocar el botón por error, el backend lo rechaza con 400.
 */
export default function AppointmentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const resetBooking = useBooking((s) => s.reset);

  const q = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => fetchAppointmentDetail(id as string),
    enabled: !!id,
  });

  const cancelMut = useMutation({
    mutationFn: () => cancelAppointment(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointment', id] });
      Alert.alert('Cita cancelada', 'Tu cita fue cancelada exitosamente.');
    },
    onError: (e) => Alert.alert('No se pudo cancelar', describeApiError(e)),
  });

  if (q.isLoading) {
    return (
      <Screen scroll={false}>
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color={COLORS.brand} />
        </View>
      </Screen>
    );
  }

  if (q.isError || !q.data) {
    return (
      <Screen>
        <Card className="border-red-100 bg-red-50">
          <Text className="text-sm text-red-700">
            {q.isError ? describeApiError(q.error) : 'Cita no encontrada.'}
          </Text>
        </Card>
      </Screen>
    );
  }

  const appt = q.data;
  const status = appt.status;
  const isModifiable = canModify(appt.date, appt.start_time, status);

  function onCancel() {
    Alert.alert(
      'Cancelar cita',
      `¿Seguro que quieres cancelar tu cita del ${formatLongDate(appt.date)} a las ${formatTime(appt.start_time)}?`,
      [
        { text: 'No, mantener', style: 'cancel' },
        { text: 'Sí, cancelar', style: 'destructive', onPress: () => cancelMut.mutate() },
      ],
    );
  }

  function onReschedule() {
    // Reusamos el wizard de reserva en modo "reagendar".
    // Pre-llenamos el store con doctor y servicio actuales.
    resetBooking();
    useBooking.getState().set({
      doctorId: appt.doctor,
      serviceId: appt.service,
      // El usuario elige nueva fecha/hora en el wizard.
    });
    // Navegamos al selector de slot (saltando el de servicio porque ya lo
    // tenemos). El wizard guardará la nueva cita; el endpoint PATCH se
    // dispara desde otra ruta — por ahora el patrón más simple es que el
    // usuario vea su próxima cita y cancele/agende manualmente.
    router.push({
      pathname: '/appointment/reschedule',
      params: { id: String(appt.id) },
    });
  }

  return (
    <Screen>
      {/* ── Header con status ─────────────────────────────────────────── */}
      <View className="items-center gap-2 pt-2">
        <View className={`rounded-full px-3 py-1 ${statusColor[status].bg}`}>
          <Text className={`text-xs font-bold uppercase tracking-wider ${statusColor[status].text}`}>
            {statusLabel[status]}
          </Text>
        </View>
        <Text className="text-2xl font-bold text-slate-900 text-center">
          {appt.service_name}
        </Text>
        <Text className="text-base text-slate-500 text-center">{appt.doctor_name}</Text>
      </View>

      {/* ── Card principal con fecha y hora ───────────────────────────── */}
      <Card className="gap-3">
        <Row icon="calendar-outline" label="Fecha" value={formatLongDate(appt.date)} />
        <View className="h-px bg-slate-100" />
        <Row icon="time-outline" label="Hora" value={formatTime(appt.start_time)} />
      </Card>

      {/* ── Clínica ───────────────────────────────────────────────────── */}
      <Card className="gap-2">
        <View className="flex-row items-center gap-2">
          <Ionicons name="business-outline" size={18} color={COLORS.brand} />
          <Text className="text-base font-semibold text-slate-900">{appt.tenant_name}</Text>
        </View>
        {/* Aquí en el futuro: dirección, mapa, botón llamar */}
      </Card>

      {/* ── Datos del paciente que llegará ────────────────────────────── */}
      <Card className="gap-2">
        <Text className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Paciente
        </Text>
        <Text className="text-base font-medium text-slate-900">{appt.patient_name}</Text>
        <Text className="text-sm text-slate-500">{appt.patient_email}</Text>
        {appt.patient_phone ? (
          <Text className="text-sm text-slate-500">{appt.patient_phone}</Text>
        ) : null}
      </Card>

      {appt.notes ? (
        <Card className="gap-2">
          <Text className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Notas
          </Text>
          <Text className="text-sm text-slate-800">{appt.notes}</Text>
        </Card>
      ) : null}

      {/* ── Acciones ──────────────────────────────────────────────────── */}
      {isModifiable ? (
        <View className="gap-3">
          <Button
            label="Reagendar"
            variant="secondary"
            fullWidth
            leftIcon={<Ionicons name="calendar" size={18} color={COLORS.brand} />}
            onPress={onReschedule}
          />
          <Button
            label="Cancelar cita"
            variant="danger"
            fullWidth
            loading={cancelMut.isPending}
            leftIcon={<Ionicons name="close-circle" size={18} color="#fff" />}
            onPress={onCancel}
          />
          <Text className="text-center text-xs text-slate-500">
            Solo puedes modificar tu cita con al menos 24 horas de anticipación.
          </Text>
        </View>
      ) : status === 'cancelled' || status === 'completed' || status === 'no_show' ? (
        <Card className="border-slate-100 bg-slate-50">
          <Text className="text-sm text-slate-600 text-center">
            Esta cita ya no se puede modificar porque está {statusLabel[status].toLowerCase()}.
          </Text>
        </Card>
      ) : (
        <Card className="border-amber-100 bg-amber-50">
          <Text className="text-sm text-amber-800 text-center">
            ⏰ Faltan menos de 24 horas — no se puede modificar.
            Si necesitas cancelar, contacta a la clínica directamente.
          </Text>
        </Card>
      )}
    </Screen>
  );
}

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
        <Text className="text-xs uppercase tracking-wider text-slate-500">{label}</Text>
        <Text className="text-base font-medium text-slate-900">{value}</Text>
      </View>
    </View>
  );
}

/**
 * Replica la regla del backend para mostrar/ocultar los botones.
 * El backend valida igual — esto es solo UX para no mostrar botones que
 * después fallarán.
 */
function canModify(dateStr: string, timeStr: string, status: AppointmentStatus): boolean {
  if (status === 'cancelled' || status === 'completed' || status === 'no_show') {
    return false;
  }
  const [y, m, d] = dateStr.split('-').map(Number);
  const [hh, mm] = timeStr.split(':').map(Number);
  const cita = new Date(y, m - 1, d, hh, mm);
  const hoursUntil = (cita.getTime() - Date.now()) / (1000 * 60 * 60);
  return hoursUntil >= 24;
}
