# Django built-in imports
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

# Image processing
from PIL import Image, ImageDraw, ImageFont

# System / utilities
import os


class User(AbstractUser):
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15, unique=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.username
    

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    experience = models.IntegerField(blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    subjects_taught = models.CharField(max_length=255, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} (Teacher)"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    enrollment_year = models.IntegerField()
    grade = models.CharField(max_length=10)
    section = models.CharField(max_length=5, blank=True, null=True)
    parent_contact = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} (Student)"
    
class Course(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField(Student, related_name='courses', blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    total_lessons = models.PositiveIntegerField(null=False)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)  # ✅ Add this field

    def __str__(self):
        return f"{self.title} by {self.teacher.user.username}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"

# ✅ Move the signal function outside the model class
@receiver(post_save, sender=Enrollment)
def create_progress_for_enrollment(sender, instance, created, **kwargs):
    if created:
        Progress.objects.create(
            student=instance.student,
            course=instance.course,
            total_lessons=instance.course.total_lessons
        )

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    
    def __str__(self):
        return f"{self.title} for {self.course.title}"

class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Announcement: {self.title} for {self.course.title}"
    
class CourseFile(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='course_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course.title})"

class Progress(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='progress')
    completed_lessons = models.IntegerField(default=0)
    total_lessons = models.IntegerField()
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title} Progress"

    def save(self, *args, **kwargs):
        if self.completed_lessons >= self.total_lessons:
            self.is_completed = True
            self.completion_date = now().date()
        super().save(*args, **kwargs)

# ✅
class Certificate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    date_issued = models.DateField(auto_now_add=True)
    certificate_file = models.ImageField(upload_to='certificates/', blank=True, null=True)

    def __str__(self):
        return f"Certificate for {self.student.user.username} - {self.course.title}"

    def generate_certificate(self):
        """Generates a certificate image when the student completes the course."""
        # Define certificate size and background
        img = Image.new('RGB', (800, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Load font (ensure you have a .ttf font file in your project directory)
        font_path = os.path.join(os.path.dirname(__file__), 'arial.ttf')
        font = ImageFont.truetype(font_path, 40)

        # Add text
        draw.text((200, 100), "Certificate of Completion", fill="black", font=font)
        draw.text((200, 200), f"Awarded to {self.student.user.username}", fill="black", font=font)
        draw.text((200, 300), f"For completing {self.course.title}", fill="black", font=font)
        draw.text((200, 400), f"Date: {self.date_issued}", fill="black", font=font)

        # Save the certificate
        filename = f"cert_{slugify(self.student.user.username)}_{slugify(self.course.title)}.png"
        cert_path = os.path.join('media/certificates', filename)
        img.save(cert_path)

        # Save file path to model
        self.certificate_file = f"certificates/{filename}"
        self.save()
