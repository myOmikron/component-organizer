import re
from typing import Iterator

from django.db.models import Count, QuerySet

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

    return StringValue.objects.annotate(**annotations) \
                              .filter(amount_total__gte=at_least) \
                              .order_by("-amount_total", "value").all()


def get_values(key: str, at_least: int = 1):
    """
    Get all ...Values stored under the given key and annotate them with how often they are used.

    :param key: key to get values for
    :type key: str
    :param at_least: how often has a StringValue to be used as key to show up (default: 1)
    :type at_least: int
    :return: annotated list of StringValues, FloatValues and so on
    """
    values = set()
    for type_, kvp in Dict.KVP_MODELS.items():
        val = Dict.VALUE_MODELS[type_]
        values.update(val.objects.filter(variable__in=kvp.objects.filter(key__value=key)) \
                         .annotate(uses=Count("variable")) \
                         .filter(uses__gte=at_least))
    return list(values)


def filter_items(string: str, /, queryset: QuerySet = None, queried_keys: set = None) -> QuerySet:
    """
    Parse an item query into a Queryset

    :param string: Query to parse
    :type string: str
    :param queryset: An optional queryset to base the resulting one on
    :type queryset: QuerySet
    :param queried_keys: A optional set the keys used in the query are put in
    :type queried_keys: empty set
    :return: queryset represented by the query string
    :rtype: QuerySet
    """
    if queryset is None:
        queryset = Item.objects.all()
    string = string.strip()
    if string:
        return queryset.filter(id__in=_parse_bracket(iter(string), queried_keys))
    else:
        return queryset.all()


_comparison_operators = {
    "=": "",
    "<": "__lt",
    ">": "__gt",
    "<=": "__lte",
    ">=": "__gte",
}
_logic_operators = {
    "|": QuerySet.union,
    "&": QuerySet.intersection,
}


def _parse_lookup(string: str, queried_keys: set = None) -> QuerySet:
    """
    Parse a key-comparator-value string into a QuerySet of item ids.

    :param string: something like "  Foo = bar" (leading and trailing whitespaces are stripped)
    :type string: str
    :param queried_keys: A optional set the keys used in the query are put in
    :type queried_keys: set
    :return: QuerySet of matching items' ids
    :rtype: QuerySet of tuples with a single int
    """
    comparator = re.search(r"(?<!\\)(?:=|<=|>=|<|>)", string)
    if comparator is None:
        raise ValueError("No comparator found.")
    else:
        a, b = comparator.span()
        key = string[:a].strip()
        op = comparator.group()
        value = string[b:].strip()

    try:
        value = float(value)
    except ValueError:
        pass

    if queried_keys is not None:
        queried_keys.add(key)
    return Dict.KVP_MODELS[type(value)].objects \
        .filter(key__value=key, **{f"value__value{_comparison_operators[op]}": value}) \
        .values_list("owner_id")


def _parse_bracket(string_iter: Iterator[str], queried_keys: set = None) -> QuerySet:
    """
    Parse an item query from a string iterator.
    This goes through the string calls `_parse_lookup` or itself recursively and combines the result using and/or.

    :param string_iter: iterator over an item query to parse
    :type string_iter: Iterator[str]
    :param queried_keys: A optional set the keys used in the query are put in
    :type queried_keys: set
    :return: QuerySet of matching items' ids
    :rtype: QuerySet of tuples with a single int
    """
    if isinstance(string_iter, str):
        string_iter = iter(string_iter)

    result = None
    combinator = lambda x, y: y
    lookup = ""
    query = None
    escaped = False
    for char in string_iter:
        query = None
        if escaped:
            lookup += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "(":
            query = _parse_bracket(string_iter, queried_keys)
        elif char == ")":
            break
        elif char in _logic_operators:
            if query is None:
                query = _parse_lookup(lookup, queried_keys)
            lookup = ""
            result = combinator(result, query)
            query = None
            combinator = _logic_operators[char]
        else:
            lookup += char

    if query is None:
        query = _parse_lookup(lookup, queried_keys)
    return combinator(result, query)
