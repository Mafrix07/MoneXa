"""
TresorIA chatbot view.

POST /api/assistant/ask/
Body: {"question": "Combien ai-je en T-Money ?"}
Response: {"answer": "Votre solde T-Money est de ...", "question": "..."}

Rate limited: 10 requests / minute per user.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import AskSerializer
from .services import answer_question


class AssistantThrottle(UserRateThrottle):
    scope = "assistant"


class AskView(APIView):
    """POST /api/assistant/ask/"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AssistantThrottle]

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        answer = answer_question(request.user, question)
        return Response({"answer": answer, "question": question})
