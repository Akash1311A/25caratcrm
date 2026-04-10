from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import Customer, ProductType, Purchase, FollowUp, SALE_PRODUCT_NAMES, AMOUNT_RANGE_CHOICES, amount_to_range


def _limit_date_to_today(field):
    field.widget.attrs["max"] = timezone.localdate().isoformat()


def _clean_non_future_date(value, label):
    selected = value or timezone.localdate()
    if selected > timezone.localdate():
        raise forms.ValidationError(f"{label} cannot be in the future.")
    return selected


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True, "class": "form-control"}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean_username(self):
        return (self.cleaned_data.get("username") or "").strip().lower()


class CustomerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        parts = [obj.name, obj.phone]
        if obj.city:
            parts.append(obj.city)
        return " • ".join(parts)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name",
            "city",
            "phone",
            "phone2",
        ]
        labels = {
            "phone": "Mobile",
            "phone2": "Phone 2",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Customer name"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+91 98765 43210"}),
            "phone2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional"}),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        existing = Customer.objects.filter(phone=phone).exclude(pk=self.instance.pk if self.instance else None).first()
        if existing:
            raise forms.ValidationError(
                f"This mobile number already belongs to {existing.name} ({existing.phone})."
            )
        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)
        customer.whatsapp = customer.phone
        if commit:
            customer.save()
            self.save_m2m()
        return customer


class PurchaseForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=ProductType.objects.filter(name__in=SALE_PRODUCT_NAMES),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Products",
    )

    class Meta:
        model = Purchase
        fields = ["products", "amount", "amount_range", "date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Total amount", "min": "5000", "step": "1"}),
            "amount_range": forms.HiddenInput(),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["products"].queryset = ProductType.objects.filter(name__in=SALE_PRODUCT_NAMES).order_by("order", "name")
        self.fields["amount_range"].choices = AMOUNT_RANGE_CHOICES
        self.fields["amount_range"].required = False
        self.fields["date"].required = False
        self.fields["date"].initial = timezone.localdate()
        _limit_date_to_today(self.fields["date"])

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount in (None, ""):
            raise forms.ValidationError("Please enter an amount.")
        if amount < 5000:
            raise forms.ValidationError("Amount must be at least 5000.")
        return amount

    def clean_amount_range(self):
        amount = self.cleaned_data.get("amount")
        return amount_to_range(amount)

    def clean_date(self):
        return _clean_non_future_date(self.cleaned_data.get("date"), "Purchase date")


class SellForm(forms.Form):
    customer = CustomerChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="Select existing customer",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Choose existing customer",
    )
    new_customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "New customer name"}),
        label="New customer name",
    )
    new_customer_city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
        label="City",
    )
    new_customer_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "New customer phone"}),
        label="New customer phone",
    )
    new_customer_phone2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional"}),
        label="Phone 2",
    )
    products = forms.ModelMultipleChoiceField(
        queryset=ProductType.objects.filter(name__in=SALE_PRODUCT_NAMES),
        widget=forms.CheckboxSelectMultiple,
        label="Products",
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=5000,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Total amount", "min": "5000", "step": "1"}),
        label="Amount",
    )
    amount_range = forms.ChoiceField(
        choices=AMOUNT_RANGE_CHOICES,
        widget=forms.HiddenInput(),
        label="Amount range",
        required=False,
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Purchase date",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["products"].queryset = ProductType.objects.filter(name__in=SALE_PRODUCT_NAMES).order_by("order", "name")
        self.fields["date"].initial = timezone.localdate()
        _limit_date_to_today(self.fields["date"])
        if self.user and not self.user.is_superuser:
            self.fields["customer"].queryset = Customer.objects.filter(assigned_to=self.user).order_by("name")
        self.fields["amount_range"].required = False

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get("customer")
        name = cleaned_data.get("new_customer_name")
        phone = cleaned_data.get("new_customer_phone")
        products = cleaned_data.get("products")

        if not customer and not name:
            raise forms.ValidationError("Select an existing customer or enter new customer details.")
        if name and not phone:
            raise forms.ValidationError("Please provide a phone number for the new customer.")
        if name and phone:
            existing = Customer.objects.filter(phone=phone).first()
            if existing and (not customer or existing.pk != customer.pk):
                raise forms.ValidationError(
                    f"This phone number already belongs to {existing.name} ({existing.phone}). Please select that customer instead."
                )
        if not products:
            raise forms.ValidationError("Please select at least one product.")
        return cleaned_data

    def clean_date(self):
        return _clean_non_future_date(self.cleaned_data.get("date"), "Sale date")

    def clean_amount_range(self):
        amount = self.cleaned_data.get("amount")
        return amount_to_range(amount)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount in (None, ""):
            raise forms.ValidationError("Please enter an amount.")
        if amount < 5000:
            raise forms.ValidationError("Amount must be at least 5000.")
        return amount

    def create_customer(self):
        name = self.cleaned_data.get("new_customer_name")
        city = self.cleaned_data.get("new_customer_city", "")
        phone = self.cleaned_data.get("new_customer_phone")
        if not name:
            return None
        return Customer.objects.create(
            name=name,
            city=city,
            phone=phone,
            whatsapp=phone,
            phone2=self.cleaned_data.get("new_customer_phone2", ""),
        )


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ["next_followup_date", "notes", "status"]
        widgets = {
            "next_followup_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Note for follow-up"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(label="Current password", strip=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password1 = forms.CharField(label="New password", strip=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password2 = forms.CharField(label="Confirm new password", strip=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
        }
        labels = {
            "first_name": "Name",
        }

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()
