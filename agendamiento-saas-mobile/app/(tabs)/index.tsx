import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Pressable, ScrollView, Text, TextInput, View } from 'react-native';

import { Card } from '@/components/Card';
import { DoctorCard } from '@/components/DoctorCard';
import { EmptyState } from '@/components/EmptyState';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { useUserLocation } from '@/hooks/useUserLocation';
import { describeApiError } from '@/lib/api';
import { fetchDoctors } from '@/lib/queries';
import { useBooking } from '@/stores/booking';
import { useAuth } from '@/stores/auth';
import type { Doctor } from '@/types/api';

/**
 * Pantalla Inicio — rediseño con principios UX/UI:
 *
 *   1. Saludo personalizado al usuario logueado.
 *   2. Filtros rápidos arriba (chips horizontales).
 *   3. Buscador.
 *   4. Lista de cards verticales ricas con foto grande, rating, próxima
 *      disponibilidad y botón directo "Agendar".
 *
 * El botón "Agendar" salta el detalle del doctor — patrón estándar para
 * reducir fricción en apps de salud (Doctoralia/ZocDoc/Practo).
 */

type DateFilter = 'all' | 'today' | 'tomorrow' | 'week';

const DATE_FILTERS: { key: DateFilter; label: string }[] = [
  { key: 'all', label: 'Todos' },
  { key: 'today', label: 'Hoy' },
  { key: 'tomorrow', label: 'Mañana' },
  { key: 'week', label: 'Esta semana' },
];

