from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Progress

@receiver(post_save, sender=Progress)
def create_certificate(sender, instance, **kwargs):
    """Generate a certificate only if the student is enrolled in the course and has completed it."""
    if instance.is_completed:
        from .models import Enrollment, Certificate  # Import inside function to avoid circular import

        is_enrolled = Enrollment.objects.filter(student=instance.student, course=instance.course).exists()
        
        if is_enrolled:
            certificate, created = Certificate.objects.get_or_create(
                student=instance.student,
                course=instance.course
            )
            if created:
                certificate.generate_certificate()
