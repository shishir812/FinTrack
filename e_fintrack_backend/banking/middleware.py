class SimpleCorsMiddleware:
    allowed_origins = {'http://localhost:5173', 'http://127.0.0.1:5173'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS':
            from django.http import HttpResponse
            response = HttpResponse()
        else:
            response = self.get_response(request)
        origin = request.headers.get('Origin')
        response['Access-Control-Allow-Origin'] = origin if origin in self.allowed_origins else 'http://localhost:5173'
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response
