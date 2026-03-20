from django.contrib import admin
from .models import Member, Meeting, Attendance, Payment

admin.site.register(Member)
admin.site.register(Meeting)
admin.site.register(Attendance)


@admin.register(Payment)

# --- THE MEMBER SUMMARY PDF GENERATOR ---
@admin.action(description="Download Member Summary Report")
def export_member_summary_pdf(modeladmin, request, queryset):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Roots Master Summary Report", styles["Title"])
    elements.append(title)

    # Create the table headers
    data = [["Member Name", "Total Paid (Approved)", "Meetings Attended"]]

    # Loop through the selected members and pull our new calculations
    for member in queryset:
        data.append(
            [
                f"{member.first_name} {member.last_name}",
                f"${member.total_approved_payments}",
                str(member.total_attendance),
            ]
        )

    t = Table(data)
    t.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#8e44ad"),
                ),  # Purple header
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(t)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="roots_member_summary.pdf"'
    response.write(pdf)

    return response


# --- THE NEW MEMBER DASHBOARD VIEW ---
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    # This dictates what columns show up on the screen
    list_display = (
        "first_name",
        "last_name",
        "phone_number",
        "total_approved_payments",
        "total_attendance",
    )
    search_fields = ("first_name", "last_name")

    # Attach the new PDF download button
    actions = [export_member_summary_pdf]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ("member", "month", "year", "status", "uploaded_at")
    list_filter = ("status", "month", "year")
    search_fields = ("member__first_name", "member__last_name")
