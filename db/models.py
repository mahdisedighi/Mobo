from django.db import models
from django.utils import timezone

class Product(models.Model):
    id = models.IntegerField(primary_key=True)
    identifier = models.CharField(max_length=128 , null=True, blank=True, unique=True)
    product_hash = models.CharField(null=True, blank=True, max_length=32)
    from_mobo = models.BooleanField(null=True, blank=True)
    commit = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    composed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.created_at = timezone.now().replace(microsecond=0)
        super().save(*args, **kwargs)


