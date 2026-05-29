"""Endpoints REST de la app patients."""
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .emails import send_activation_email
from .models import Patient, PatientActivationToken
from .serializers import (
    ActivatePatientSerializer,
    PatientRegisterSerializer,
    PatientSerializer,
)


class PatientRegisterView(APIView):
    """
    POST /rest/v1/public/patients/register/

    Cuerpo: {email, password, first_name, last_name?, phone?, birth_date?}

    Crea User (is_active=False) + Patient + envía email de activación.
    No requiere autenticación. No requiere tenant (Patient es global).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PatientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        send_activation_email(result['activation'])
        return Response(
            {
                'status': 'registered',
                'message': 'Cuenta creada. Revisa tu correo para activarla.',
                'email': result['patient'].user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class PatientActivateView(APIView):
    """
    Activación de cuenta de paciente. Soporta dos formatos:

    - POST /rest/v1/public/patients/activate/   {"token": "..."}
        → JSON 200 {status, email}.  La app móvil usa este formato (después de
          capturar el deep-link `agendamiento://activate?token=...`).

    - GET  /rest/v1/public/patients/activate/?token=...
        → HTML 200.  Lo que sale en el botón del correo cuando el paciente lo
          abre en cualquier navegador (Mac, PC, celular sin la app instalada).
          Muestra una página simple "Cuenta activada ✓" y un link al login.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ActivatePatientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'status': 'activated', 'email': user.email},
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        # Reusamos exactamente la misma lógica que POST — solo cambia el
        # contrato de salida (HTML vs JSON).
        token_raw = request.query_params.get('token', '').strip()
        if not token_raw:
            return render(
                request,
                'patients/activate_error.html',
                {'message': 'Falta el token de activación en el enlace.'},
                status=400,
            )

        # Validar con el mismo serializer para no duplicar reglas.
        serializer = ActivatePatientSerializer(data={'token': token_raw})
        if not serializer.is_valid():
            # Tomamos el primer mensaje de error legible.
            errors = serializer.errors
            msg = 'Enlace inválido.'
            if 'token' in errors and errors['token']:
                msg = str(errors['token'][0])
            return render(
                request,
                'patients/activate_error.html',
                {'message': msg},
                status=400,
            )

        user = serializer.save()
        return render(
            request,
            'patients/activate_success.html',
            {'email': user.email},
            status=200,
        )


