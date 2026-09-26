"""Back-office coupon management — staff-only, thin per the convention.

Create, edit the expiry, and retire. There is deliberately no delete:
retired coupons stay so past orders keep pointing at the deal they got.
The ``section`` context entry drives the active tab in the staff shell.
"""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import StaffRequiredMixin

from .forms import CouponCreateForm, CouponExpiryForm
from .models import Coupon


class ManageCouponListView(StaffRequiredMixin, ListView):
    """Every coupon, newest first, with how many orders used it."""

    template_name = "coupons/manage_coupons.html"
    context_object_name = "coupons"
    extra_context = {"section": "coupons"}

    def get_queryset(self):
        return Coupon.objects.with_times_used().prefetch_related("products")


class ManageCouponCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Coupon
    form_class = CouponCreateForm
    template_name = "coupons/manage_coupon_form.html"
    success_url = reverse_lazy("coupons:manage_coupons")
    success_message = "%(code)s created."
    extra_context = {"section": "coupons"}


class ManageCouponUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    """Only the expiry is editable; retired coupons can't be edited at all."""

    queryset = Coupon.objects.live()
    form_class = CouponExpiryForm
    template_name = "coupons/manage_coupon_form.html"
    success_url = reverse_lazy("coupons:manage_coupons")
    success_message = "%(code)s saved."
    extra_context = {"section": "coupons"}

    def get_success_message(self, cleaned_data):
        return self.success_message % {"code": self.object.code}


class ManageCouponRetireView(StaffRequiredMixin, DetailView):
    """GET asks for confirmation; POST retires the coupon for good."""

    queryset = Coupon.objects.live()
    context_object_name = "coupon"
    template_name = "coupons/manage_coupon_confirm_retire.html"
    extra_context = {"section": "coupons"}

    def post(self, request, *args, **kwargs):
        coupon = self.get_object()
        coupon.retire()
        messages.success(request, f"{coupon.code} retired.")
        return redirect("coupons:manage_coupons")
