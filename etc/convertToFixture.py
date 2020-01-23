import collections
import json


db = []
itemToIngredients = collections.defaultdict(set)
appName = 'item'
ingredientScores = collections.defaultdict(dict)

# 피부 별 점수를 얻기 위해 먼저 처리
with open('ingredient-data.json', encoding='utf-8') as f:
    modelName = '.'.join( ( appName, 'Ingredient' ) )

    for record in json.load(f):
        name = record['name']
        assert name not in ingredientScores

        for field in ('oily', 'dry', 'sensitive'):
            value = record[field]

            if value == 'O':
                value = 1
            elif value == 'X':
                value = -1
            else:
                assert not value

                value = 0

            record[field] = value
            ingredientScores[name][field] = value

        record = {
            'model': modelName,
            'fields' : record,
        }

with open('item-data.json', encoding='utf-8') as f:
    records = json.load(f)
    priceKey = 'price'
    modelName = '.'.join( ( appName, 'Item' ) )

    for i, record in enumerate(records):
        record[priceKey] = int(record[priceKey])
        ingredients = record['ingredients']
        index = record['id']
        oilyScore = 0
        dryScore = 0
        sensitiveScore = 0

        for ingredient in ingredients.split(','):
            itemToIngredients[index].add(ingredient)

            # 성분이 피부 별로 몇 점에 해당하는지 계산
            ingredientScore = ingredientScores[ingredient]
            oilyScore += ingredientScore['oily']
            dryScore += ingredientScore['dry']
            sensitiveScore += ingredientScore['sensitive']

        record['oilyScore'] = oilyScore
        record['dryScore'] = dryScore
        record['sensitiveScore'] = sensitiveScore
        record = {
            'model': modelName,
            'fields': record,
        }
        db.append(record)

with open('../myapp/item/fixtures/items-data.json', 'w', encoding='utf-8') as f:
    json.dump(db, f)