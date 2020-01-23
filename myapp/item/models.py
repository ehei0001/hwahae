from django.db import models


ITEM_NAME = 100
INGREDIENT_NAME = 100
            


# Create your models here.
class Item(models.Model):
    id = models.IntegerField(primary_key=True)
    imageId = models.CharField(max_length=512, null=True)
    name = models.CharField(max_length=ITEM_NAME, db_index=True)
    price = models.PositiveIntegerField(db_index=True, default=9999999)
    gender = models.CharField(max_length=6, db_index=True, default='all')
    category = models.CharField(max_length=256, db_index=True, default='etc')
    ingredients = models.TextField(max_length=512, default='')
    monthlySales = models.IntegerField(default=0)
    oilyScore = models.SmallIntegerField(default=0)
    dryScore = models.SmallIntegerField(default=0)
    sensitiveScore = models.SmallIntegerField(default=0)



class Ingredient(models.Model):
    name = models.CharField(max_length=INGREDIENT_NAME, primary_key=True, unique=True)
    oily = models.SmallIntegerField()
    dry = models.SmallIntegerField()
    sensitive = models.SmallIntegerField()



class ItemToIngredient(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='itemID', db_index=True)
    ingredient = models.CharField(max_length=INGREDIENT_NAME, default='', db_index=True)