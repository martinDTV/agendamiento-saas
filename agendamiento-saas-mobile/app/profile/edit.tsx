import { Ionicons } from '@expo/vector-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Text, View } from 'react-native';

import { AddressFieldset } from '@/components/AddressFieldset';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { Screen } from '@/components/Screen';
import { Select } from '@/components/Select';
import { BLOOD_TYPE_OPTIONS, GENDER_OPTIONS } from '@/config/patientOptions';
import { COLORS } from '@/config/theme';
import { describeApiError } from '@/lib/api';
import { type FieldErrors, parseFieldErrors } from '@/lib/fieldErrors';
import { fetchMyProfile, updateMyProfile } from '@/lib/queries';
import type { BloodType, Gender, PatientUpdate } from '@/types/api';

/**
 * Pantalla de edición de perfil clínico.
 *
 * Validación: el BACKEND es autoritativo (apps/patients/validators.py).
 * Aquí solo añadimos `maxLength`/`autoCapitalize` para mejor UX de input,
 * y capturamos los errores 400 por campo del backend para mostrarlos
 * inline con cada input.
 *
 * El backend normaliza antes de validar — el usuario puede escribir
 * "+52 55 1234 5678" o "pepj 800101 hdfrrr01" y queda en el formato
 * canónico ("5512345678", "PEPJ800101HDFRRR01") al guardar.
 */
