"""
Hospitals — Django ORM Models
===============================
The Hospital entity is the multi-tenant root. Every user, patient, log, and
clinical record belongs to exactly one hospital.
"""

import string
import random
from django.db import models


class Hospital(models.Model):
    """Top-level organizational unit enforcing data isolation across tenants."""

    id = models.CharField(primary_key=True, max_length=50, editable=False)
    name = models.CharField(max_length=255)
    logo = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            initials = "".join([word[0].upper() for word in self.name.split() if word])
            if not initials:
                initials = "H" # Fallback if name is empty
            while True:
                random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                new_id = f"{initials}-{random_chars}"
                if not Hospital.objects.filter(id=new_id).exists():
                    self.id = new_id
                    break
        super().save(*args, **kwargs)
