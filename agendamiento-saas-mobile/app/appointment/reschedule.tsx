import { Ionicons } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Pressable, Text, View } from 'react-native';

import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { formatTime } from '@/lib/format';
import {
  fetchAppointmentDetail,
  fetchSlots,
  rescheduleAppointment,
} from '@/lib/queries';

/**
 * Pantalla para reagendar una cita existente.
 *
 * Reusa los mismos slots del booking flow: muestra los próximos 14 días
 * arriba (tirilla scrolleable) y los horarios disponibles del doctor en
 * un grid de 4 columnas (mismo patrón que select-slot.tsx).
 *
 * Al elegir slot, dispara PATCH /patients/me/appointments/{id}/.
 */
function buildDays(): string[] {
  const today = new Date();
  return Array.from({ length: 14 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    return d.toISOString().slice(0, 10);
  });
}

export default function RescheduleScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const apptQuery = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => fetchAppointmentDetail(id as string),
    enabled: !!id,
  });
  const appt = apptQuery.data;

  const days = useMemo(buildDays, []);
  const [selectedDate, setSelectedDate] = useState<string>(days[0]);

  const slotsQuery = useQuery({
    queryKey: ['slots', appt?.doctor, appt?.service, selectedDate],
    queryFn: () =>
      fetchSlots({
        doctor: appt!.doctor as string,
        service: appt!.service as string,
        date: selectedDate,
      }),
    enabled: !!appt,
  });

  const rescheduleMut = useMutation({
    mutationFn: (payload: { date: string; start_time: string }) =>
      rescheduleAppointment(id as string, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointment', id] });
      Alert.alert('Cita reagendada', 'Tu cita fue reagendada exitosamente.', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    },
    onError: (e) => Alert.alert('No se pudo reagendar', describeApiError(e)),
  });

  function onPickSlot(start: string) {
    rescheduleMut.mutate({ date: selectedDate, start_time: start });
  }

  if (apptQuery.isLoading || !appt) {
    return (
      <Screen scroll={false}>
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color={COLORS.brand} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false}>
      <View className="px-5 pb-3 pt-4">
        <Text className="text-xl font-bold text-slate-900">Reagendar cita</Text>
        <Text className="text-sm text-slate-500">
          Con {appt.doctor_name} — {appt.service_name}
        </Text>
      </View>

      {/* Tirilla de fechas */}
      <View className="pl-5">
        <FlatList
          data={days}
          horizontal
          keyExtractor={(d) => d}
          showsHorizontalScrollIndicator={false}
          contentContainerClassName="gap-2 pr-5 pb-3"
          renderItem={({ item }) => {
            const d = new Date(item + 'T00:00:00');
            const active = item === selectedDate;
            const dayName = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'][d.getDay()];
            const monthName = [
              'ene', 'feb', 'mar', 'abr', 'may', 'jun',
              'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
            ][d.getMonth()];
            return (
              <Pressable
                onPress={() => setSelectedDate(item)}
                className={`w-16 items-center rounded-2xl border px-2 py-3 ${
                  active ? 'border-brand-600 bg-brand-600' : 'border-slate-200 bg-white'
                }`}
              >
                <Text className={`text-xs ${active ? 'text-brand-100' : 'text-slate-500'}`}>
                  {dayName}
                </Text>
                <Text className={`text-lg font-bold ${active ? 'text-white' : 'text-slate-900'}`}>
                  {d.getDate()}
                </Text>
                <Text className={`text-[10px] ${active ? 'text-brand-100' : 'text-slate-400'}`}>
                  {monthName}
                </Text>
              </Pressable>
            );
          }}
        />
      </View>

      <View className="flex-1 px-5">
        {slotsQuery.isLoading ? (
          <View className="flex-1 items-center justify-center">
            <ActivityIndicator color={COLORS.brand} />
          </View>
        ) : slotsQuery.isError ? (
          <Card className="border-red-100 bg-red-50">
            <Text className="text-sm text-red-700">{describeApiError(slotsQuery.error)}</Text>
          </Card>
        ) : (slotsQuery.data?.slots.length ?? 0) === 0 ? (
          <EmptyState
            icon="time-outline"
            title="No hay horarios disponibles"
            description="Prueba con otro día."
          />
        ) : (
          <FlatList
            data={slotsQuery.data?.slots ?? []}
            keyExtractor={(s) => s.start}
            numColumns={4}
            columnWrapperClassName="gap-2"
            contentContainerClassName="pb-8 gap-2 pt-2"
            renderItem={({ item }) => (
              <Pressable
                onPress={() => onPickSlot(item.start)}
                disabled={rescheduleMut.isPending}
                className="flex-1 items-center rounded-lg border border-brand-200 bg-white py-2.5 active:bg-brand-600"
              >
                <Text className="text-sm font-semibold text-brand-700">
                  {formatTime(item.start)}
                </Text>
              </Pressable>
            )}
          />
        )}

        {rescheduleMut.isPending ? (
          <View className="absolute inset-0 items-center justify-center bg-white/60">
            <ActivityIndicator size="large" color={COLORS.brand} />
          </View>
        ) : null}
      </View>
    </Screen>
  );
}
