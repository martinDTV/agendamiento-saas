/**
 * Opciones de los enums del paciente. Mantener en sync con
 * `apps/patients/models.py` (Gender, BloodType).
 *
 * Si el backend agrega/cambia una opción, actualizar aquí o el dropdown
 * mostrará un valor obsoleto y/o fallará la validación del modelo.
 */
import type { BloodType, Gender, SelectOption } from '@/types/api';

export const GENDER_OPTIONS: SelectOption<Exclude<Gender, ''>>[] = [
  { value: 'female', label: 'Femenino' },
  { value: 'male', label: 'Masculino' },
  { value: 'other', label: 'Otro' },
  { value: 'undisclosed', label: 'Prefiero no decir' },
];

// Orden: los más comunes primero (O+ es el más común en MX), después el resto,
// y "Desconocido" al final para que no se elija por accidente.
export const BLOOD_TYPE_OPTIONS: SelectOption<Exclude<BloodType, ''>>[] = [
  { value: 'O+', label: 'O+' },
  { value: 'A+', label: 'A+' },
  { value: 'B+', label: 'B+' },
  { value: 'AB+', label: 'AB+' },
  { value: 'O-', label: 'O-' },
  { value: 'A-', label: 'A-' },
  { value: 'B-', label: 'B-' },
  { value: 'AB-', label: 'AB-' },
  { value: 'unknown', label: 'No lo sé' },
];
