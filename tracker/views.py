from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
from .models import Member, Meeting, Attendance
import json
import os
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def upload_receipt(request):
    error_message = None  # Set a blank error message initially

    if request.method == "POST":
        form = ReceiptUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Try to save the form to the database
                form.save()
                return redirect("upload_success")
            except IntegrityError:
                # If the database rejects it because of a duplicate, do this instead:
                error_message = "Hold on! A receipt has already been uploaded for this member for the selected month."
    else:
        form = ReceiptUploadForm()

    return render(
        request, "tracker/upload.html", {"form": form, "error_message": error_message}
    )


def upload_success(request):
    return render(request, "tracker/success.html")


def download_master_summary(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Roots Master Summary Report - All Members", styles["Title"])
    elements.append(title)

    data = [["Member Name", "Total Paid (Approved)", "Meeting Breakdown"]]

    # Automatically grab ALL members and ALL meetings
    all_meetings = Meeting.objects.all().order_by("date")
    all_members = Member.objects.all().order_by("first_name")

    for member in all_members:
        attendance_details = ""
        for meeting in all_meetings:
            record = Attendance.objects.filter(member=member, meeting=meeting).first()

            if record and record.mode in ["physical", "online"]:
                status = (
                    f"<font color='green'>Attended ({record.get_mode_display()})</font>"
                )
            else:
                status = "<font color='red'>Absent</font>"

            attendance_details += (
                f"<b>{meeting.date.strftime('%b %d, %Y')}</b>: {status}<br/>"
            )

        if not all_meetings:
            attendance_details = "No meetings recorded yet."

        p_attendance = Paragraph(attendance_details, styles["Normal"])

        data.append(
            [
                f"{member.first_name} {member.last_name}",
                f"${member.total_approved_payments}",
                p_attendance,
            ]
        )

    t = Table(data, colWidths=[150, 120, 250])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8e44ad")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
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
    # This names the file nicely for you
    response["Content-Disposition"] = (
        'attachment; filename="Roots_Complete_Group_Summary.pdf"'
    )
    response.write(pdf)

    return response


@csrf_exempt
def whatsapp_webhook(request):
    # 1. THE HANDSHAKE (Meta verifying your server)
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        # We will set this secret password in our .env file next!
        VERIFY_TOKEN = "Password@1"

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified by Meta!")
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse("Forbidden", status=403)

    # 2. THE INBOX (Receiving actual WhatsApp messages)
    elif request.method == "POST":
        try:
            body = json.loads(request.body)

            # Print the incoming message to your terminal so we can see it!
            print("📩 NEW WHATSAPP MESSAGE RECEIVED:")
            print(json.dumps(body, indent=2))

            # Always return a 200 OK so Meta knows we got it
            return HttpResponse("EVENT_RECEIVED", status=200)

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return HttpResponse(status=400)

    return HttpResponse("Method not allowed", status=405)
