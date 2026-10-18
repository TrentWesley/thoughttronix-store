"""Review endpoints — thin HTMX views that return partials, like the cart's.

Every review endpoint goes through ``ReviewEndpointMixin``, the error
machinery later phases reuse:

- Signed out: an HTMX request gets ``HX-Redirect`` to sign-in, so a login
  page is never swapped into the Reviews section. A plain request gets the
  normal login redirect. Either way, sign-in returns to the product page.
- Refusals: a handler raises ``PermissionDenied`` (403) or ``Http404``
  (404). The mixin answers with the inline alert partial, the real status
  code, and ``HX-Retarget``/``HX-Reswap`` aimed at the affected element,
  plus the refreshed summary out of band when the product is known. HTMX 2
  only swaps those 4xx responses because the product page carries an
  ``htmx-config`` meta tag allowing it.
"""

from http import HTTPStatus

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from products.models import Product

from .forms import ReviewForm
from .models import Eligibility, Review

REFUSALS = {
    Eligibility.NOT_PURCHASED: (
        "Only customers with a delivered order can review this product."
    ),
    Eligibility.ALREADY_REVIEWED: "You've already reviewed this product.",
}


def form_slot_context(user, product, *, form=None) -> dict:
    """Context for ``_form_slot.html``: which of its four states ``user`` sees.

    Signed out, not eligible, the review form, or the user's own review
    (pinned in the slot, so the list must exclude it).
    """
    eligibility = Review.objects.eligibility(user, product)
    own_review = None
    if eligibility == Eligibility.ALREADY_REVIEWED:
        own_review = (
            Review.objects.select_related("user")
            .filter(user=user, product=product)
            .first()
        )
    elif eligibility == Eligibility.ELIGIBLE:
        form = form or ReviewForm()
    return {
        "product": product,
        "eligibility": eligibility,
        "own_review": own_review,
        "form": form,
    }


class ReviewEndpointMixin:
    """Sign-in redirects and inline 403/404 alerts for review endpoints.

    Handlers set ``self.product`` once it's known, so an alert can carry
    the refreshed summary.
    """

    alert_target = "#review-form-slot"
    alert_swap = "innerHTML"
    not_found_message = "This review is no longer available."
    product = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.signed_out_response()
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied as refusal:
            return self.alert(str(refusal), status=HTTPStatus.FORBIDDEN)
        except Http404:
            return self.alert(self.not_found_message, status=HTTPStatus.NOT_FOUND)

    def product_url(self) -> str:
        """The product page that sign-in should return to."""
        raise NotImplementedError

    def get_alert_target(self) -> str:
        return self.alert_target

    def signed_out_response(self) -> HttpResponse:
        login = redirect_to_login(self.product_url())
        if self.request.headers.get("HX-Request") != "true":
            return login
        response = HttpResponse(status=HTTPStatus.NO_CONTENT)
        response["HX-Redirect"] = login.url
        return response

    def alert(self, message: str, *, status: int) -> HttpResponse:
        context = {"message": message or "That isn't something you can do here."}
        if self.product is not None:
            context["review_summary"] = self.product.reviews.summary()
        response = render(
            self.request, "reviews/partials/_alert.html", context, status=status
        )
        response["HX-Retarget"] = self.get_alert_target()
        response["HX-Reswap"] = self.alert_swap
        return response


class CreateReviewView(ReviewEndpointMixin, View):
    """HTMX POST: write a review, which then appears pinned in the form slot.

    Eligibility is re-checked here, so an ineligible create is a 403 no
    matter what the page showed. Invalid input re-renders the form. If a
    duplicate slips past the check (two tabs at once), the unique
    constraint catches it and the customer sees the review they already
    have.
    """

    not_found_message = "This product is no longer available."

    def product_url(self):
        return get_object_or_404(Product, pk=self.kwargs["pk"]).get_absolute_url()

    def post(self, request, pk):
        self.product = get_object_or_404(Product, pk=pk)
        eligibility = Review.objects.eligibility(request.user, self.product)
        if eligibility != Eligibility.ELIGIBLE:
            raise PermissionDenied(REFUSALS[eligibility])

        form = ReviewForm(
            request.POST, instance=Review(user=request.user, product=self.product)
        )
        if not form.is_valid():
            return render(
                request,
                "reviews/partials/_review_form.html",
                {"product": self.product, "form": form},
            )

        duplicate = False
        try:
            # Nested, so a constraint violation leaves the request usable.
            with transaction.atomic():
                review = form.save()
        except IntegrityError:
            review = Review.objects.get(user=request.user, product=self.product)
            duplicate = True
        return render(
            request,
            "reviews/partials/_form_slot.html",
            {
                "product": self.product,
                "eligibility": Eligibility.ALREADY_REVIEWED,
                "own_review": review,
                "duplicate": duplicate,
                "review_summary": self.product.reviews.summary(),
                "oob_summary": True,
            },
        )
