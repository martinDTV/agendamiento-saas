import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { ActivityIndicator, FlatList, Text, View } from 'react-native';

import { Card, PressableCard } from '@/components/Card';
import { EmptyState } from '@/components/EmptyState';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { formatCurrency } from '@/lib/format';
import { fetchServicesForDoctor } from '@/lib/queries';
import { useBooking } from '@/stores/booking';
import type { Service } from '@/types/api';

export default function SelectServiceScreen() {
  const router = useRouter();
  const setBooking = useBooking((s) => s.set);
  const doctorId = useBooking((s) => s.doctorId);

  // Solo servicios que ofrece ESTE doctor (cross-clínica: cada clínica tiene
  // sus propios servicios, y cada doctor ofrece un subset).
  const q = useQuery({
    queryKey: ['services-for-doctor', doctorId],
    queryFn: () => fetchServicesForDoctor(doctorId as string),
    enabled: doctorId != null,
  });

  function onSelect(service: Service) {
    setBooking({ serviceId: service.id, date: null, startTime: null });
    router.push('/booking/select-slot');
  }

  return (
    <Screen scroll={false}>
      <View className="px-5 pb-2 pt-4">
        <Text className="text-xl font-bold text-slate-900">Elige un servicio</Text>
        <Text className="text-sm text-slate-500">
          Selecciona qué tipo de consulta o procedimiento necesitas.
        </Text>
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
        <EmptyState icon="briefcase-outline" title="No hay servicios disponibles" />
      ) : (
        <FlatList
          data={q.data ?? []}
          keyExtractor={(s) => String(s.id)}
          contentContainerClassName="px-5 pb-8 gap-3 pt-2"
          renderItem={({ item }) => (
            <PressableCard onPress={() => onSelect(item)}>
              <View className="flex-row items-start gap-3">
                <View className="size-12 items-center justify-center rounded-xl bg-brand-100">
                  <Ionicons name="medkit" size={20} color={COLORS.brand} />
                </View>
                <View className="flex-1">
                  <Text className="text-base font-semibold text-slate-900">{item.name}</Text>
                  {item.description ? (
                    <Text className="mt-0.5 text-sm text-slate-500" numberOfLines={2}>
                      {item.description}
                    </Text>
                  ) : null}
                  <View className="mt-2 flex-row items-center gap-3">
                    <Text className="text-xs text-slate-500">⏱ {item.duration} min</Text>
                    <Text className="text-xs font-semibold text-brand-700">
                      {formatCurrency(item.price ?? null)}
                    </Text>
                  </View>
                </View>
                <Ionicons name="chevron-forward" size={20} color="#94A3B8" />
              </View>
            </PressableCard>
          )}
        />
      )}
    </Screen>
  );
}
