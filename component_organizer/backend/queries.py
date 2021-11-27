import re
from functools import reduce

from django.db.models import Count

from backend.models import StringValue, Item, Dict


def get_keys(at_least: int = 1):
    """
    Get all StringValues used as keys and annotate them with how many times they are used.

    :param at_least: how often has a StringValue to be used as key to show up (default: 1)
    :type at_least: int
    :return: annotated queryset of StringValues
    """
    annotations = {}
    for type_, model in Dict.KVP_MODELS.items():
        annotations[f"amount_{type_.__name__}"] = Count(f"{model.__name__.lower()}__key")
    annotations["amount_total"] = sum(annotations.values())

    return StringValue.objects.annotate(**annotations).filter(amount_total__gte=at_least).order_by("amount_total").all()


_separator = re.compile(r" *(?<!\\), *")
_query = re.compile(r"^([^=<>]+) *(=|<=|>=|<|>) *(.+)$")
_operators = {
    "=": "",
    "<": "__lt",
    ">": "__gt",
    "<=": "__lte",
    ">=": "__gte",
}


def filter_items(string, queryset=None):
    """
    Parse an item query into a Queryset
    """
    if queryset is None:
        queryset = Item.objects.all()

    parsed_queries = []
    raw_queries = _separator.split(string)
    print(raw_queries)
    for query in raw_queries:
        try:
            key, op, value = _query.match(query).groups()
        except AttributeError:  # match is None
            continue
        print(op)

        try:
            value = float(value)
        except ValueError:
            pass

        parsed_queries.append(
            Dict.KVP_MODELS[type(value)].objects
                .filter(key__value=key, **{f"value__value{_operators[op]}": value})
                .values_list("owner_id")
        )

    if parsed_queries:
        return queryset.filter(id__in=reduce(lambda a, b: a.intersection(b), parsed_queries))
    else:
        return queryset.all()
