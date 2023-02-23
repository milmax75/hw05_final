from django.db import models


class CreatedModel(models.Model):
    """Abstract model. Adds creation date."""
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        # This is an abstract model:
        abstract = True
