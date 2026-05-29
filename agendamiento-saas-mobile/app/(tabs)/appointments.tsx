import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { ActivityIndicator, FlatList, RefreshControl, Text, View } from 'react-native';

import { Card, PressableCard } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { formatLongDate, formatTime } from '@/lib/format';
import { fetchMyAppointments } from '@/lib/queries';
import type { Appointment, AppointmentStatus } from '@/types/api';

const statusLabel: Record<AppointmentStatus, string> = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  cancelled: 'Cancelada',
  completed: 'Completada',
  no_show: 'No asistió',
};

const statusStyle: Record<AppointmentStatus, string> = {
  pending: 'bg-amber-100 text-amber-800',
  confirmed: 'bg-emerald-100 text-emerald-800',
  cancelled: 'bg-red-100 text-red-800',
  completed: 'bg-slate-100 text-slate-700',
  no_show: 'bg-red-100 text-red-800',
};

export default function AppointmentsScreen() {
  const router = useRouter();
  const q = useQuery({ queryKey: ['my-appointments'], queryFn: fetchMyAppointments });

  function openDetail(appointment: Appointment) {
    router.push({
      pathname: '/appointment/[id]',
      params: { id: String(appointment.id) },
    });
  }

  return (
    <Screen scroll={false}>
      <View className="px-5 pt-6 pb-3">
        <Text className="text-2xl font-bold text-slate-900">Mis citas</Text>
        <Text className="text-sm text-slate-500">Historial y próximas reservas.</Text>
      </View>

      {q.isLoading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color={COLORS.brand} />
        </View>
      ) : q.isError ? (
        <View className="px-5">
          <Card className="border-red-100 bg-red-50">
            <Text className="text-sm text-red-700">{describeApiError(q.error)}</Text>
          </Card>
        </View>
      ) : (q.data?.length ?? 0) === 0 ? (
        <EmptyState
          icon="calendar-outline"
          title="Aún no tienes citas"
          description="Ve a Inicio para agendar la primera."
        />
      ) : (
        <FlatList
          data={q.data ?? []}
          keyExtractor={(a) => String(a.id)}
          contentContainerClassName="px-5 pb-8 gap-3"
          refreshControl={<RefreshControl refreshing={q.isFetching} onRefresh={() => q.refetch()} />}
          renderItem={({ item }) => (
            <AppointmentRow appointment={item} onPress={() => openDetail(item)} />
          )}
        />
      )}
    </Screen>
  );
}

function AppointmentRow({
  appointment,
  onPress,
}: {
  appointment: Appointment;
  onPress: () => void;
}) {
  return (
    <PressableCard onPress={onPress}>
      <View className="flex-row items-start justify-between gap-3">
        <View className="flex-1 gap-1">
          <Text className="text-base font-semibold text-slate-900">{appointment.service_name}</Text>
          <Text className="text-sm text-slate-500">{appointment.doctor_name}</Text>
          {appointment.tenant_name ? (
            <View className="mt-1 flex-row items-center gap-1.5">
              <Ionicons name="business-outline" size={14} color="#64748B" />
              <Text className="text-xs text-slate-500">{appointment.tenant_name}</Text>
            </View>
          ) : null}
          <View className="mt-2 flex-row items-center gap-2">
            <Ionicons name="calendar-outline" size={16} color="#64748B" />
            <Text className="text-sm text-slate-700">
              {formatLongDate(appointment.date)} · {formatTime(appointment.start_time)}
            </Text>
          </View>
        </View>
        <View className="items-end gap-2">
          <View className={`rounded-full px-2.5 py-1 ${statusStyle[appointment.status].split(' ')[0]}`}>
            <Text className={`text-xs font-semibold ${statusStyle[appointment.status].split(' ')[1]}`}>
              {statusLabel[appointment.status]}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
        </View>
      </View>
    </PressableCard>
  );
}
