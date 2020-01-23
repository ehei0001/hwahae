import collections
import functools
import operator
import urllib.parse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
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


# Create your views here.
def index(request):
    return render(request, 'index.html', {})


def products(request):
    '''제품 목록을 반환

    예: skin_type=oily&category=skincare&page=3&include_ingredient=Glycerin
    '''
    arguments = __getArguments(request)

    skinTypeKey = 'skin_type'
    skinType = arguments.get(skinTypeKey)
    if skinType is None:
        return HttpResponse('skin_type field must be exist', status=500)

    entries = Item.objects
    databaseField = SKIN_TYPE_TO_DATABASE_FIELDS[skinType]
    entries = entries.order_by(databaseField, 'price')

    if entries:
        category = arguments.get('category')
        if category is not None:
            entries = entries.filter(category__iexact=category)

        queries = __buildIngredientQueries(arguments, 'exclude_ingredient', operator.or_)
        if queries is not None:
            entries = entries.exclude(queries)

        queries = __buildIngredientQueries(arguments, 'include_ingredient', operator.and_)
        if queries is not None:
            entries = entries.filter(queries)

        page = arguments.get('page')
        if page is None:
            entries = entries[:ITEM_PER_PAGE]
        else:
            currentCount = ITEM_PER_PAGE * page
            entries = entries[currentCount:currentCount + ITEM_PER_PAGE]

        fields = (
            'id',
            'name',
            'price',
            'ingredients',
            'monthlySales',
        )
        results = []
        for entry in entries:
            result = __extractDataFromEntry(entry, fields, True)
            results.append(result)

        return JsonResponse(results, safe=False, json_dumps_params=JSON_PARAMETERS)
    else:
        return JsonResponse([], safe=False)


def detail(request, item_id):
    '''상품 세부 정보를 반환

    예: skin_type=oily
    '''
    assert isinstance(item_id, int)

    entries = Item.objects
    itemEntry = entries.get(id__exact=item_id)

    if itemEntry is None:
        return HttpResponse('item is not exists', status=500)

    arguments = __getArguments(request)

    skinTypeKey = 'skin_type'
    skinType = arguments.get(skinTypeKey)
    if skinType is None:
        return HttpResponse('skin_type field must be exist', status=500)

    fields = (
        'id',
        'name',
        'price',
        'gender',
        'category',
        'ingredients',
        'monthlySales',
    )
    result = __extractDataFromEntry(itemEntry, fields, False)
    results = [result]

    recommendItemEntries = entries.filter(category__exact=itemEntry.category)
    databaseField = SKIN_TYPE_TO_DATABASE_FIELDS[skinType]
    recommendItemEntries = recommendItemEntries.order_by(databaseField, 'price')

    fields = (
        'id',
        'name',
        'price',
    )
    for entry in recommendItemEntries[:MAX_RECOMMEND_ITEM_COUNT]:
        result = __extractDataFromEntry(entry, fields, True)
        results.append(result)

    return JsonResponse(results, safe=False, json_dumps_params=JSON_PARAMETERS)


def __getArguments(request) -> '{str: object}':
    result = {}

    singleArguments = (
        ('skin_type', str),
        ('category', str),
        ('page', int),
    )
    for argument, valueType in singleArguments:
        value = request.GET.get(argument)
        if value:
            value = valueType(value)
            result[argument] = value

    multipleArguments = ('exclude_ingredient', 'include_ingredient')
    for argument in multipleArguments:
        value = request.GET.get(argument)
        if value:
            result[argument] = set(value.split(','))

    return result


def __buildIngredientQueries(arguments, keyword, operatorType) -> 'None or Q':
    assert isinstance(arguments, collections.abc.Mapping)
    assert isinstance(keyword, str)
    assert operatorType in (operator.or_, operator.and_)

    ingredients = arguments.get(keyword)
    if ingredients is None:
        return None
    else:
        queries = []
        for ingredient in ingredients:
            query = Q(ingredients__icontains=ingredient)
            queries.append(query)

        return functools.reduce(operatorType, queries)


def __buildImageURL(imageID, isThumbnail = True) -> str:
    assert isinstance(imageID, str)
    assert isinstance(isThumbnail, bool)

    if isThumbnail:
        path = 'https://grepp-programmers-challenges.s3.ap-northeast-2.amazonaws.com/2020-birdview/thumbnail/'
    else:
        path = 'https://grepp-programmers-challenges.s3.ap-northeast-2.amazonaws.com/2020-birdview/image/'

    return urllib.parse.urljoin(path,imageID + '.jpg')


def __extractDataFromEntry(entry, fields, isThumbnail) -> '{str: object}':
    assert isinstance(fields, collections.abc.Sequence)
    assert isinstance(isThumbnail, bool)

    result = {}

    for field in fields:
        value = entry.__getattribute__(field)
        result[field] = value

    imageUrl = __buildImageURL(entry.imageId, isThumbnail)
    result['imgUrl'] = imageUrl

    return result
