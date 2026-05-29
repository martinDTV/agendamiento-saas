import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { addDays, format } from 'date-fns';
import { es } from 'date-fns/locale';
import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, Text, View } from 'react-native';

import { Card } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { formatTime } from '@/lib/format';
import { fetchSlots } from '@/lib/queries';
import { useBooking } from '@/stores/booking';

/**
 * Tirilla de 14 días para elegir fecha + grid de horas disponibles.
 * Las horas vienen de GET /public/slots/?doctor=&service=&date=
 */

function buildDays(): string[] {
  const today = new Date();
  return Array.from({ length: 14 }, (_, i) => format(addDays(today, i), 'yyyy-MM-dd'));
}

export default function SelectSlotScreen() {
  const router = useRouter();
  const { doctorId, serviceId, date, set } = useBooking();
  const days = useMemo(buildDays, []);
  const [selectedDate, setSelectedDate] = useState<string>(date ?? days[0]);

  const slotsQuery = useQuery({
    queryKey: ['slots', doctorId, serviceId, selectedDate],
    queryFn: () =>
      fetchSlots({ doctor: doctorId as string, service: serviceId as string, date: selectedDate }),
    enabled: doctorId != null && serviceId != null,
  });

  if (doctorId == null || serviceId == null) {
    return (
      <Screen>
        <EmptyState
          icon="warning-outline"
          title="Faltan datos"
          description="Vuelve al inicio del flujo de reserva."
        />
      </Screen>
    );
  }

  function onPickSlot(time: string) {
    set({ date: selectedDate, startTime: time });
    router.push('/booking/confirm');
  }

  return (
    <Screen scroll={false}>
      <View className="px-5 pb-3 pt-4">
        <Text className="text-xl font-bold text-slate-900">Elige fecha y hora</Text>
        <Text className="text-sm text-slate-500">
          Disponibilidad en tiempo real según la agenda del doctor.
        </Text>
      </View>

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
            return (
              <Pressable
                onPress={() => setSelectedDate(item)}
                className={`w-16 items-center rounded-2xl border px-2 py-3 ${
                  active ? 'border-brand-600 bg-brand-600' : 'border-slate-200 bg-white'
                }`}
              >
                <Text className={`text-xs ${active ? 'text-brand-100' : 'text-slate-500'}`}>
                  {format(d, 'EEE', { locale: es })}
                </Text>
                <Text className={`text-lg font-bold ${active ? 'text-white' : 'text-slate-900'}`}>
                  {format(d, 'd')}
                </Text>
                <Text className={`text-[10px] ${active ? 'text-brand-100' : 'text-slate-400'}`}>
                  {format(d, 'MMM', { locale: es })}
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
            // Chips compactos 4 por fila al estilo OpenTable/Calendly — más
            // horarios visibles sin scroll, layout más limpio.
            numColumns={4}
            columnWrapperClassName="gap-2"
            contentContainerClassName="pb-8 gap-2 pt-2"
            renderItem={({ item }) => (
              <Pressable
                onPress={() => onPickSlot(item.start)}
                className="flex-1 items-center rounded-lg border border-brand-200 bg-white py-2.5 active:bg-brand-600"
              >
                <Text className="text-sm font-semibold text-brand-700">
                  {formatTime(item.start)}
                </Text>
              </Pressable>
            )}
          />
        )}
      </View>
    </Screen>
  );
}
