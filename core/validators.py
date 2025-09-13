from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from pathlib import Path
import mimetypes


@deconstructible
class FileValidator(object):
    error_messages = {
        'max_size': _("The file size less than or equal to %(max_size)s"),
        'min_size': _("Ensure this file size is not less than %(min_size)s. "
                  "Your file size is %(size)s."),
        'content_type': _("Files of type %(content_type)s are not supported."),
        'allowed_extensions': _("File extension \"%(extension)s\" is not allowed. "
                        "Allowed extensions are: %(allowed_extensions)s."),

    }

    def __init__(self, max_size=None, min_size=None, content_types=(), allowed_extensions=None,):
        self.max_size = max_size
        self.min_size = min_size
        self.content_types = content_types
        if allowed_extensions is not None:
            allowed_extensions = [
                allowed_extension.lower() for allowed_extension in allowed_extensions
            ]
        self.allowed_extensions = allowed_extensions

    def __call__(self, data):
        if self.max_size is not None and data.size > self.max_size:
            params = {
                'max_size': filesizeformat(self.max_size), 
                'size': filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages['max_size'],
                                   'max_size', params)

        if self.min_size is not None and data.size < self.min_size:
            params = {
                'min_size': filesizeformat(self.min_size),
                'size': filesizeformat(data.size)
            }
            raise ValidationError(self.error_messages['min_size'], 
                                   'min_size', params)

        if self.content_types:
            content_type, _ = mimetypes.guess_type(data.name)
            if content_type is None:
                content_type = 'application/octet-stream'
            if content_type not in self.content_types:
                params = { 'content_type': content_type }
                raise ValidationError(self.error_messages['content_type'],
                                   'content_type', params)
        
        if self.allowed_extensions:
            extension = Path(data.name).suffix[1:].lower()
            if (
                self.allowed_extensions is not None
                and extension not in self.allowed_extensions
            ):
                raise ValidationError(
                    self.error_messages['allowed_extensions'],
                    params={
                        "extension": extension,
                        "allowed_extensions": ", ".join(self.allowed_extensions),
                        "value": data,
                    },
                )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.max_size == other.max_size and
            self.min_size == other.min_size and
            self.content_types == other.content_types and
            self.allowed_extensions == other.allowed_extensions
        )