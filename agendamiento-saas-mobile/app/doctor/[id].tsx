import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';

import { Avatar } from '@/components/Avatar';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { fetchDoctorReviews, fetchDoctors } from '@/lib/queries';
import { useBooking } from '@/stores/booking';
import type { Review } from '@/types/api';

export default function DoctorDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const setBooking = useBooking((s) => s.set);

  const q = useQuery({
    queryKey: ['doctors-discover'],
    queryFn: () => fetchDoctors(),
    select: (list) => list.find((d) => String(d.id) === id) ?? null,
  });

  // Reseñas del doctor (pública, no requiere auth)
  const reviewsQuery = useQuery({
    queryKey: ['doctor-reviews', id],
    queryFn: () => fetchDoctorReviews(id as string),
    enabled: !!id,
  });

  function onBook() {
    if (!q.data) return;
    setBooking({ doctorId: q.data.id, serviceId: null, date: null, startTime: null });
    router.push('/booking/select-service');
  }

  function onWriteReview() {
    if (!id) return;
    router.push({ pathname: '/doctor/review', params: { id } });
  }

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
            {q.isError ? describeApiError(q.error) : 'Doctor no encontrado.'}
          </Text>
        </Card>
      </Screen>
    );
  }

  const doctor = q.data;
  const reviews = reviewsQuery.data ?? [];
  const hasRating = doctor.avg_rating != null && doctor.review_count > 0;

  return (
    <Screen>
      {/* ── Header ────────────────────────────────────────────────────── */}
      <View className="items-center gap-3 pt-2">
        <Avatar uri={doctor.photo_url} size={96} />
        <View className="items-center gap-1">
          <Text className="text-xl font-bold text-slate-900">
            Dr. {doctor.full_name}
          </Text>
          {doctor.specialty ? (
            <Text className="text-base text-slate-500">{doctor.specialty}</Text>
          ) : null}

          {/* Rating del doctor */}
          {hasRating ? (
            <View className="mt-1 flex-row items-center gap-1">
              <RatingStars rating={doctor.avg_rating!} />
              <Text className="text-sm font-semibold text-slate-900">
                {doctor.avg_rating!.toFixed(1)}
              </Text>
              <Text className="text-sm text-slate-500">
                ({doctor.review_count} reseñas)
              </Text>
            </View>
          ) : (
            <Text className="mt-1 text-xs text-slate-400">Aún sin reseñas</Text>
          )}

          <View className="mt-1 flex-row items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-1">
            <Ionicons name="business-outline" size={12} color={COLORS.brand} />
            <Text className="text-xs font-medium text-brand-700">{doctor.tenant_name}</Text>
          </View>
        </View>
      </View>

      {/* ── Bio ───────────────────────────────────────────────────────── */}
      {doctor.bio ? (
        <Card>
          <Text className="mb-2 text-sm font-semibold text-slate-800">Sobre el doctor</Text>
          <Text className="text-sm leading-5 text-slate-600">{doctor.bio}</Text>
        </Card>
      ) : null}

      {/* ── Reserva en línea badge ────────────────────────────────────── */}
      <Card>
        <View className="flex-row items-center gap-3">
          <Ionicons name="shield-checkmark" size={22} color="#10B981" />
          <View className="flex-1">
            <Text className="text-sm font-semibold text-slate-800">Reserva en línea</Text>
            <Text className="text-xs text-slate-500">
              Confirmación inmediata por correo. Política de cancelación 24h.
            </Text>
          </View>
        </View>
      </Card>

      {/* ── Agendar cita ──────────────────────────────────────────────── */}
      <Button
        label="Agendar cita"
        size="lg"
        fullWidth
        leftIcon={<Ionicons name="calendar" size={18} color="#fff" />}
        onPress={onBook}
      />

      {/* ── Reseñas ───────────────────────────────────────────────────── */}
      <View className="gap-3 pt-2">
        <View className="flex-row items-center justify-between">
          <Text className="text-base font-semibold text-slate-900">
            Reseñas {reviews.length > 0 ? `(${reviews.length})` : ''}
          </Text>
          <Pressable onPress={onWriteReview}>
            <View className="flex-row items-center gap-1">
              <Ionicons name="add-circle-outline" size={16} color={COLORS.brand} />
              <Text className="text-sm font-semibold text-brand-700">Dejar reseña</Text>
            </View>
          </Pressable>
        </View>

        {reviewsQuery.isLoading ? (
          <Card>
            <ActivityIndicator size="small" color={COLORS.brand} />
          </Card>
        ) : reviewsQuery.isError ? (
          <Card className="border-red-100 bg-red-50">
            <Text className="text-sm text-red-700">
              {describeApiError(reviewsQuery.error)}
            </Text>
          </Card>
        ) : reviews.length === 0 ? (
          <Card className="border-slate-100 bg-slate-50">
            <Text className="text-center text-sm text-slate-500">
              Aún no hay reseñas para este doctor.
            </Text>
            <Text className="mt-1 text-center text-xs text-slate-400">
              ¡Sé el primero en dejar una!
            </Text>
          </Card>
        ) : (
          <View className="gap-2">
            {reviews.slice(0, 10).map((review) => (
              <ReviewItem key={review.id} review={review} />
            ))}
          </View>
        )}
      </View>
    </Screen>
  );
}

/** 5 estrellas para mostrar (no editable). */
function RatingStars({ rating, size = 12 }: { rating: number; size?: number }) {
  return (
    <View className="flex-row items-center">
      {[1, 2, 3, 4, 5].map((n) => (
        <Ionicons
          key={n}
          name={n <= Math.round(rating) ? 'star' : 'star-outline'}
          size={size}
          color="#F59E0B"
        />
      ))}
    </View>
  );
}

function ReviewItem({ review }: { review: Review }) {
  return (
    <Card>
      <View className="flex-row items-center justify-between">
        <Text className="text-sm font-semibold text-slate-900">{review.author_name}</Text>
        <Text className="text-xs text-slate-400">{formatRelativeDate(review.created_at)}</Text>
      </View>
      <View className="mt-1">
        <RatingStars rating={review.rating} size={14} />
      </View>
      {review.comment ? (
        <Text className="mt-2 text-sm text-slate-700 leading-5">{review.comment}</Text>
      ) : null}
    </Card>
  );
}

function formatRelativeDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days < 1) return 'Hoy';
  if (days < 7) return `Hace ${days} d`;
  if (days < 30) return `Hace ${Math.floor(days / 7)} sem`;
  if (days < 365) return `Hace ${Math.floor(days / 30)} mes${days >= 60 ? 'es' : ''}`;
  return `Hace ${Math.floor(days / 365)} año${days >= 730 ? 's' : ''}`;
}
