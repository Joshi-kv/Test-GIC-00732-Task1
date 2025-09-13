from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.v1.serializers.uploader import FileUploadSerializer


class FileUploadView(APIView):
    
    """
    Handle file uploads and process them.
    
    endpoint: /api/v1/upload-file/
    Method: POST
    it accepts a csv file and processes it using FileUploadSerializer.
    
    Returns:
        dict: success status, message, and data or errors.
    """
    
    with transaction.atomic():
        def post(self, request, *args,  **kwargs):
            try:
                serializer = FileUploadSerializer(data=request.data)
                if serializer.is_valid():
                    result = serializer.save()
                    response = {
                        'success': True,
                        'message': 'File processed successfully.',
                        'data': result
                    }
                    return Response(response, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'errors': {key: serializer.errors[key][0] for key in serializer.errors.keys()}
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)