from datetime import date, timedelta
from django.contrib import messages
from django.core import signing
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView, PasswordChangeView
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import Http404
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import ChangePasswordForm, CustomerForm, FollowUpForm, LoginForm, ProfileForm, PurchaseForm
from .models import AMOUNT_RANGE_CHOICES, Customer, FollowUp, ProductType, Purchase, amount_to_range


class LoginView(AuthLoginView):
    template_name = "crm/login.html"
    authentication_form = LoginForm


class LogoutView(AuthLogoutView):
    pass


class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = "crm/change_password.html"
    form_class = ChangePasswordForm
    success_url = reverse_lazy("crm:dashboard")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been updated.")
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "crm/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customers = self.get_customer_queryset()
        purchases = self.get_purchase_queryset()
        followups = self.get_followup_queryset()
        total_sales = purchases.aggregate(total=Sum("amount"))["total"] or 0
        pending_followups = followups.filter(status="Pending").count()
        today = date.today()
        todays_followups = followups.filter(status="Pending", next_followup_date=today)
        overdue_followups = followups.filter(status="Pending", next_followup_date__lt=today)
        completed_followups_30d = followups.filter(
            status="Completed",
            next_followup_date__gte=today - timedelta(days=30),
            next_followup_date__lte=today,
        ).count()
        recent_customers = customers.order_by("-created_at")[:5]
        top_customers = customers.annotate(total_amount=Sum("purchases__amount")).order_by("-total_amount")[:5]
        staff_followup_stats = followups.values("assigned_to__username").annotate(total=Count("id")).order_by("-total")
        context.update({
            "total_customers": customers.count(),
            "total_sales": total_sales,
            "pending_followups": pending_followups,
            "todays_followups": todays_followups,
            "overdue_followups": overdue_followups,
            "completed_followups_30d": completed_followups_30d,
            "recent_customers": recent_customers,
            "top_customers": top_customers,
            "product_types": ProductType.objects.all(),
            "staff_followup_stats": staff_followup_stats,
            "my_customers_count": Customer.objects.filter(assigned_to=self.request.user).count() if not self.request.user.is_superuser else customers.count(),
            "my_followups_count": FollowUp.objects.filter(assigned_to=self.request.user).count() if not self.request.user.is_superuser else followups.count(),
        })
        return context

    def get_customer_queryset(self):
        queryset = Customer.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)

    def get_purchase_queryset(self):
        queryset = Purchase.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)

    def get_followup_queryset(self):
        queryset = FollowUp.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)


class SearchFilterMixin:
    def filter_queryset(self, queryset):
        q = self.request.GET.get("q", "").strip()
        city = self.request.GET.get("city")
        amount_range = self.request.GET.get("amount_range")
        followup = self.request.GET.get("followup")
        sort = self.request.GET.get("sort", "-total_spent")

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(phone__icontains=q) | Q(city__icontains=q) | Q(whatsapp__icontains=q)
            )
        if city:
            queryset = queryset.filter(city__icontains=city)
        if amount_range:
            queryset = queryset.filter(purchases__amount_range=amount_range).distinct()
        if followup == "pending":
            queryset = queryset.filter(followups__status="Pending").distinct()
        elif followup == "today":
            queryset = queryset.filter(
                followups__status="Pending",
                followups__next_followup_date=date.today(),
            ).distinct()
        elif followup == "overdue":
            queryset = queryset.filter(
                followups__status="Pending",
                followups__next_followup_date__lt=date.today(),
            ).distinct()
        elif followup == "completed":
            queryset = queryset.filter(followups__status="Completed").distinct()
        queryset = queryset.annotate(total_spent=Sum("purchases__amount"))
        if sort == "spent_asc":
            queryset = queryset.order_by("total_spent", "name")
        elif sort == "name":
            queryset = queryset.order_by("name")
        else:
            queryset = queryset.order_by("-total_spent", "name")
        return queryset.distinct()


