from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import(
    RegisterView, LoginView, UserProfileView,upload_course,
    AssignmentCreateView,AssignmentEditDeleteView,EnrollCourseView,
    UploadCourseFileView,EditCourseView,DeleteCourseFileView,DeleteCourseView,
    AnnouncementCreateView,AnnouncementDetailView,EnrolledCoursesView,
    ProgressDetailView,MyCoursesView,CourseDetailView,AnnouncementUpdateDeleteView,get_all_courses)

urlpatterns = [
    path('courses/<int:course_id>/', CourseDetailView.as_view(), name='course-detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('upload-course/', upload_course, name='upload-course'),
    path('enroll/', EnrollCourseView.as_view(), name='enroll-course'),
    path('upload-course-file/', UploadCourseFileView.as_view(), name='upload-course-file'),
    path('edit-course/<int:pk>/', EditCourseView.as_view(), name='edit-course'),
    path('course-file/delete/<int:pk>/', DeleteCourseFileView.as_view(), name='delete-course-file'),
    path('course/delete/<int:pk>/', DeleteCourseView.as_view(), name='delete-course'),
    path('assignments/create/', AssignmentCreateView.as_view(), name='assignment-create'),
    path('assignments/<int:pk>/', AssignmentEditDeleteView.as_view(), name='assignment-edit-delete'),
    path('enrolled-courses/', EnrolledCoursesView.as_view(), name='enrolled-courses'),
    path('my-courses/', MyCoursesView.as_view(), name='my-courses'),
    path('announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('progress/<int:pk>/', ProgressDetailView.as_view(), name='progress-detail'),
    path('announcements/create/', AnnouncementCreateView.as_view(), name='create-announcement'),
    path('announcements/<int:pk>/', AnnouncementUpdateDeleteView.as_view(), name='announcement-detail'),
    path('courses/', get_all_courses, name="all-courses")
]

