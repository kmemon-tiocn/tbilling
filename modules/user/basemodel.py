import uuid
import copy
from django.db import models
from django.forms.models import model_to_dict

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    update_history = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = type(self).objects.get(pk=self.pk)
            except type(self).DoesNotExist:
                old_instance = None
            if old_instance:
                old_data = model_to_dict(old_instance)
                new_data = model_to_dict(self)
                update_record = []
                for field, old_value in old_data.items():
                    if 'update_history' in field:
                        continue
                    new_value = new_data.get(field)
                    if old_value != new_value:
                        update_record.append({
                            'note': f'Field "{field}" updated from "{old_value}" to "{new_value}"',
                            'field': field,
                            'updated_by': str(self.updated_by),
                            'updated_at': self.updated_at.isoformat(),
                        })
                if update_record:
                    if self.update_history is None:
                        self.update_history = []
                    self.update_history.extend(copy.deepcopy(update_record))
        super().save(*args, **kwargs)