class PatientMeView(APIView):
    """
    GET   /rest/v1/patients/me/   → perfil completo
    PATCH /rest/v1/patients/me/   → actualizar perfil

    Requiere autenticación. El user debe tener un Patient asociado.
    """
    permission_classes = [IsAuthenticated]

    def _get_patient(self, request):
        patient = Patient.objects.filter(user=request.user).first()
        if not patient:
            return None
        return patient

    def get(self, request):
        patient = self._get_patient(request)
        if not patient:
            return Response(
                {'detail': 'Este usuario no tiene perfil de paciente.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PatientSerializer(patient).data)

    def patch(self, request):
        patient = self._get_patient(request)
        if not patient:
            return Response(
                {'detail': 'Este usuario no tiene perfil de paciente.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PatientSerializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PatientMyAppointmentsView(APIView):
    """
    GET /rest/v1/patients/me/appointments/

    Lista TODAS las citas del paciente, cross-tenant (en cualquier clínica donde
    haya reservado). Usa el manager `_all` (no scoped) porque Patient es global.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.bookings.models import Appointment
        from apps.bookings.serializers import AppointmentSerializer

        patient = Patient.objects.filter(user=request.user).first()
        if not patient:
            return Response(
                {'detail': 'Este usuario no tiene perfil de paciente.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        appointments = (
            Appointment._all.filter(patient=patient)
            .select_related('doctor', 'service', 'tenant')
            .order_by('-date', '-start_time')
        )
        return Response(AppointmentSerializer(appointments, many=True).data)


class PatientAppointmentDetailView(APIView):
    """
    GET    /rest/v1/patients/me/appointments/{id}/   → detalle
    PATCH  /rest/v1/patients/me/appointments/{id}/   → reagendar (date, start_time)
    DELETE /rest/v1/patients/me/appointments/{id}/   → cancelar

    Reglas de seguridad:
      - El paciente solo puede tocar SUS citas (filtramos por patient=request.user).
      - DELETE no borra físicamente, cambia status a 'cancelled' (las clínicas
        quieren ver cancelaciones para estadísticas de no-show).
      - PATCH solo permite cambiar fecha/hora — NO permite cambiar doctor o
        servicio (eso sería crear una cita nueva).
      - No se puede cancelar/reagendar con menos de 24h de anticipación.
    """
    permission_classes = [IsAuthenticated]

    def _get_appointment(self, request, appointment_id):
        from apps.bookings.models import Appointment
        patient = Patient.objects.filter(user=request.user).first()
        if not patient:
            return None, Response(
                {'detail': 'Este usuario no tiene perfil de paciente.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        appointment = Appointment._all.filter(
            pk=appointment_id, patient=patient,
        ).select_related('doctor__user', 'service', 'tenant').first()
        if not appointment:
            return None, Response(
                {'detail': 'Cita no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return appointment, None

    def _validate_modifiable(self, appointment):
        """
        Verifica que la cita aún se puede modificar:
          - No esté cancelada o completada.
          - Falten más de 24h para la cita.
        """
        from datetime import datetime, timedelta
        from apps.bookings.models import AppointmentStatus

        if appointment.status in (
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
        ):
            return Response(
                {'detail': 'Esta cita ya no se puede modificar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cita_dt = datetime.combine(appointment.date, appointment.start_time)
        if cita_dt - datetime.now() < timedelta(hours=24):
            return Response(
                {'detail': 'Solo puedes modificar la cita con al menos 24 horas de anticipación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None

    def get(self, request, appointment_id):
        from apps.bookings.serializers import AppointmentSerializer
        appointment, err = self._get_appointment(request, appointment_id)
        if err:
            return err
        return Response(AppointmentSerializer(appointment).data)

    def patch(self, request, appointment_id):
        """Reagendar: solo se permite cambiar `date` y `start_time`."""
        from datetime import datetime, timedelta, date as date_type
        from apps.bookings.models import Appointment, AppointmentStatus
        from apps.bookings.serializers import AppointmentSerializer
        from apps.bookings.slots import get_available_slots

        appointment, err = self._get_appointment(request, appointment_id)
        if err:
            return err

        guard = self._validate_modifiable(appointment)
        if guard:
            return guard

        new_date_str = request.data.get('date')
        new_time_str = request.data.get('start_time')
        if not new_date_str or not new_time_str:
            return Response(
                {'detail': 'date y start_time son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_date = date_type.fromisoformat(new_date_str)
            new_time = datetime.strptime(new_time_str, '%H:%M').time()
        except ValueError:
            return Response(
                {'detail': 'Formato de fecha/hora inválido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_date < date_type.today():
            return Response(
                {'detail': 'No puedes reagendar a una fecha pasada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar disponibilidad del slot
        slots = get_available_slots(
            appointment.doctor, appointment.service, new_date,
        )
        slot_available = any(
            s['start'] == new_time.strftime('%H:%M') for s in slots
        )
        # El slot puede ser el actual de la cita (sin cambio) — eso también vale.
        is_same_slot = (
            appointment.date == new_date and appointment.start_time == new_time
        )
        if not slot_available and not is_same_slot:
            return Response(
                {'detail': 'Este horario ya no está disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calcular nuevo end_time
        new_end = (datetime.combine(new_date, new_time)
                   + timedelta(minutes=appointment.service.duration)).time()

        appointment.date = new_date
        appointment.start_time = new_time
        appointment.end_time = new_end
        # Reset a 'pending' si la clínica requería confirmación, igual que en
        # una cita nueva. Si era 'confirmed' la dejamos así.
        appointment.save(update_fields=['date', 'start_time', 'end_time', 'updated_at'])

        return Response(AppointmentSerializer(appointment).data)

    def delete(self, request, appointment_id):
        """Cancelar la cita (no la borra, solo cambia status)."""
        from apps.bookings.models import AppointmentStatus
        from apps.bookings.serializers import AppointmentSerializer

        appointment, err = self._get_appointment(request, appointment_id)
        if err:
            return err

        guard = self._validate_modifiable(appointment)
        if guard:
            return guard

        appointment.status = AppointmentStatus.CANCELLED
        appointment.save(update_fields=['status', 'updated_at'])
        return Response(AppointmentSerializer(appointment).data)
