import { Ionicons } from '@expo/vector-icons';
import { useState } from 'react';
import {
  FlatList,
  Modal,
  Pressable,
  Text,
  TouchableWithoutFeedback,
  View,
} from 'react-native';

import { COLORS } from '@/config/theme';

export interface SelectOption<V extends string> {
  /** Valor que se manda al backend (ej. "A+", "male"). */
  value: V;
  /** Texto visible al usuario (ej. "A positivo", "Masculino"). */
  label: string;
}

interface Props<V extends string> {
  label?: string;
  hint?: string;
  error?: string;
  /** Texto cuando no hay valor seleccionado. */
  placeholder?: string;
  /** Valor actual ('' = sin seleccionar). */
  value: V | '';
  /** Lista de opciones; en orden de presentación. */
  options: SelectOption<V>[];
  onChange: (value: V | '') => void;
  /** Permite "limpiar" la selección desde el sheet. Default true. */
  clearable?: boolean;
}

/**
 * Select tipo iOS — abre un sheet desde abajo con la lista de opciones.
 *
 * - Se usa como un Input normal: misma altura, mismos colores.
 * - El sheet se cierra al tocar afuera, al elegir, o el botón "Cancelar".
 * - Soporta `clearable` para que el usuario pueda volver a "sin valor".
 *
 * Diseño: no usamos `<Picker>` de RN porque es feo y poco controlable,
 * ni librerías terceras porque no las necesitamos para algo tan simple.
 */
export function Select<V extends string>({
  label,
  hint,
  error,
  placeholder = 'Selecciona una opción',
  value,
  options,
  onChange,
  clearable = true,
}: Props<V>) {
  const [open, setOpen] = useState(false);

  const selected = options.find((opt) => opt.value === value);

  return (
    <View className="gap-1.5">
      {label ? <Text className="text-sm font-medium text-slate-700">{label}</Text> : null}

      {/* Trigger: parece un Input pero abre el sheet al tocar */}
      <Pressable
        onPress={() => setOpen(true)}
        accessibilityRole="button"
        className={[
          'flex-row items-center justify-between rounded-xl border bg-white px-4 py-3',
          error ? 'border-red-400' : 'border-slate-200',
        ].join(' ')}
      >
        <Text className={`text-base ${selected ? 'text-slate-900' : 'text-slate-400'}`}>
          {selected?.label ?? placeholder}
        </Text>
        <Ionicons name="chevron-down" size={18} color="#94A3B8" />
      </Pressable>

      {error ? (
        <Text className="text-xs text-red-600">{error}</Text>
      ) : hint ? (
        <Text className="text-xs text-slate-500">{hint}</Text>
      ) : null}

      {/* Sheet modal con opciones */}
      <Modal
        visible={open}
        transparent
        animationType="slide"
        onRequestClose={() => setOpen(false)}
      >
        {/* Tocar el backdrop cierra el sheet */}
        <TouchableWithoutFeedback onPress={() => setOpen(false)}>
          <View className="flex-1 justify-end bg-black/40">
            {/* Stop propagation: tocar el sheet NO lo cierra */}
            <TouchableWithoutFeedback>
              <View className="rounded-t-3xl bg-white pb-8 pt-2">
                {/* Handle visual del sheet */}
                <View className="items-center py-2">
                  <View className="h-1 w-10 rounded-full bg-slate-300" />
                </View>

                {/* Header */}
                <View className="flex-row items-center justify-between px-5 pb-2 pt-1">
                  <Text className="text-base font-semibold text-slate-900">
                    {label ?? placeholder}
                  </Text>
                  {clearable && selected ? (
                    <Pressable
                      onPress={() => {
                        onChange('' as V | '');
                        setOpen(false);
                      }}
                    >
                      <Text className="text-sm font-medium text-red-600">Limpiar</Text>
                    </Pressable>
                  ) : null}
                </View>

                {/* Lista de opciones */}
                <FlatList
                  data={options}
                  keyExtractor={(opt) => opt.value}
                  className="max-h-96"
                  renderItem={({ item }) => {
                    const isSelected = item.value === value;
                    return (
                      <Pressable
                        onPress={() => {
                          onChange(item.value);
                          setOpen(false);
                        }}
                        className={`flex-row items-center justify-between px-5 py-3.5 active:bg-slate-100 ${
                          isSelected ? 'bg-brand-50' : ''
                        }`}
                      >
                        <Text
                          className={`text-base ${
                            isSelected ? 'font-semibold text-brand-700' : 'text-slate-800'
                          }`}
                        >
                          {item.label}
                        </Text>
                        {isSelected ? (
                          <Ionicons name="checkmark" size={20} color={COLORS.brand} />
                        ) : null}
                      </Pressable>
                    );
                  }}
                  ItemSeparatorComponent={() => (
                    <View className="mx-5 h-px bg-slate-100" />
                  )}
                />
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </View>
  );
}
