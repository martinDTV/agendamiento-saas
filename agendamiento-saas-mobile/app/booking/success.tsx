import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Text, View } from 'react-native';

import { Button } from '@/components/Button';
import { Screen } from '@/components/Screen';
import { useBooking } from '@/stores/booking';

export default function BookingSuccessScreen() {
  const router = useRouter();
  const reset = useBooking((s) => s.reset);

  function goHome() {
    reset();
    router.replace('/(tabs)');
  }

  function viewAppointments() {
    reset();
    router.replace('/(tabs)/appointments');
  }

  return (
    <Screen scroll={false}>
      <View className="flex-1 items-center justify-center px-6 gap-6">
        <View className="size-24 items-center justify-center rounded-full bg-emerald-100">
          <Ionicons name="checkmark-circle" size={64} color="#10B981" />
        </View>
        <View className="items-center gap-2">
          <Text className="text-2xl font-bold text-slate-900">¡Reserva confirmada!</Text>
          <Text className="text-center text-base text-slate-500">
            Te enviamos los detalles a tu correo. Recibirás un recordatorio 24 horas antes.
          </Text>
        </View>
        <View className="w-full gap-3">
          <Button label="Ver mis citas" size="lg" fullWidth onPress={viewAppointments} />
          <Button label="Volver al inicio" variant="ghost" fullWidth onPress={goHome} />
        </View>
      </View>
    </Screen>
  );
}
