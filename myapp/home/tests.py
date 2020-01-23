import functools
import json
import operator
from django.db.models import Max, Q
from django.http import HttpRequest
from django.test import Client, RequestFactory, TestCase
from myapp.item.models import Item
from myapp.home.views import _build_image_url, _get_arguments, product, products, ITEM_PER_PAGE, RESOURCE_URL, \
    MAX_RECOMMEND_ITEM_COUNT


# Create your tests here.
class FunctionTest(TestCase):
    def test_buildImageUrl(self) -> None:
        url = _build_image_url('test')
        self.assertTrue(url.startswith(RESOURCE_URL))
        self.assertTrue(url.endswith('.jpg'))
        self.assertIn('/thumbnail/', url)

        url = _build_image_url('test', is_thumbnail=False)
        self.assertTrue(url.startswith(RESOURCE_URL))
        self.assertTrue(url.endswith('.jpg'))
        self.assertIn('/image/', url)

    def test_getArguments(self) -> None:
        request = RequestFactory().get(
            '/products?skin_type=oily&category=skincare&page=3&include_ingredient=Glycerin,Nitro&exclude_ingredient=A,B,C')
        arguments = _get_arguments(request)
        self.assertEqual('oily', arguments['skin_type'])
        self.assertEqual('skincare', arguments['category'])
        self.assertEqual(3, arguments['page'])
        self.assertEqual(2, len(arguments['include_ingredient']))
        self.assertEqual(3, len(arguments['exclude_ingredient']))


class QueryTest(TestCase):
    fixtures = ['items-data.json']

    def setUp(self) -> None:
        self.entries = Item.objects
        self.client = Client()
        self.requestFactory = RequestFactory()

    def test_errorTest(self) -> None:
        request = HttpRequest()
        response = products(request)
        self.assertEqual(500, response.status_code)

        request = self.requestFactory.get('/products?skin_type=xxxx')
        response = products(request)
        self.assertEqual(500, response.status_code)

        request = self.requestFactory.get('/product/xxx')
        response = products(request)
        self.assertEqual(500, response.status_code)

        request = self.requestFactory.get('/product')
        response = product(request, item_id=17)
        self.assertEqual(500, response.status_code)

        request = self.requestFactory.get('/product/17?skin_type=xxxx')
        response = product(request, item_id=17)
        self.assertEqual(500, response.status_code)

    def test_productsTest(self) -> None:
        request = self.requestFactory.get('/products?skin_type=dry')
        response = products(request)
        self.assertGreaterEqual(ITEM_PER_PAGE, len(json.loads(response.content)))

        request = self.requestFactory.get('/products?skin_type=oily&category=skincare')
        response = products(request)
        self.assertGreaterEqual(ITEM_PER_PAGE, len(json.loads(response.content)))

        request = self.requestFactory.get('/products?skin_type=oily&category=skincare&include_ingredient=mechanism')
        response = products(request)
        self.assertGreaterEqual(3, len(json.loads(response.content)))

        # 건성일 때 점수가 같은 것이 나오는 쿼리
        request = self.requestFactory.get(
            '/products?skin_type=dry&category=skincare&include_ingredient=mechanism&exclude_ingredient=moral')
        response = products(request)
        results = json.loads(response.content)
        self.assertEqual(2, len(results))
        self.assertLessEqual(results[0]['price'], results[1]['price'], '점수가 같으면 가격을 오름차순 정렬해야 합니다')

        # 엄지 그림이 들었는지 검사
        for result in results:
            img_url = result['imgUrl']
            self.assertTrue(img_url.startswith(RESOURCE_URL))
            self.assertIn('/thumbnail/', img_url)

        request = self.requestFactory.get(
            '/products?skin_type=oily&category=skincare&include_ingredient=mechanism,burial')
        response = products(request)
        self.assertGreaterEqual(1, len(json.loads(response.content)))

    def test_productTest(self) -> None:
        request = self.requestFactory.get('/product/17?skin_type=oily')
        response = product(request, item_id=7)
        results = json.loads(response.content)
        self.assertGreaterEqual(4, len(results))
        self.assertIn('/image/', results[0]['imgUrl'])
        self.assertEqual(MAX_RECOMMEND_ITEM_COUNT, len(results[1:]), '추천 개수는 제한됩니다')

        for result in results[1:]:
            img_url = result['imgUrl']
            self.assertIn('/thumbnail/', img_url)

        item_ids = set(result['id'] for result in results)
        self.assertEqual(4, len(item_ids), '동일 상품이 나와서는 안됩니다')

    def test_categoryQuery(self) -> None:
        """
        select * from mydb.item_item
        where category='suncare'
        """
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
        """
        select name from mydb.item_item
        where ingredients not like '%multimedia%' and ingredients not like '%provision%'
        """
        ingredient0 = 'multimedia'
        ingredient1 = 'provision'
        result = self.entries.exclude(Q(ingredients__icontains=ingredient0) | Q(ingredients__icontains=ingredient1))
        self.assertEqual(988, len(result))

        queries = (Q(ingredients__icontains=ingredient0), Q(ingredients__icontains=ingredient1))
        result = self.entries.exclude(functools.reduce(operator.or_, queries))
        self.assertEqual(988, len(result))

    def test_includeIngredientQuery(self) -> None:
        """
        select name from mydb.item_item
        where ingredients like '%multimedia%' and ingredients like '%provision%'
        """
        ingredient0 = 'multimedia'
        ingredient1 = 'provision'
        result = self.entries.filter(Q(ingredients__icontains=ingredient0) & Q(ingredients__icontains=ingredient1))
        self.assertEqual(1, len(result))