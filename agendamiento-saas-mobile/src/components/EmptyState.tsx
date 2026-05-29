import { Ionicons } from '@expo/vector-icons';
import { Text, View } from 'react-native';

import { COLORS } from '@/config/theme';

interface Props {
  icon?: keyof typeof Ionicons.glyphMap;
  title: string;
  description?: string;
}

export function EmptyState({ icon = 'sparkles-outline', title, description }: Props) {
  return (
    <View className="items-center justify-center gap-3 py-12 px-6">
      <View className="size-16 items-center justify-center rounded-full bg-brand-100">
        <Ionicons name={icon} size={28} color={COLORS.brand} />
      </View>
      <Text className="text-center text-base font-semibold text-slate-800">{title}</Text>
      {description ? (
        <Text className="text-center text-sm text-slate-500">{description}</Text>
      ) : null}
    </View>
  );
}
