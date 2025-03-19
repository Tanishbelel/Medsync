from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .ocr_processor import process_prescription

def upload_prescription(request):
    if request.method == "POST":
        image = request.FILES["prescription"]
        medicine_data = process_prescription(image)

        # Convert queryset to dictionary
        medicine_dict = {med.name: f"{med.dosage} {med.description}" for med in medicine_data}

        return render(request, "result.html", {"medicines": medicine_dict})

    return render(request, "result.html")