export default function HomeScreen() {
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const resetBooking = useBooking((s) => s.reset);
  const [search, setSearch] = useState('');
  const [dateFilter, setDateFilter] = useState<DateFilter>('all');

  // "Cerca de mí" — ubicación del usuario. Cuando está activo, refetcheamos
  // con lat/lng y los doctores vienen ordenados por distancia desde el backend.
  const userLocation = useUserLocation();
  const isNearMe = userLocation.status === 'granted' && !!userLocation.location;

  // Activamos `with_next_slot` para que la card muestre próxima disponibilidad.
  // Es costoso en backend pero el valor visual lo justifica en esta pantalla.
  const doctorsQuery = useQuery({
    queryKey: [
      'doctors-discover',
      'with-slots',
      isNearMe ? `near:${userLocation.location?.lat},${userLocation.location?.lng}` : 'all',
    ],
    queryFn: () =>
      fetchDoctors({
        with_next_slot: true,
        ...(isNearMe && userLocation.location
          ? {
              lat: userLocation.location.lat,
              lng: userLocation.location.lng,
              radius_km: 50,
            }
          : {}),
      }),
  });

  async function onToggleNearMe() {
    if (isNearMe) {
      userLocation.clear();
      return;
    }
    const loc = await userLocation.request();
    if (!loc && userLocation.status === 'denied') {
      Alert.alert(
        'Ubicación denegada',
        'Para encontrar doctores cerca de ti, activa la ubicación en Configuración.',
      );
    }
  }

  // Filtros aplicados client-side (búsqueda + fecha).
  const filtered = useMemo(() => {
    let list = doctorsQuery.data ?? [];

    // Filtro de búsqueda
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter((d) => {
        const haystack = `${d.full_name} ${d.specialty ?? ''} ${d.tenant_name}`.toLowerCase();
        return haystack.includes(q);
      });
    }

    // Filtro de fecha — basado en next_available
    if (dateFilter !== 'all') {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const cutoff = new Date(today);
      if (dateFilter === 'today') cutoff.setDate(today.getDate() + 1);
      else if (dateFilter === 'tomorrow') cutoff.setDate(today.getDate() + 2);
      else if (dateFilter === 'week') cutoff.setDate(today.getDate() + 7);

      list = list.filter((d) => {
        if (!d.next_available) return false;
        const [y, m, day] = d.next_available.date.split('-').map(Number);
        const slot = new Date(y, m - 1, day);
        // Para 'today' debe ser hoy o antes que cutoff (mañana 00:00)
        return slot < cutoff;
      });
    }

    return list;
  }, [doctorsQuery.data, search, dateFilter]);

  function onDoctorPress(doctor: Doctor) {
    resetBooking();
    useBooking.getState().set({ doctorId: doctor.id });
    router.push({ pathname: '/doctor/[id]', params: { id: String(doctor.id) } });
  }

  function onBookDirect(doctor: Doctor) {
    // Salto directo al wizard de reserva — sin pasar por detalle del doctor.
    resetBooking();
    useBooking.getState().set({ doctorId: doctor.id });
    router.push('/booking/select-service');
  }

  const firstName = user?.first_name?.trim();

  return (
    <Screen scroll={false}>
      {/* ── Header con saludo personalizado ───────────────────────────── */}
      <View className="px-5 pt-6 pb-3">
        <Text className="text-sm text-slate-500">
          {firstName ? `Hola, ${firstName} 👋` : 'Hola 👋'}
        </Text>
        <Text className="text-2xl font-bold text-slate-900">
          Encuentra un especialista
        </Text>
      </View>

      {/* ── Buscador ──────────────────────────────────────────────────── */}
      <View className="px-5 pb-3">
        <View className="flex-row items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3">
          <Ionicons name="search" size={20} color="#64748B" />
          <TextInput
            className="flex-1 text-base text-slate-900"
            placeholder="Doctor, especialidad o clínica"
            placeholderTextColor="#94A3B8"
            value={search}
            onChangeText={setSearch}
            returnKeyType="search"
            autoCapitalize="none"
            autoCorrect={false}
          />
          {search ? (
            <Pressable onPress={() => setSearch('')}>
              <Ionicons name="close-circle" size={20} color="#94A3B8" />
            </Pressable>
          ) : null}
        </View>
      </View>

      {/* ── Filtros chips ─────────────────────────────────────────────── */}
      <View className="pb-3">
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerClassName="px-5 gap-2"
        >
          {/* Chip "Cerca de mí" — primero porque es el más impactante */}
          <Pressable
            onPress={onToggleNearMe}
            disabled={userLocation.status === 'requesting'}
            className={`flex-row items-center gap-1.5 rounded-full border px-4 py-2 ${
              isNearMe
                ? 'border-brand-600 bg-brand-600'
                : 'border-slate-200 bg-white'
            }`}
          >
            {userLocation.status === 'requesting' ? (
              <ActivityIndicator size="small" color={isNearMe ? '#fff' : COLORS.brand} />
            ) : (
              <Ionicons
                name={isNearMe ? 'location' : 'location-outline'}
                size={14}
                color={isNearMe ? '#fff' : COLORS.brand}
              />
            )}
            <Text
              className={`text-sm font-medium ${
                isNearMe ? 'text-white' : 'text-slate-700'
              }`}
            >
              Cerca de mí
            </Text>
          </Pressable>

          {DATE_FILTERS.map((f) => {
            const active = dateFilter === f.key;
            return (
              <Pressable
                key={f.key}
                onPress={() => setDateFilter(f.key)}
                className={`rounded-full border px-4 py-2 ${
                  active
                    ? 'border-brand-600 bg-brand-600'
                    : 'border-slate-200 bg-white'
                }`}
              >
                <Text
                  className={`text-sm font-medium ${
                    active ? 'text-white' : 'text-slate-700'
                  }`}
                >
                  {f.label}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {/* ── Lista ─────────────────────────────────────────────────────── */}
      {doctorsQuery.isLoading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color={COLORS.brand} />
        </View>
      ) : doctorsQuery.isError ? (
        <View className="px-5">
          <Card className="border-red-100 bg-red-50">
            <Text className="text-sm text-red-700">
              {describeApiError(doctorsQuery.error)}
            </Text>
          </Card>
        </View>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="medical-outline"
          title={search || dateFilter !== 'all' ? 'Sin coincidencias' : 'Sin doctores disponibles'}
          description={
            search || dateFilter !== 'all'
              ? 'Prueba con otros filtros o términos de búsqueda.'
              : 'Vuelve más tarde.'
          }
        />
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(d) => String(d.id)}
          contentContainerClassName="px-5 pb-8 gap-3"
          renderItem={({ item }) => (
            <DoctorCard
              doctor={item}
              onPress={() => onDoctorPress(item)}
              onBook={() => onBookDirect(item)}
            />
          )}
        />
      )}
    </Screen>
  );
}
