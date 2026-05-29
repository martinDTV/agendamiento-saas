"""Correos del flujo de reseñas anónimas."""
from shared.emails import build_app_link, send_branded_email

from .models import PendingReview


def send_review_confirmation_email(pending: PendingReview) -> None:
    """
    Manda link de verificación a la persona que dejó una reseña anónima.

    Solo al hacer click se publica la reseña. Esto evita:
      - Reseñas con emails inventados (no llega el correo, no se publica)
      - Bots que envíen masivamente
      - Spam contra competidores (la persona dueña del email debe confirmar)
    """
    confirm_path = f'/rest/v1/public/reviews/confirm/?token={pending.token}'
    confirm_url = build_app_link(confirm_path)

    send_branded_email(
        subject=f'Confirma tu reseña sobre {pending.doctor}',
        to=pending.reviewer_email,
        template_name='reviews/confirm_email.html',
        text_template='reviews/confirm_email.txt',
        context={
            'reviewer_name': pending.reviewer_name,
            'doctor_name': str(pending.doctor),
            'rating': pending.rating,
            'comment': pending.comment,
            'confirm_url': confirm_url,
            'cta_url': confirm_url,
            'cta_label': 'Confirmar mi reseña',
        },
    )
