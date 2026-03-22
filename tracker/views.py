from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
import requests
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
    # 1. THE HANDSHAKE (LEAVE THIS ALONE!)
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        # ... (all your handshake code stays exactly the same) ...

    # 2. THE INBOX & ROUTING
    elif request.method == "POST":
        try:
            body = json.loads(request.body)

            if "object" in body and body["object"] == "whatsapp_business_account":
                entry = body.get("entry", [{}])[0]
                changes = entry.get("changes", [{}])[0]
                value = changes.get("value", {})

                if "messages" in value:
                    message = value["messages"][0]
                    sender_phone = message["from"]
                    message_type = message.get("type")

                    # Route A: It's a standard text message
                    if message_type == "text":
                        incoming_text = message["text"]["body"]
                        print(
                            f"📩 Received TEXT: '{incoming_text}' from {sender_phone}"
                        )
                        send_whatsapp_reply(sender_phone, incoming_text)

                    # Route B: It's an image! (Likely a receipt)
                    elif message_type == "image":
                        image_id = message["image"]["id"]
                        print(
                            f"📸 Received IMAGE with ID: {image_id} from {sender_phone}"
                        )
                        send_receipt_confirmation_button(sender_phone)
                        download_whatsapp_media(image_id)

                    # Route C: It's an interactive button click!
                    elif message_type == "interactive":
                        button_reply = message["interactive"].get("button_reply", {})
                        button_id = button_reply.get("id")
                        print(
                            f"🔘 User clicked button ID: {button_id} from {sender_phone}"
                        )

                        if button_id == "btn_yes_receipt":
                            # Send them the popup list of months!
                            send_month_selection_list(sender_phone),
                            

                        elif button_id == "btn_no_receipt":
                            send_whatsapp_reply(
                                sender_phone,
                                "No problem! I will toss that photo in the trash and pretend I didn't see it. 🗑️",
                            )
            return HttpResponse("EVENT_RECEIVED", status=200)

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            return HttpResponse(status=400)

    return HttpResponse("Method not allowed", status=405)


# 3. THE OUTBOX (Sending a custom text message back)
def send_whatsapp_reply(recipient_phone, received_text):
    ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    # DEBUG 1: Let's make sure your server can actually see the keys!
    print(f"🔑 DEBUG KEY CHECK - Phone ID: {PHONE_NUMBER_ID}")

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    reply_text = f"Roots has received your message: '{received_text}'. Your bot is officially live!"

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": reply_text},
    }

    # DEBUG 2: Capture Meta's exact response and print it to the logs
    print(f"🚀 Firing message to {recipient_phone}...")
    response = requests.post(url, headers=headers, json=payload)

    print(f"📤 META API RESPONSE CODE: {response.status_code}")
    print(f"📝 META API DETAILS: {response.text}")


def download_whatsapp_media(media_id):
    ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # DANCE STEP 1: Ask Meta for the secure download URL
    print(f"🔍 Asking Meta for the URL for media ID: {media_id}")
    url_request = requests.get(
        f"https://graph.facebook.com/v22.0/{media_id}", headers=headers
    )
    media_data = url_request.json()

    if "url" not in media_data:
        print(f"❌ Failed to get URL. Meta said: {media_data}")
        return None

    media_url = media_data["url"]
    print(f"✅ Got secure URL! Downloading image now...")

    # DANCE STEP 2: Use the URL to download the actual image bytes
    image_response = requests.get(media_url, headers=headers)

    if image_response.status_code == 200:
        # Save it temporarily to your server so we can prove it works!
        filename = f"whatsapp_receipt_{media_id}.jpg"
        with open(filename, "wb") as f:
            f.write(image_response.content)


        print(f"🎉 SUCCESS! Image downloaded and saved as {filename}")
        return filename
    else:
        print(f"❌ Failed to download image. Status: {image_response.status_code}")
        return None
# 4. THE INTERACTIVE MENU (Asking Yes/No)
def send_receipt_confirmation_button(recipient_phone):
    ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # The special payload for Interactive Buttons
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "I just received an image! 📸\n\nIs this a Roots monthly payment receipt?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": "btn_yes_receipt", "title": "✅ Yes, it is"},
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btn_no_receipt",
                            "title": "❌ No, just a photo",
                        },
                    },
                ]
            },
        },
    }


    print(f"🔘 Sending interactive buttons to {recipient_phone}...")
    requests.post(url, headers=headers, json=payload)
# 5. THE LIST MENU (Asking for the Month)
def send_month_selection_list(recipient_phone):
    ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # We create a list of all 12 months
    month_rows = [
        {"id": "month_jan", "title": "January"},
        {"id": "month_feb", "title": "February"},
        {"id": "month_mar", "title": "March"},
        {"id": "month_apr", "title": "April"},
        {"id": "month_may", "title": "May"},
        {"id": "month_jun", "title": "June"},
        {"id": "month_jul", "title": "July"},
        {"id": "month_aug", "title": "August"},
        {"id": "month_sep", "title": "September"},
        {"id": "month_oct", "title": "October"},
        {"id": "month_nov", "title": "November"},
        {"id": "month_dec", "title": "December"},
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "📅 Payment Month"},
            "body": {"text": "Perfect! Which month is this $10 receipt paying for?"},
            "footer": {"text": "Roots Command Center"},
            "action": {
                "button": "Tap to Select Month",
                "sections": [{"title": "2026 Months", "rows": month_rows}],
            },
        },
    }

    print(f"📋 Sending month list menu to {recipient_phone}...")
    requests.post(url, headers=headers, json=payload)
