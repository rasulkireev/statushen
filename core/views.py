from datetime import timedelta
from urllib.parse import urlencode

from core.views_utils import StatusSummaryMixin
import stripe

from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, UpdateView, ListView, DetailView, CreateView, FormView
from django.shortcuts import get_object_or_404

from djstripe import models as djstripe_models

from core.forms import ProfileUpdateForm, ServiceForm
from core.models import Profile, BlogPost, Project
from core.utils import check_if_profile_has_pro_subscription

from statushen.utils import get_statushen_logger

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = get_statushen_logger(__name__)

class HomeView(StatusSummaryMixin, TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            profile = self.request.user.profile
            user_projects = Project.objects.filter(profile=profile).prefetch_related('services', 'services__statuses')

            for project in user_projects:
                self.add_status_summary_to_services(project.services.all(), number_of_sticks=100)

            context["user_projects"] = user_projects

        payment_status = self.request.GET.get("payment")
        if payment_status == "success":
            messages.success(self.request, "Thanks for subscribing, I hope you enjoy the app!")
            context["show_confetti"] = True
        elif payment_status == "failed":
            messages.error(self.request, "Something went wrong with the payment.")


        return context


class UserSettingsView(StatusSummaryMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    login_url = "account_login"
    model = Profile
    form_class = ProfileUpdateForm
    success_message = "User Profile Updated"
    success_url = reverse_lazy("settings")
    template_name = "pages/user-settings.html"

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.profile

        email_address = EmailAddress.objects.get_for_user(user, user.email)
        context["email_verified"] = email_address.verified
        context["resend_confirmation_url"] = reverse("resend_confirmation")
        context["has_subscription"] = profile.subscription is not None

        user_projects = profile.projects.all().prefetch_related('services', 'services__statuses')
        for project in user_projects:
            self.add_status_summary_to_services(project.services.all())

        context["user_projects"] = user_projects

        return context


@login_required
def resend_confirmation_email(request):
    user = request.user
    send_email_confirmation(request, user, EmailAddress.objects.get_for_user(user, user.email))

    return redirect("settings")


class PricingView(TemplateView):
    template_name = "pages/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                context["has_pro_subscription"] = check_if_profile_has_pro_subscription(profile.id)
            except Profile.DoesNotExist:
                context["has_pro_subscription"] = False
        else:
            context["has_pro_subscription"] = False

        return context


def create_checkout_session(request, pk, plan):
    user = request.user

    product = djstripe_models.Product.objects.get(name=plan)
    price = product.prices.filter(active=True).first()
    customer, _ = djstripe_models.Customer.get_or_create(subscriber=user)

    profile = user.profile
    profile.customer = customer
    profile.save(update_fields=["customer"])

    base_success_url = request.build_absolute_uri(reverse("home"))
    base_cancel_url = request.build_absolute_uri(reverse("home"))

    success_params = {"payment": "success"}
    success_url = f"{base_success_url}?{urlencode(success_params)}"

    cancel_params = {"payment": "failed"}
    cancel_url = f"{base_cancel_url}?{urlencode(cancel_params)}"

    checkout_session = stripe.checkout.Session.create(
        customer=customer.id,
        payment_method_types=["card"],
        allow_promotion_codes=True,
        automatic_tax={"enabled": True},
        line_items=[
            {
                "price": price.id,
                "quantity": 1,
            }
        ],
        mode="subscription" if plan != "one-time" else "payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_update={
            "address": "auto",
        },
        metadata={"user_id": user.id, "pk": pk, "price_id": price.id},
    )

    return redirect(checkout_session.url, code=303)


@login_required
def create_customer_portal_session(request):
    user = request.user
    customer = djstripe_models.Customer.objects.get(subscriber=user)

    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=request.build_absolute_uri(reverse("home")),
    )

    return redirect(session.url, code=303)


class BlogView(ListView):
    model = BlogPost
    template_name = "blog/blog_posts.html"
    context_object_name = "blog_posts"


class BlogPostView(DetailView):
    model = BlogPost
    template_name = "blog/blog_post.html"
    context_object_name = "blog_post"


class CreateProjectView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/create_project.html'
    fields = ['name', 'slug', 'icon', 'public']
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.profile = self.request.user.profile
        response = super().form_valid(form)
        messages.success(self.request, f"Project '{self.object.name}' has been successfully created!")
        return response


class ProjectStatusPageView(StatusSummaryMixin, DetailView):
    model = Project
    template_name = 'projects/project_status.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        services = self.object.services.all()

        # Add status summary to services
        self.add_status_summary_to_services(services)

        # Get overall project status
        context['project_overall_status'] = self.get_overall_project_status(services)

        context['services'] = services
        return context


class ProjectSettingsView(StatusSummaryMixin, LoginRequiredMixin, FormView):
    template_name = 'projects/project_settings.html'
    form_class = ServiceForm

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=self.kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        services = self.project.services.all()

        self.add_status_summary_to_services(services)
        context['services'] = services
        return context

    def form_valid(self, form):
        service = form.save(commit=False)
        service.project = self.project
        service.save()
        messages.success(self.request, f"Service '{service.name}' has been successfully created!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project-settings', kwargs={'slug': self.project.slug})
