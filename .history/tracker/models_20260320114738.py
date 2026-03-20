class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # Add your payment methods here
    METHOD_CHOICES = [
        ("bank", "Bank Transfer (e.g., Stanbic)"),
        ("ecocash", "EcoCash"),
        ("physical", "Physical Cash / Receipt"),
    ]

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField(default=timezone.now().year)

    # Add the new field, defaulting to bank transfer
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
