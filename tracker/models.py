import hashlib
from django.db import models
from django.utils import timezone



class Group(models.Model):
    name = models.CharField(
        max_length=100, unique=True, help_text="e.g., Planted 2026 CCWP05"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="members", null=True
    )

    # 👉 NEW: Supervisor exemption and Birthday
    is_exempt_from_paying = models.BooleanField(
        default=False,
        help_text="Check this for supervisors like Sis Trudy so they don't show as owing money.",
    )
    date_of_birth = models.DateField(blank=True, null=True)
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
        approved = self.payments.filter(status="approved")
        return sum(p.amount for p in approved)

    @property
    def total_attendance(self):
        # Counts how many times they attended (either physical or online)
        return self.attendance_records.filter(mode__in=["physical", "online"]).count()


class Topic(models.Model):
    group = models.ForeignKey(Group, related_name="topics", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Meeting(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="meetings", null=True
    )

    date = models.DateField(default=timezone.now)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.topic} - {self.date}"


class Attendance(models.Model):
    MODE_CHOICES = [
        ("physical", "Physical"),
        ("online", "Online"),
        ("absent", "Absent"),
    ]
    comments = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Why were they absent? Any payment notes?",
    )

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

    receipt_hash = models.CharField(max_length=64, blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        # Only calculate the hash if there is an image and it hasn't been hashed yet
        if self.receipt_image and not self.receipt_hash:
            hasher = hashlib.sha256()
            for chunk in self.receipt_image.chunks():
                hasher.update(chunk)
            self.receipt_hash = hasher.hexdigest()

        super().save(*args, **kwargs)


class WhatsAppDraft(models.Model):
    # We use unique=True so a user only ever has one active draft at a time
    phone_number = models.CharField(max_length=20, unique=True)

    # These fields can be blank initially, and we fill them in step-by-step
    image_id = models.CharField(max_length=255, null=True, blank=True)
    month = models.CharField(max_length=50, null=True, blank=True)
    payment_mode = models.CharField(max_length=50, null=True, blank=True)

    # A timestamp just in case we ever want to clear out old, abandoned drafts
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Draft for {self.phone_number}"
