from django.db import models

class Medicine(models.Model):
    name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def _str_(self):
        return self.name