import collections
import functools
import operator
import urllib.parse
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from myapp.item.models import Item


SKIN_TYPE_TO_DATABASE_FIELDS = {
    'oily' : '-oilyScore',
    'dry' : '-dryScore',
    'sensitive' : '-sensitive',
}
ITEM_PER_PAGE = 50
JSON_PARAMETERS = {'ensure_ascii': False}
if __debug__:
    JSON_PARAMETERS['indent'] = 4
    JSON_PARAMETERS['sort_keys'] = True

MAX_RECOMMEND_ITEM_COUNT = 3
RESOURCE_URL = 'https://grepp-programmers-challenges.s3.ap-northeast-2.amazonaws.com/2020-birdview/'


# Create your views here.
def index(request) -> 'HttpResponse':
    assert isinstance(request, HttpRequest)

    return render(request, 'index.html', {})


def products(request) -> 'HttpResponse':
    """제품 목록을 반환
    """
    assert isinstance(request, HttpRequest)

    arguments = _get_arguments(request)

    skin_type_key = 'skin_type'
    skin_type = arguments.get(skin_type_key)
    if skin_type is None:
        return HttpResponse('skin_type field must be exist', status=500)
    else:
        assert isinstance(skin_type, str)

    entries = Item.objects

    if skin_type not in SKIN_TYPE_TO_DATABASE_FIELDS:
        return HttpResponse('skin_type is wrong', status=500)

    database_field = SKIN_TYPE_TO_DATABASE_FIELDS[skin_type]
    entries = entries.order_by(database_field, 'price')

    if entries:
        category = arguments.get('category')
        if category is not None:
            entries = entries.filter(category__iexact=category)

        queries = _build_ingredient_queries(arguments, 'exclude_ingredient', operator.or_)
        if queries is not None:
            entries = entries.exclude(queries)

        queries = _build_ingredient_queries(arguments, 'include_ingredient', operator.and_)
        if queries is not None:
            entries = entries.filter(queries)

        page = arguments.get('page')
        if page is None:
            entries = entries[:ITEM_PER_PAGE]
        else:
            current_count = ITEM_PER_PAGE * page
            entries = entries[current_count:current_count + ITEM_PER_PAGE]

        if entries:
            fields = (
                'id',
                'name',
                'price',
                'ingredients',
                'monthlySales',
            )
            results = []
            for entry in entries:
                result = _extract_data_from_entry(entry, fields, True)
                results.append(result)

            return JsonResponse(results, safe=False, json_dumps_params=JSON_PARAMETERS)

    return JsonResponse([], safe=False)


def product(request, item_id) -> 'HttpResponse':
    """상품 세부 정보를 반환
    """
    assert isinstance(request, HttpRequest)
    assert isinstance(item_id, int)

    entries = Item.objects
    item_entry = entries.get(id__exact=item_id)

    if item_entry is None:
        return HttpResponse('item is not exists', status=500)

    arguments = _get_arguments(request)

    skin_type = arguments.get('skin_type')
    if skin_type is None:
        return HttpResponse('skin_type field must be exist', status=500)
    else:
        assert isinstance(skin_type, str)
        assert skin_type

    if skin_type not in SKIN_TYPE_TO_DATABASE_FIELDS:
        return HttpResponse('skin_type is wrong', status=500)

    fields = (
        'id',
        'name',
        'price',
        'gender',
        'category',
        'ingredients',
        'monthlySales',
    )
    result = _extract_data_from_entry(item_entry, fields, False)
    results = [result]

    recommend_item_entries = entries.filter(category__exact=item_entry.category)
    recommend_item_entries = recommend_item_entries.exclude(id__exact=item_id)
    database_field = SKIN_TYPE_TO_DATABASE_FIELDS[skin_type]
    recommend_item_entries = recommend_item_entries.order_by(database_field, 'price')

    fields = (
        'id',
        'name',
        'price',
    )
    for entry in recommend_item_entries[:MAX_RECOMMEND_ITEM_COUNT]:
        result = _extract_data_from_entry(entry, fields, True)
        results.append(result)

    return JsonResponse(results, safe=False, json_dumps_params=JSON_PARAMETERS)


def _get_arguments(request) -> '{str: object}':
    assert isinstance(request, HttpRequest)

    result = {}

    single_arguments = (
        ('skin_type', str),
        ('category', str),
        ('page', int),
    )
    for argument, valueType in single_arguments:
        value = request.GET.get(argument)
        if value:
            value = valueType(value)
            result[argument] = value

    multiple_arguments = ('exclude_ingredient', 'include_ingredient')
    for argument in multiple_arguments:
        value = request.GET.get(argument)
        if value:
            result[argument] = set(value.split(','))

    return result


def _build_ingredient_queries(arguments, keyword, operator_type) -> 'None or Q':
    assert isinstance(arguments, collections.abc.Mapping)
    assert isinstance(keyword, str)
    assert operator_type in (operator.or_, operator.and_)

    ingredients = arguments.get(keyword)
    if ingredients is None:
        return None
    else:
        queries = []
        for ingredient in ingredients:
            query = Q(ingredients__icontains=ingredient)
            queries.append(query)

        return functools.reduce(operator_type, queries)


def _build_image_url(image_id, is_thumbnail = True) -> str:
    assert isinstance(image_id, str)
    assert isinstance(is_thumbnail, bool)

    if is_thumbnail:
        path = 'thumbnail'
    else:
        path = 'image'

    file_name = image_id + '.jpg'
    path = '/'.join((path, file_name))

    return urllib.parse.urljoin(RESOURCE_URL, path)


def _extract_data_from_entry(entry, fields, is_thumbnail) -> '{str: object}':
    assert isinstance(entry, Item)
    assert isinstance(fields, collections.abc.Sequence)
    assert isinstance(is_thumbnail, bool)

    result = {}

    for field in fields:
        value = entry.__getattribute__(field)
        result[field] = value

    image_url = _build_image_url(entry.imageId, is_thumbnail)
    result['imgUrl'] = image_url

    return result
