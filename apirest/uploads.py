"""
Endpoint genérico para subir imágenes (logos del tenant y del platform).
Cualquier usuario autenticado puede subir. El archivo queda en MEDIA_ROOT/logos/
y se devuelve una URL pública absoluta.

POST /rest/v1/uploads/logo/  (multipart/form-data, field='file')
→ 201 { "url": "http://localhost:8000/media/logos/<uuid>.<ext>" }
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


ALLOWED_TYPES = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    'image/gif': '.gif',
}
MAX_BYTES = 2 * 1024 * 1024  # 2 MB


class LogoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        f = request.FILES.get('file')
        if f is None:
            return Response({'error': 'Falta el campo "file".'}, status=status.HTTP_400_BAD_REQUEST)

        ext = ALLOWED_TYPES.get(f.content_type)
        if ext is None:
            return Response(
                {'error': f'Tipo no permitido: {f.content_type}. Acepta PNG, JPG, WEBP, SVG, GIF.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if f.size > MAX_BYTES:
            return Response(
                {'error': f'El archivo excede {MAX_BYTES // (1024 * 1024)} MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = f'logos/{uuid.uuid4().hex}{ext}'
        saved = default_storage.save(filename, f)

        media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else settings.MEDIA_URL + '/'
        absolute = request.build_absolute_uri(f'/{media_url.lstrip("/")}{saved}')
        return Response({'url': absolute}, status=status.HTTP_201_CREATED)
