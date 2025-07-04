from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.db.models import Sum

from .models import GrantApplication, GrantReview
from .forms import GrantApplicationForm, GrantReviewForm, GrantDecisionForm


class GrantApplicationMixin:
    """Mixin for common grant application functionality"""
    
    def get_success_url(self):
        return reverse("grants:application_detail")
    
    def add_success_message(self, action="submitted"):
        messages.success(
            self.request, 
            f"Your grant application has been {action} successfully!"
        )
    
    def redirect_to_current_page(self):
        return HttpResponseRedirect(self.request.path)


class GrantReviewMixin:
    """Mixin for common grant review functionality"""
    
    def get_optimized_queryset(self):
        return GrantApplication.objects.select_related('user').prefetch_related('reviews')
    
    def get_budget_context(self):
        total_budget = getattr(settings, 'GRANT_TOTAL_BUDGET', 0)
        approved_total = GrantApplication.objects.filter(
            status='approved'
        ).aggregate(total=Sum('approved_amount'))['total'] or 0
        
        return {
            'total_budget': total_budget,
            'approved_total': approved_total,
            'remaining_budget': total_budget - approved_total
        }


class GrantApplicationCreateView(LoginRequiredMixin, CreateView, GrantApplicationMixin):
    model = GrantApplication
    form_class = GrantApplicationForm
    template_name = "grants/application_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.add_success_message("submitted")
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if not settings.GRANT_APPLICATIONS_OPEN:
            messages.error(request, "Grant applications are currently closed.")
            return redirect("wafer_user_profile", username=request.user.username)

        if hasattr(request.user, "grant_application"):
            messages.warning(request, "You have already submitted a grant application.")
            return redirect("grants:application_detail")
        
        return super().get(request, *args, **kwargs)


class GrantApplicationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView, GrantApplicationMixin):
    model = GrantApplication
    form_class = GrantApplicationForm
    template_name = "grants/application_form.html"

    def test_func(self):
        return hasattr(self.request.user, 'grant_application')

    def get_object(self, queryset=None):
        return self.request.user.grant_application

    def form_valid(self, form):
        self.add_success_message("updated")
        return super().form_valid(form)


class GrantApplicationDetailView(LoginRequiredMixin, DetailView):
    model = GrantApplication
    template_name = "grants/application_detail.html"
    context_object_name = "application"

    def get_object(self):
        return get_object_or_404(GrantApplication, user=self.request.user)


class GrantApplicationListView(PermissionRequiredMixin, ListView, GrantReviewMixin):
    model = GrantApplication
    template_name = "grants/application_list.html"
    context_object_name = "applications"
    paginate_by = 20
    permission_required = 'grants.view_grantreview'

    def get_queryset(self):
        return self.get_optimized_queryset().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_budget_context())
        return context


class GrantApplicationReviewView(PermissionRequiredMixin, DetailView, GrantApplicationMixin):
    model = GrantApplication
    template_name = "grants/review_detail.html"
    context_object_name = "application"
    permission_required = 'grants.add_grantreview'

    def get_user_review(self):
        """Get user's existing review if any"""
        try:
            return self.object.reviews.get(reviewer=self.request.user)
        except GrantReview.DoesNotExist:
            return None

    def get_review_context(self):
        """Build review-specific context"""
        reviews = self.object.reviews.all().select_related('reviewer')
        user_review = self.get_user_review()
        
        return {
            'can_decide': self.request.user.is_superuser,
            'reviews': reviews,
            'user_review': user_review,
            'is_readonly': self.object.status in ['approved', 'rejected'],
            'average_score': self.calculate_average_score(reviews)
        }

    def calculate_average_score(self, reviews):
        """Calculate average score from reviews"""
        if reviews:
            total_score = sum(review.score for review in reviews)
            return round(total_score / len(reviews), 1)
        return None

    def get_forms_context(self, user_review=None):
        """Build forms context"""
        context = {}
        
        if user_review:
            context['review_form'] = GrantReviewForm(instance=user_review)
        else:
            context['review_form'] = GrantReviewForm()
            
        if self.request.user.is_superuser:
            context['decision_form'] = GrantDecisionForm(instance=self.object)
            
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_context = self.get_review_context()
        context.update(review_context)
        context.update(self.get_forms_context(review_context['user_review']))
        return context

    def handle_decision_form(self, request):
        """Handle superuser decision submission"""
        if not request.user.is_superuser:
            messages.error(request, 'You do not have permission to make decisions.')
            return self.redirect_to_current_page()
            
        form = GrantDecisionForm(request.POST, instance=self.object)
        if form.is_valid():
            application = form.save(commit=False)
            if application.status in ['approved', 'rejected', 'waitlisted']:
                application.decided_by = request.user
                application.decided_at = timezone.now()
            application.save()
            
            messages.success(request, 'Final decision recorded successfully!')
            return self.redirect_to_current_page()
        
        context = self.get_context_data()
        context['decision_form'] = form
        return self.render_to_response(context)

    def handle_review_form(self, request):
        """Handle review submission"""
        if self.object.status in ['approved', 'rejected']:
            messages.error(request, 'Cannot review a finalized application.')
            return self.redirect_to_current_page()
        
        user_review = self.get_user_review()
        if user_review:
            form = GrantReviewForm(request.POST, instance=user_review)
        else:
            form = GrantReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.application = self.object
            review.reviewer = request.user
            review.save()
            
            self.auto_update_status()
            messages.success(request, 'Review submitted successfully!')
            return self.redirect_to_current_page()
        
        context = self.get_context_data()
        context['review_form'] = form
        return self.render_to_response(context)

    def auto_update_status(self):
        """Auto-update application status when first review is submitted"""
        if self.object.status == 'submitted':
            self.object.status = 'under_review'
            self.object.save()
            messages.info(self.request, 'Application status automatically updated to "Under Review".')

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm('grants.add_grantreview'):
            messages.error(request, 'You do not have permission to submit reviews.')
            return self.redirect_to_current_page()
            
        self.object = self.get_object()
        
        if request.GET.get('action') == 'decide':
            return self.handle_decision_form(request)
        else:
            return self.handle_review_form(request)
