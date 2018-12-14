# -*- coding: utf-8 -*-

from datetimewidget.widgets import DateWidget
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm, ValidationError
from django.forms.models import modelform_factory
from django.http import HttpResponse
from django.template import loader
from django.utils.decorators import method_decorator
from django.views import generic
# from django.views.decorators.cache import cache_page
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm
from leaflet.forms.widgets import LeafletWidget
import requests
import re



def assign_widgets(field, widget = None):
    if field.name == 'geometrie':
        return field.formfield(widget = LeafletWidget())
    elif field.__class__.__name__ == 'DateField':
        return field.formfield(widget = DateWidget(usel10n = True, bootstrap_version = 3))
    else:
        return field.formfield()


class AddressSearchView(generic.View):
    http_method_names = ['get',]
    
    def dispatch(self, request, *args, **kwargs):
        self.addresssearch_type = 'search'
        self.addresssearch_class = 'address'
        self.addresssearch_query = 'rostock ' + request.GET.get('query', '')
        self.addresssearch_out_epsg = '4326'
        self.addresssearch_shape = 'bbox'
        self.addresssearch_limit = '5'
        return super(AddressSearchView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        response = requests.get(settings.ADDRESS_SEARCH_URL + 'key=' + settings.ADDRESS_SEARCH_KEY + '&type=' + self.addresssearch_type + '&class=' + self.addresssearch_class + '&query=' + self.addresssearch_query + '&out_epsg=' + self.addresssearch_out_epsg + '&shape=' + self.addresssearch_shape + '&limit=' + self.addresssearch_limit)
        return HttpResponse(response, content_type = 'application/json')


class ReverseSearchView(generic.View):
    http_method_names = ['get',]
    
    def dispatch(self, request, *args, **kwargs):
        self.reversesearch_type = 'reverse'
        self.reversesearch_class = 'address'
        self.reversesearch_x = request.GET.get('x', '')
        self.reversesearch_y = request.GET.get('y', '')
        self.reversesearch_in_epsg = '4326'
        self.reversesearch_radius = '200'
        return super(ReverseSearchView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        response = requests.get(settings.ADDRESS_SEARCH_URL + 'key=' + settings.ADDRESS_SEARCH_KEY + '&type=' + self.reversesearch_type + '&class=' + self.reversesearch_class + '&query=' + self.reversesearch_x + ',' + self.reversesearch_y + '&in_epsg=' + self.reversesearch_in_epsg + '&radius=' + self.reversesearch_radius)
        return HttpResponse(response, content_type = 'application/json')


class DataForm(ModelForm):
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(DataForm, self).__init__(*args, **kwargs)
        self.foreign_key_label = (self.instance._meta.foreign_key_label if hasattr(self.instance._meta, 'foreign_key_label') else '')
        self.address_optional = (self.instance._meta.address_optional if hasattr(self.instance._meta, 'address_optional') else None)
        
        for field in self.fields:
            if self.fields[field].label == 'Geometrie':
                message = 'Es muss ein Marker in der Karte gesetzt werden bzw. eine Linie oder Fläche gezeichnet werden, falls es sich um Daten linien- oder flächenhafter Repräsentation handelt!'
            elif self.fields[field].__class__.__name__ == 'ModelChoiceField':
                message = u'Die Referenz zu „{label}“ ist Pflicht!'.format(label = self.foreign_key_label)
            else:
                message = u'Das Attribut „{label}“ ist Pflicht!'.format(label = self.fields[field].label)
                if self.fields[field].__class__.__name__ == 'DecimalField':
                    self.fields[field].localize = True
            self.fields[field].error_messages = { 'required': message, 'invalid_image': 'Sie müssen eine valide Bilddatei hochladen!' }
            
    def clean_geometrie(self):
        data = self.cleaned_data['geometrie']
        error_text = 'Es muss ein Marker in der Karte gesetzt werden bzw. eine Linie oder Fläche gezeichnet werden, falls es sich um Daten linien- oder flächenhafter Repräsentation handelt!'
        if '-' in str(data):
            raise ValidationError(error_text)
        return data
    
    def clean_strasse_name(self):
        data = self.cleaned_data['strasse_name']
        if not data and self.address_optional:
            return data
        elif not data and not self.address_optional:
            raise ValidationError('Das Attribut „Adresse“ ist Pflicht!')
        elif data and self.address_optional:
            error_text = 'Bitte geben Sie eine eindeutige und existierende Adresse oder Straße an. Die Schreibweise muss korrekt sein, vor allem die Groß- und Kleinschreibung!'
        else:
            error_text = 'Bitte geben Sie eine eindeutige und existierende Adresse an. Die Schreibweise muss korrekt sein, vor allem die Groß- und Kleinschreibung!'
        request = requests.get(settings.ADDRESS_SEARCH_URL + 'key=' + settings.ADDRESS_SEARCH_KEY + '&type=search&class=address&query=rostock ' + data)
        json = request.json()
        ergebnisse = json.get('features')
        if not ergebnisse:
            raise ValidationError(error_text)
        for ergebnis in ergebnisse:
            if re.sub('^.*\, ', '', ergebnis.get('properties').get('_title_')) == data:
                return data
        raise ValidationError(error_text)


class IndexView(generic.ListView):
    template_name = 'datenmanagement/index.html'

    def get_queryset(self):
        model_list = []
        app_models = apps.get_app_config('datenmanagement').get_models()
        for model in app_models:
            model_list.append(model)
        return model_list


class StartView(generic.ListView):
    def __init__(self, model = None, template_name = None):
        self.model = model
        self.template_name = template_name
        super(StartView, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(StartView, self).get_context_data(**kwargs)
        context['model_name'] = self.model.__name__
        context['model_name_lower'] = self.model.__name__.lower()
        context['model_verbose_name_plural'] = self.model._meta.verbose_name_plural
        context['geometry_type'] = (self.model._meta.geometry_type if hasattr(self.model._meta, 'geometry_type') else None)
        return context


# @method_decorator(cache_page(60 * 10), name='dispatch')
class DataListView(generic.ListView):
    def __init__(self, model = None, template_name = None, success_url = None):
        self.model = model
        self.template_name = template_name
        super(DataListView, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(DataListView, self).get_context_data(**kwargs)
        context['model_name'] = self.model.__name__
        context['model_name_lower'] = self.model.__name__.lower()
        context['model_verbose_name'] = self.model._meta.verbose_name
        context['model_verbose_name_plural'] = self.model._meta.verbose_name_plural
        context['model_description'] = self.model._meta.description
        context['list_fields'] = self.model._meta.list_fields
        context['list_fields_labels'] = self.model._meta.list_fields_labels
        context['geometry_type'] = (self.model._meta.geometry_type if hasattr(self.model._meta, 'geometry_type') else None)
        return context


# @method_decorator(cache_page(60 * 10), name='dispatch')
class DataMapView(generic.ListView):
    def __init__(self, model = None, template_name = None, success_url = None):
        self.model = model
        self.template_name = template_name
        super(DataMapView, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(DataMapView, self).get_context_data(**kwargs)
        context['model_name'] = self.model.__name__
        context['model_name_lower'] = self.model.__name__.lower()
        context['model_verbose_name'] = self.model._meta.verbose_name
        context['model_verbose_name_plural'] = self.model._meta.verbose_name_plural
        context['model_description'] = self.model._meta.description
        context['list_fields'] = self.model._meta.list_fields
        context['list_fields_labels'] = self.model._meta.list_fields_labels
        context['show_alkis'] = (self.model._meta.show_alkis if hasattr(self.model._meta, 'show_alkis') else None)
        context['map_feature_tooltip_field'] = (self.model._meta.map_feature_tooltip_field if hasattr(self.model._meta, 'map_feature_tooltip_field') else None)
        context['geometry_type'] = (self.model._meta.geometry_type if hasattr(self.model._meta, 'geometry_type') else None)
        return context


class DataAddView(generic.CreateView):
    def __init__(self, model = None, template_name = None, success_url = None):
        self.model = model
        self.template_name = template_name
        self.success_url = success_url
        self.form_class = modelform_factory(self.model, form = DataForm, fields = '__all__', formfield_callback = assign_widgets)
        super(DataAddView, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(DataAddView, self).get_context_data(**kwargs)
        context['LEAFLET_CONFIG'] = settings.LEAFLET_CONFIG
        context['model_name'] = self.model.__name__
        context['model_name_lower'] = self.model.__name__.lower()
        context['model_verbose_name'] = self.model._meta.verbose_name
        context['model_verbose_name_plural'] = self.model._meta.verbose_name_plural
        context['model_description'] = self.model._meta.description
        context['show_alkis'] = (self.model._meta.show_alkis if hasattr(self.model._meta, 'show_alkis') else None)
        context['address'] = (self.model._meta.address if hasattr(self.model._meta, 'address') else None)
        context['address_optional'] = (self.model._meta.address_optional if hasattr(self.model._meta, 'address_optional') else None)
        context['geometry_type'] = (self.model._meta.geometry_type if hasattr(self.model._meta, 'geometry_type') else None)
        context['foreign_key_label'] = (self.model._meta.foreign_key_label if hasattr(self.model._meta, 'foreign_key_label') else None)
        return context

    def get_initial(self):
        return {
            'ansprechpartner': self.request.user.first_name + ' ' + self.request.user.last_name + ' (' + self.request.user.email + ')',
            'bearbeiter': self.request.user.first_name + ' ' + self.request.user.last_name
        }

    def form_valid(self, form):
        form.instance = form.save(commit = False)
        if hasattr(self.model._meta, 'address') and self.model._meta.address:
            if form.instance.strasse_name:
                adresse = form.instance.strasse_name
                form.instance.strasse_name = re.sub(' [0-9]+([a-z]+)?$', '', adresse)
                m = re.search('[0-9]+[a-z]+$', adresse)
                if m:
                    form.instance.hausnummer = re.sub('[a-z]+', '', m.group(0))
                    form.instance.hausnummer_zusatz = re.sub('\d+', '', m.group(0))
                m = re.search('[0-9]+$', adresse)
                if m:
                    form.instance.hausnummer = m.group(0)
        form.instance = form.save()
        assign_perm('datenmanagement.change_' + self.model.__name__.lower(), self.request.user, form.instance)
        assign_perm('datenmanagement.delete_' + self.model.__name__.lower(), self.request.user, form.instance)
        for group in Group.objects.all():
            if group.permissions.filter(codename = 'change_' + self.model.__name__.lower()):
                assign_perm('datenmanagement.change_' + self.model.__name__.lower(), group, form.instance)
            if group.permissions.filter(codename = 'delete_' + self.model.__name__.lower()):
                assign_perm('datenmanagement.delete_' + self.model.__name__.lower(), group, form.instance)
        return super(DataAddView, self).form_valid(form)


class DataChangeView(generic.UpdateView):
    def __init__(self, model = None, template_name = None, success_url = None):
        self.model = model
        self.template_name = template_name
        self.success_url = success_url
        self.form_class = modelform_factory(self.model, form = DataForm, fields = '__all__', formfield_callback = assign_widgets)
        super(DataChangeView, self).__init__()

    def get_context_data(self, **kwargs):
        context = super(DataChangeView, self).get_context_data(**kwargs)
        context['model_name'] = self.model.__name__
        context['model_name_lower'] = self.model.__name__.lower()
        context['model_verbose_name'] = self.model._meta.verbose_name
        context['model_verbose_name_plural'] = self.model._meta.verbose_name_plural
        context['model_description'] = self.model._meta.description
        context['show_alkis'] = (self.model._meta.show_alkis if hasattr(self.model._meta, 'show_alkis') else None)
        context['address'] = (self.model._meta.address if hasattr(self.model._meta, 'address') else None)
        context['address_optional'] = (self.model._meta.address_optional if hasattr(self.model._meta, 'address_optional') else None)
        context['geometry_type'] = (self.model._meta.geometry_type if hasattr(self.model._meta, 'geometry_type') else None)
        context['foreign_key_label'] = (self.model._meta.foreign_key_label if hasattr(self.model._meta, 'foreign_key_label') else None)
        return context

    def get_initial(self):
        if hasattr(self.model._meta, 'address') and self.model._meta.address:
            if hasattr(self.object, 'strasse_name') and self.object.strasse_name:
                adresse = self.object.strasse_name.strip()
                if hasattr(self.object, 'hausnummer') and self.object.hausnummer:
                    adresse = (adresse + ' ' + self.object.hausnummer.strip())
                    if hasattr(self.object, 'hausnummer_zusatz') and self.object.hausnummer_zusatz:
                        adresse = adresse + self.object.hausnummer_zusatz.strip()
                return {
                    'strasse_name': adresse
                }
            else:
                return {
                }
        else:
            return {
            }

    def form_valid(self, form):
        form.instance = form.save(commit = False)
        if hasattr(self.model._meta, 'address') and self.model._meta.address:
            if form.instance.strasse_name:
                adresse = form.instance.strasse_name
                form.instance.strasse_name = re.sub(' [0-9]+([a-z]+)?$', '', adresse)
                m = re.search('[0-9]+[a-z]+$', adresse)
                if m:
                    form.instance.hausnummer = re.sub('[a-z]+', '', m.group(0))
                    form.instance.hausnummer_zusatz = re.sub('\d+', '', m.group(0))
                m = re.search('[0-9]+$', adresse)
                if m:
                    form.instance.hausnummer = m.group(0)
        form.instance = form.save()
        return super(DataChangeView, self).form_valid(form)
        
    def get_object(self, *args, **kwargs):
        obj = super(DataChangeView, self).get_object(*args, **kwargs)
        userobjperm = ObjectPermissionChecker(self.request.user).has_perm('change_' + self.model.__name__.lower(), obj)
        if not userobjperm:
            raise PermissionDenied()
        return obj


class DataDeleteView(generic.DeleteView):
    def get_object(self, *args, **kwargs):
        obj = super(DataDeleteView, self).get_object(*args, **kwargs)
        userobjperm = ObjectPermissionChecker(self.request.user).has_perm('delete_' + self.model.__name__.lower(), obj)
        if not userobjperm:
            raise PermissionDenied()
        return obj
