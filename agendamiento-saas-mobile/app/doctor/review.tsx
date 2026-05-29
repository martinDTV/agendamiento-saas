import { Ionicons } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Text,
  View,
} from 'react-native';

import { Avatar } from '@/components/Avatar';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { RatingPicker } from '@/components/RatingPicker';
import { Screen } from '@/components/Screen';
import { COLORS } from '@/config/theme';
import { type FieldErrors, parseFieldErrors } from '@/lib/fieldErrors';
import {
  createAnonymousReview,
  createReview,
  fetchDoctors,
} from '@/lib/queries';
import { useAuth } from '@/stores/auth';

/**
 * Pantalla "Escribir reseña" para un doctor.
 *
 * Dos modos según auth:
 *   - **Logueado**: rating + comentario opcional → POST /reviews/ → publicado.
 *   - **Anónimo**: nombre + email + rating + comentario → POST /public/reviews/
 *     → email con link de confirmación → publicado al confirmar.
 *
 * Recibe `?id=<doctor_uuid>` en query params.
 */
export default function ReviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useAuth((s) => s.user);
  const isAuthenticated = !!user;

  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  // Solo se usan en modo anónimo
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Cargamos el doctor para mostrar nombre + foto en el header
  const doctorQuery = useQuery({
    queryKey: ['doctors-discover', 'all'],
    queryFn: () => fetchDoctors(),
    select: (list) => list.find((d) => d.id === id) ?? null,
  });
  const doctor = doctorQuery.data;

  const authMutation = useMutation({
    mutationFn: createReview,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctors-discover'] });
      queryClient.invalidateQueries({ queryKey: ['doctor-reviews', id] });
      Alert.alert('¡Gracias!', 'Tu reseña fue publicada.', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    },
    onError: (e) => {
      const errors = parseFieldErrors(e);
      setFieldErrors(errors);
      setGeneralError(errors._general ?? null);
    },
  });

  const anonMutation = useMutation({
    mutationFn: createAnonymousReview,
    onSuccess: (res) => {
      Alert.alert(
        'Revisa tu correo',
        res.message,
        [{ text: 'Entendido', onPress: () => router.back() }],
      );
    },
    onError: (e) => {
      const errors = parseFieldErrors(e);
      setFieldErrors(errors);
      setGeneralError(errors._general ?? null);
    },
  });

  function onSubmit() {
    setFieldErrors({});
    setGeneralError(null);

    if (rating < 1 || rating > 5) {
      setGeneralError('Elige una calificación de 1 a 5 estrellas.');
      return;
    }
    if (!id) return;

    if (isAuthenticated) {
      authMutation.mutate({
        doctor: id,
        rating,
        comment: comment.trim() || undefined,
      });
    } else {
      // Validaciones del modo anónimo (el backend también valida)
      if (!name.trim()) {
        setFieldErrors({ reviewer_name: 'Tu nombre es requerido.' });
        return;
      }
      if (!email.trim() || !email.includes('@')) {
        setFieldErrors({ reviewer_email: 'Ingresa un correo válido.' });
        return;
      }
      anonMutation.mutate({
        doctor: id,
        reviewer_name: name.trim(),
        reviewer_email: email.trim().toLowerCase(),
        rating,
        comment: comment.trim() || undefined,
      });
    }
  }

  const isSubmitting = authMutation.isPending || anonMutation.isPending;

  if (doctorQuery.isLoading) {
    return (
      <Screen scroll={false}>
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color={COLORS.brand} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        className="gap-5"
      >
        {/* Header con doctor */}
        {doctor ? (
          <Card>
            <View className="flex-row items-center gap-3">
              <Avatar uri={doctor.photo_url} size={56} />
              <View className="flex-1">
                <Text className="text-base font-semibold text-slate-900">
                  Dr. {doctor.full_name}
                </Text>
                {doctor.specialty ? (
                  <Text className="text-sm text-slate-500">{doctor.specialty}</Text>
                ) : null}
              </View>
            </View>
          </Card>
        ) : null}

        {/* Rating picker */}
        <View className="gap-2">
          <Text className="text-center text-base font-semibold text-slate-800">
            ¿Cómo calificarías tu experiencia?
          </Text>
          <View className="py-2">
            <RatingPicker value={rating} onChange={setRating} />
          </View>
          {rating > 0 ? (
            <Text className="text-center text-sm text-slate-500">
              {['Pésima', 'Mala', 'Regular', 'Buena', 'Excelente'][rating - 1]}
            </Text>
          ) : (
            <Text className="text-center text-sm text-slate-400">
              Toca las estrellas para calificar
            </Text>
          )}
        </View>

        {/* Comentario */}
        <Input
          label="Comentario (opcional)"
          value={comment}
          onChangeText={setComment}
          multiline
          numberOfLines={4}
          placeholder="Cuenta brevemente cómo fue tu experiencia"
          maxLength={500}
          hint={`${comment.length}/500`}
          error={fieldErrors.comment}
        />

        {/* Datos en modo anónimo */}
        {!isAuthenticated ? (
          <View className="gap-3">
            <Card className="border-amber-100 bg-amber-50">
              <View className="flex-row items-start gap-2">
                <Ionicons name="information-circle" size={18} color="#92400E" />
                <Text className="flex-1 text-xs text-amber-800">
                  Te mandaremos un correo para confirmar que esta reseña es tuya.
                  Solo se publica al hacer click en el link.
                </Text>
              </View>
            </Card>
            <Input
              label="Tu nombre"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
              placeholder="Juan Pérez"
              error={fieldErrors.reviewer_name}
            />
            <Input
              label="Tu correo"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              placeholder="tu@correo.com"
              error={fieldErrors.reviewer_email}
            />
          </View>
        ) : null}

        {/* Error general */}
        {generalError ? (
          <Card className="border-red-100 bg-red-50">
            <Text className="text-sm text-red-700">{generalError}</Text>
          </Card>
        ) : null}

        {/* Submit */}
        <Button
          label={isAuthenticated ? 'Publicar reseña' : 'Enviar para verificación'}
          size="lg"
          fullWidth
          loading={isSubmitting}
          onPress={onSubmit}
        />
      </KeyboardAvoidingView>
    </Screen>
  );
}
