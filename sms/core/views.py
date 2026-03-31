from django.shortcuts import render
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

# Create your views here.
from django.shortcuts import render

def home_view(request):
    return render(request, 'core/home.html')

@login_required
@require_POST
def chatbot_ask(request):
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()

        if not question:
            return JsonResponse({"error": "No question provided"}, status=400)

        response = requests.post(
            "http://127.0.0.1:5000/ask",
            json={"question": question},
            timeout=30
        )

        return JsonResponse(response.json(), status=response.status_code)

    except requests.exceptions.RequestException:
        return JsonResponse(
            {"error": "Chatbot service is currently unavailable."},
            status=503
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)