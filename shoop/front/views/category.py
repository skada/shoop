# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django import forms
from django.views.generic import DetailView

from shoop.core.models import Category, Manufacturer, Product
from shoop.front.utils.product_sorting import PRODUCT_SORT_CHOICES, sort_products
from shoop.front.utils.views import cache_product_things


class ProductListForm(forms.Form):
    sort = forms.CharField(required=False, widget=forms.Select(choices=PRODUCT_SORT_CHOICES))
    manufacturers = forms.ModelMultipleChoiceField(queryset=Manufacturer.objects.all(), required=False)


class CategoryView(DetailView):
    template_name = "shoop/front/product/category.jinja"
    model = Category
    template_object_name = "category"

    def get_queryset(self):
        return self.model.objects.all_visible(
            customer=self.request.customer,
            shop=self.request.shop,
        )

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        category = self.object
        context["form"] = form = ProductListForm(data=self.request.GET)
        form.full_clean()

        filters = {
            "shop_products__shop": self.request.shop,
            "shop_products__categories": category,
            "variation_parent": None
        }
        manufacturers = form.cleaned_data.get("manufacturers")
        if manufacturers:
            filters["manufacturer__in"] = manufacturers

        products = Product.objects.list_visible(
            customer=self.request.customer,
            shop=self.request.shop
        ).filter(**filters).distinct()

        products = cache_product_things(self.request, products)
        products = sort_products(self.request, products, self.request.GET.get("sort"))
        context["products"] = products
        return context
