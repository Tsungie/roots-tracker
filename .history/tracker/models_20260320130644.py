import hashlib
from django.db import models
from django.utils import timezone


class Member(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(
        max_length=20, unique=True, help_text="WhatsApp number format: +263..."
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_approved_payments(self):
        # Grabs all 'approved' payments for this member and sums the amount
        approved = self.payments.filter(status='approved')
        return sum(p.amount for p in approved)

    @property
    def total_attendance(self):
        # Counts how many times they attended (either physical or online)
        return self.attendance_records.filter(mode__in=['physical', 'online']).count()

class Meeting(models.Model):
    date = models.DateField(default=timezone.now)
    topic = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Roots Meeting - {self.date}"


class Attendance(models.Model):
    MODE_CHOICES = [
        ("physical", "Physical"),
        ("online", "Online"),
        ("absent", "Absent"),
    ]

    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="attendees"
    )
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="attendance_records"
    )
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="absent")

    class Meta:
        unique_together = ["meeting", "member"]  # Prevents duplicate attendance marking

    def __str__(self):
        return f"{self.member} - {self.get_mode_display()} on {self.meeting.date}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # We need to make sure this is included!
    MONTH_CHOICES = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    METHOD_CHOICES = [
        ("bank", "Bank Transfer"),
        ("ecocash", "EcoCash"),
        ("physical", "Physical Cash / Receipt"),
    ]

    member = models.ForeignKey(
        "Member", on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField(default=timezone.now().year)
    payment_method = models.CharField(
        max_length=15, choices=METHOD_CHOICES, default="bank"
    )
    receipt_image = models.ImageField(upload_to="receipts/%Y/%m/")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    admin_notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ["member", "month", "year"]
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.member} - {self.get_month_display()} {self.year} ({self.status})"
    
    


class Dashboard(Payment):
    class Meta:
        proxy = True  # This tells Django NOT to create a new database table
        verbose_name = "📊 Overview Dashboard"
        verbose_name_plural = "📊 Overview Dashboard"