export default function EditProfileScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [form, setForm] = useState<PatientUpdate>({});

  const profileQuery = useQuery({
    queryKey: ['my-profile'],
    queryFn: fetchMyProfile,
  });

  useEffect(() => {
    if (profileQuery.data) {
      const { id, email, full_name, created_at, updated_at, ...editable } = profileQuery.data;
      setForm(editable);
    }
  }, [profileQuery.data]);

  const mutation = useMutation({
    mutationFn: updateMyProfile,
    onSuccess: (data) => {
      queryClient.setQueryData(['my-profile'], data);
      router.back();
    },
    onError: (e) => {
      const errors = parseFieldErrors(e);
      setFieldErrors(errors);
      setGeneralError(errors._general ?? null);
    },
  });

  function set<K extends keyof PatientUpdate>(key: K, value: PatientUpdate[K]) {
    setForm((f) => ({ ...f, [key]: value }));
    // Al editar un campo, limpiamos su error específico (UX: si el usuario
    // está corrigiendo, no quiero verlo gritar el error viejo).
    if (fieldErrors[key as string]) {
      setFieldErrors((errs) => {
        const next = { ...errs };
        delete next[key as string];
        return next;
      });
    }
  }

  function err(field: keyof PatientUpdate): string | undefined {
    return fieldErrors[field as string];
  }

  if (profileQuery.isLoading) {
    return (
      <Screen scroll={false}>
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator color={COLORS.brand} />
        </View>
      </Screen>
    );
  }

  if (profileQuery.isError) {
    return (
      <Screen>
        <Card className="border-red-100 bg-red-50">
          <Text className="text-sm text-red-700">{describeApiError(profileQuery.error)}</Text>
        </Card>
      </Screen>
    );
  }

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} className="gap-5">
        <SectionHeader icon="person-outline" title="Datos básicos" />
        <View className="gap-3">
          <Input
            label="Nombre"
            value={form.first_name ?? ''}
            onChangeText={(v) => set('first_name', v)}
            autoCapitalize="words"
            error={err('first_name')}
          />
          <Input
            label="Apellido"
            value={form.last_name ?? ''}
            onChangeText={(v) => set('last_name', v)}
            autoCapitalize="words"
            error={err('last_name')}
          />
          <Input
            label="Teléfono"
            keyboardType="phone-pad"
            value={form.phone ?? ''}
            onChangeText={(v) => set('phone', v)}
            maxLength={20}
            placeholder="+52 55 1234 5678"
            hint="10 dígitos. Puedes incluir lada (+52) y espacios."
            error={err('phone')}
          />
          <Input
            label="Fecha de nacimiento (YYYY-MM-DD)"
            value={form.birth_date ?? ''}
            onChangeText={(v) => set('birth_date', v || null)}
            placeholder="1990-05-15"
            maxLength={10}
            error={err('birth_date')}
          />
          <Select<Exclude<Gender, ''>>
            label="Género"
            placeholder="Selecciona"
            value={(form.gender as Gender) || ''}
            options={GENDER_OPTIONS}
            onChange={(v) => set('gender', v as Gender)}
            error={err('gender')}
          />
        </View>

        <SectionHeader icon="medkit-outline" title="Datos clínicos" />
        <View className="gap-3">
          <Select<Exclude<BloodType, ''>>
            label="Tipo de sangre"
            placeholder="Selecciona"
            value={(form.blood_type as BloodType) || ''}
            options={BLOOD_TYPE_OPTIONS}
            onChange={(v) => set('blood_type', v as BloodType)}
            error={err('blood_type')}
          />
          <Input
            label="Alergias"
            value={form.allergies ?? ''}
            onChangeText={(v) => set('allergies', v)}
            multiline
            numberOfLines={3}
            error={err('allergies')}
          />
          <Input
            label="Medicamentos actuales"
            value={form.current_medications ?? ''}
            onChangeText={(v) => set('current_medications', v)}
            multiline
            numberOfLines={3}
            error={err('current_medications')}
          />
          <Input
            label="Condiciones médicas"
            value={form.medical_conditions ?? ''}
            onChangeText={(v) => set('medical_conditions', v)}
            multiline
            numberOfLines={3}
            error={err('medical_conditions')}
          />
        </View>

        <SectionHeader icon="home-outline" title="Dirección" />
        <AddressFieldset
          value={{
            address_street: form.address_street,
            address_neighborhood: form.address_neighborhood,
            address_city: form.address_city,
            address_state: form.address_state,
            address_zip: form.address_zip,
          }}
          onChange={(patch) => setForm((f) => ({ ...f, ...patch }))}
          fieldError={(key) => err(key as keyof PatientUpdate)}
        />

        <SectionHeader icon="alert-circle-outline" title="Contacto de emergencia" />
        <View className="gap-3">
          <Input
            label="Nombre"
            value={form.emergency_contact_name ?? ''}
            onChangeText={(v) => set('emergency_contact_name', v)}
            autoCapitalize="words"
            error={err('emergency_contact_name')}
          />
          <Input
            label="Teléfono"
            keyboardType="phone-pad"
            value={form.emergency_contact_phone ?? ''}
            onChangeText={(v) => set('emergency_contact_phone', v)}
            maxLength={20}
            placeholder="+52 55 1234 5678"
            hint="10 dígitos (con lada)."
            error={err('emergency_contact_phone')}
          />
          <Input
            label="Relación"
            placeholder="Madre, Hermano, Cónyuge…"
            value={form.emergency_contact_relation ?? ''}
            onChangeText={(v) => set('emergency_contact_relation', v)}
            autoCapitalize="words"
            error={err('emergency_contact_relation')}
          />
        </View>

        <SectionHeader icon="document-text-outline" title="Identificación MX" />
        <View className="gap-3">
          <Input
            label="CURP"
            autoCapitalize="characters"
            autoCorrect={false}
            value={form.curp ?? ''}
            onChangeText={(v) => set('curp', v.toUpperCase())}
            maxLength={18}
            placeholder="PEPJ800101HDFRRR01"
            hint="18 caracteres del RENAPO."
            error={err('curp')}
          />
          <Input
            label="RFC"
            autoCapitalize="characters"
            autoCorrect={false}
            value={form.rfc ?? ''}
            onChangeText={(v) => set('rfc', v.toUpperCase())}
            maxLength={13}
            placeholder="PEPJ800101AB1"
            hint="13 caracteres para persona física."
            error={err('rfc')}
          />
        </View>

        {generalError ? (
          <Card className="border-red-100 bg-red-50">
            <Text className="text-sm text-red-700">{generalError}</Text>
          </Card>
        ) : null}

        <Button
          label="Guardar cambios"
          size="lg"
          fullWidth
          loading={mutation.isPending}
          onPress={() => {
            setGeneralError(null);
            setFieldErrors({});
            mutation.mutate(form);
          }}
        />
      </KeyboardAvoidingView>
    </Screen>
  );
}

function SectionHeader({
  icon,
  title,
}: {
  icon: keyof typeof import('@expo/vector-icons/build/Ionicons').default.glyphMap;
  title: string;
}) {
  return (
    <View className="flex-row items-center gap-2 pt-2">
      <Ionicons name={icon} size={18} color={COLORS.brand} />
      <Text className="text-base font-semibold text-slate-800">{title}</Text>
    </View>
  );
}