class CustomerListView(LoginRequiredMixin, SearchFilterMixin, ListView):
    template_name = "crm/customer_list.html"
    model = Customer
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related("assigned_to").prefetch_related("purchases__products", "followups")
        if not self.request.user.is_superuser:
            queryset = queryset.filter(assigned_to=self.request.user)
        queryset = queryset.annotate(
            total_spent=Sum("purchases__amount"),
            pending_followups_count=Count("followups", filter=Q(followups__status="Pending")),
        )
        return self.filter_queryset(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product_types"] = ProductType.objects.all()
        context["amount_range_choices"] = AMOUNT_RANGE_CHOICES
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    template_name = "crm/customer_form.html"
    model = Customer
    form_class = CustomerForm
    success_url = reverse_lazy("crm:customer_list")

    def form_valid(self, form):
        form.instance.assigned_to = self.request.user
        messages.success(self.request, "Customer added successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        error_text = ", ".join(
            str(error)
            for errors in form.errors.values()
            for error in errors
        ) or "Please check the customer details."
        messages.error(self.request, error_text)
        return redirect("crm:dashboard")


class CustomerDetailView(LoginRequiredMixin, DetailView):
    template_name = "crm/customer_detail.html"
    model = Customer

    def get_queryset(self):
        queryset = super().get_queryset().select_related("assigned_to").prefetch_related("purchases__products", "followups")
        if not self.request.user.is_superuser:
            queryset = queryset.filter(assigned_to=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["purchase_form"] = PurchaseForm()
        context["followup_form"] = FollowUpForm()
        return context


def create_auto_followups(customer, purchase_date, assigned_to=None, purchase=None, replace_existing=True):
    if replace_existing:
        FollowUp.objects.filter(customer=customer).delete()
    followup_days = [3, 7, 15]
    for days in followup_days:
        followup_date = purchase_date + timedelta(days=days)
        FollowUp.objects.get_or_create(
            customer=customer,
            next_followup_date=followup_date,
            defaults={
                "notes": "Auto-generated follow-up",
                "status": "Pending",
                "assigned_to": assigned_to,
            },
        )


class SellCreateView(LoginRequiredMixin, FormView):
    template_name = "crm/sell_form.html"
    form_class = None

    def get_form_class(self):
        from .forms import SellForm
        return SellForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        customer_id = self.request.GET.get("customer")
        if customer_id:
            initial["customer"] = customer_id
        return initial

    def form_valid(self, form):
        customer = form.cleaned_data.get("customer")
        if not customer:
            customer = form.create_customer()
        if not customer.assigned_to_id:
            customer.assigned_to = self.request.user
            customer.save(update_fields=["assigned_to"])
        amount = form.cleaned_data["amount"]
        amount_range = amount_to_range(amount)

        purchase = Purchase.objects.create(
            customer=customer,
            amount_range=amount_range,
            amount=amount,
            date=form.cleaned_data["date"],
            assigned_to=self.request.user,
        )
        purchase.products.set(form.cleaned_data["products"])
        create_auto_followups(customer, purchase.date, assigned_to=self.request.user, purchase=purchase)
        messages.success(self.request, "Sale recorded, follow-ups scheduled, and thank-you card created.")
        return redirect("crm:sale_thank_you", pk=purchase.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the highlighted sale form errors and try again.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "customer" in form.fields and not self.request.user.is_superuser:
            form.fields["customer"].queryset = Customer.objects.filter(assigned_to=self.request.user).order_by("name")
        return form


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "crm/customer_form.html"
    model = Customer
    form_class = CustomerForm
    success_url = reverse_lazy("crm:customer_list")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Customer details updated.")
        return super().form_valid(form)


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "crm/confirm_delete.html"
    model = Customer
    success_url = reverse_lazy("crm:customer_list")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Customer deleted.")
        return super().delete(request, *args, **kwargs)


class PurchaseCreateView(LoginRequiredMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "crm/purchase_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer"] = get_object_or_404(Customer, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs["pk"])
        if not self.request.user.is_superuser and customer.assigned_to_id != self.request.user.id:
            return redirect("crm:customer_list")
        form.instance.customer = customer
        form.instance.assigned_to = self.request.user
        form.instance.amount_range = amount_to_range(form.cleaned_data["amount"])
        messages.success(self.request, "Purchase saved.")
        response = super().form_valid(form)
        self.object.products.set(form.cleaned_data["products"])
        create_auto_followups(customer, self.object.date, assigned_to=self.request.user, purchase=self.object)
        return response

    def get_success_url(self):
        return reverse_lazy("crm:customer_detail", kwargs={"pk": self.kwargs["pk"]})


class FollowUpCreateView(LoginRequiredMixin, CreateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = "crm/followup_form.html"

    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs["pk"])
        if not self.request.user.is_superuser and customer.assigned_to_id != self.request.user.id:
            return redirect("crm:customer_list")
        form.instance.customer = customer
        form.instance.assigned_to = self.request.user
        messages.success(self.request, "Follow-up added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("crm:customer_detail", kwargs={"pk": self.kwargs["pk"]})


class PurchaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Purchase
    template_name = "crm/confirm_delete.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)

    def get_success_url(self):
        return reverse_lazy("crm:customer_detail", kwargs={"pk": self.object.customer.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Purchase removed.")
        return super().delete(request, *args, **kwargs)


class FollowUpCompleteView(LoginRequiredMixin, UpdateView):
    model = FollowUp
    fields = []

    def post(self, request, *args, **kwargs):
        followup = self.get_object()
        followup.status = "Completed"
        followup.completed_at = timezone.localdate()
        followup.save()
        messages.success(request, "Follow-up marked completed.")
        return redirect("crm:customer_detail", pk=followup.customer.pk)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)


class FollowUpDeleteView(LoginRequiredMixin, DeleteView):
    model = FollowUp
    template_name = "crm/confirm_delete.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)

    def get_success_url(self):
        return reverse_lazy("crm:customer_detail", kwargs={"pk": self.object.customer.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Follow-up removed.")
        return super().delete(request, *args, **kwargs)


class SaleThankYouView(LoginRequiredMixin, DetailView):
    model = Purchase
    template_name = "crm/sale_thank_you.html"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("customer", "assigned_to").prefetch_related("products")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(assigned_to=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products_display"] = self.object.products.all()
        share_token = signing.dumps({"pk": self.object.pk, "customer_pk": self.object.customer_id}, salt="sale-thank-you")
        context["thank_you_share_url"] = self.request.build_absolute_uri(
            reverse("crm:sale_thank_you_public", kwargs={"pk": self.object.pk, "token": share_token})
        )
        context["whatsapp_share_text"] = (
            f"Hi {self.object.customer.name}, here is your 25 Carat thank you card: "
            f"{context['thank_you_share_url']}"
        )
        return context


class PublicSaleThankYouView(DetailView):
    model = Purchase
    template_name = "crm/sale_thank_you.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            payload = signing.loads(kwargs["token"], salt="sale-thank-you", max_age=60 * 60 * 24 * 90)
        except signing.BadSignature as exc:
            raise Http404("Invalid thank-you card link.") from exc
        if payload.get("pk") != kwargs["pk"]:
            raise Http404("Invalid thank-you card link.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().select_related("customer", "assigned_to").prefetch_related("products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products_display"] = self.object.products.all()
        context["public_view"] = True
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "crm/profile.html"

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.save(update_fields=["first_name"])
            messages.success(request, "Your name has been updated.")
            return redirect("crm:profile")
        context = self.get_context_data(profile_form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        assigned_customers = Customer.objects.filter(assigned_to=user)
        assigned_followups = FollowUp.objects.filter(assigned_to=user)
        context["profile_form"] = kwargs.get("profile_form") or ProfileForm(instance=user)
        context.update({
            "profile_user": user,
            "assigned_customers_count": assigned_customers.count() if not user.is_superuser else Customer.objects.count(),
            "assigned_followups_count": assigned_followups.count() if not user.is_superuser else FollowUp.objects.count(),
            "completed_followups_count": assigned_followups.filter(status="Completed").count() if not user.is_superuser else FollowUp.objects.filter(status="Completed").count(),
            "pending_followups_count": assigned_followups.filter(status="Pending").count() if not user.is_superuser else FollowUp.objects.filter(status="Pending").count(),
            "recent_customers": assigned_customers.order_by("-created_at")[:5],
        })
        return context
