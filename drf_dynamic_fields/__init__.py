"""
Mixin to dynamically select only a subset of fields per DRF resource.
"""
from collections import OrderedDict
import warnings

from django.utils.functional import cached_property


class DynamicFieldsMixin(object):
    """
    A serializer mixin that takes an additional `fields` argument that controls
    which fields should be displayed.
    """

    @cached_property
    def _readable_fields_dict(self):
        return OrderedDict(
            (name, field) for name, field in self.fields.items()
            if not field.write_only
        )

    @property
    def _readable_fields(self):
        return self._filtered_readable_fields_dict().values()

    def _filtered_readable_fields_dict(self):
        """
        Filters the fields according to the `fields` query parameter.

        a blank `fields` parameter (?fields) will remove all fields.
        not passing `fields` will pass all fields
        individual fields are comma separated (?fields=id,name,url,email)
        """
        fields = self._readable_fields_dict

        if not hasattr(self, '_context'):
            # we are being called before a request cycle.
            return fields

        try:
            request = self.context['request']
        except KeyError:
            warnings.warn('Context does not have access to request')
            return fields

        # NOTE: drf test framework builds a request object where the query
        # parameters are found under the GET attribute.
        params = getattr(
            request, 'query_params', getattr(request, 'GET', None)
        )
        if params is None:
            warnings.warn('Request object does not contain query paramters')

        try:
            filter_fields = params.get('fields', None).split(',')
        except AttributeError:
            filter_fields = None

        try:
            omit_fields = params.get('omit', None).split(',')
        except AttributeError:
            omit_fields = []

        # Drop any fields that are not specified in the `fields` argument.
        existing = set(fields.keys())
        if filter_fields is None:
            # no fields param given, don't filter.
            allowed = existing
        else:
            allowed = set(filter(None, filter_fields))

        # omit fields in the `omit` argument.
        omitted = set(filter(None, omit_fields))

        for field in existing:

            if field not in allowed:
                fields.pop(field, None)

            if field in omitted:
                fields.pop(field, None)

        return fields
