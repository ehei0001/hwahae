from django.db import models
            


# Create your models here.
class Item(models.Model):
    id = models.IntegerField(primary_key=True)
    imageId = models.CharField(max_length=512, null=True)
    name = models.CharField(max_length=100, db_index=True)
    price = models.PositiveIntegerField(db_index=True, default=9999999)
    gender = models.CharField(max_length=6, db_index=True, default='all')
    category = models.CharField(max_length=256, db_index=True, default='etc')
    ingredients = models.TextField(max_length=512, default='')
    monthlySales = models.IntegerField(default=0)
    oilyScore = models.SmallIntegerField(default=0)
    dryScore = models.SmallIntegerField(default=0)
    sensitiveScore = models.SmallIntegerField(default=0)