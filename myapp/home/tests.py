import functools
import operator
from django.db.models import Max, Q
from django.test import TestCase
from myapp.item.models import Item

# Create your tests here.
class QueryTest(TestCase):
    fixtures = ['db.json']


    def setUp(self) -> None:
        self.entries = Item.objects


    def test_categoryQuery(self) -> None:
        result = self.entries.filter(category__iexact='suncare')
        self.assertGreater(len(result), 0)

        result = self.entries.filter(category__iexact='xxxxxx')
        self.assertEqual(len(result), 0)


    def test_skinTypeQuery(self) -> None:
        value = self.entries.all().aggregate(Max('oilyScore'))
        result = self.entries.order_by('-oilyScore')[0]
        self.assertEqual(result.oilyScore, next(iter(value.values())))


    def test_pageQuery(self) -> None:
        offset = 10
        limit = 5
        result = self.entries.all()[offset:offset + limit]
        self.assertEqual(len(result), limit)


    def test_excludeIngredientQuery(self) -> None:
        '''
        select name from mydb.item_item
        where ingredients not like '%multimedia%' and ingredients not like '%provision%'
        '''
        ingredient0 = 'multimedia'
        ingredient1 = 'provision'
        result = self.entries.exclude(Q(ingredients__icontains=ingredient0) | Q(ingredients__icontains=ingredient1))
        self.assertEqual(988, len(result))

        # https: // stackoverflow.com / questions / 34739680 / how - to - add - filters - to - a - query - dynamically - in -django
        queries = (Q(ingredients__icontains=ingredient0), Q(ingredients__icontains=ingredient1))
        result = self.entries.exclude(functools.reduce(operator.or_, queries))
        self.assertEqual(988, len(result))


    def test_includeIngredientQuery(self) -> None:
        '''
        select name from mydb.item_item
        where ingredients like '%multimedia%' and ingredients like '%provision%'
        '''
        ingredient0 = 'multimedia'
        ingredient1 = 'provision'
        result = self.entries.filter(Q(ingredients__icontains=ingredient0) & Q(ingredients__icontains=ingredient1))
        self.assertEqual(1, len(result))
        pass