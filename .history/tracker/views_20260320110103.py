from django.shortcuts import render, redirect
from .forms import ReceiptUploadForm


def upload_receipt(request):
    # If someone clicks "Submit" on the form
    if request.method == "POST":
        # request.FILES is crucial here because we are handling an image!
        form = ReceiptUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("upload_success")  # Send them to a thank you page

    # If someone just visits the link for the first time
    else:
        form = ReceiptUploadForm()

    return render(request, "tracker/upload.html", {"form": form})


def upload_success(request):
    return render(request, "tracker/success.html")
