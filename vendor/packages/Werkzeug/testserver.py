from werkzeug import Request, Response, run_simple

@Request.application
def application(request):
    if request.method == 'POST':
        return Response(repr(request.files) + "\n" + repr(request.form), status=500)
    return Response('<form action="" method="post" enctype="multipart/form-data"><input type="file" name="f"><input type="submit" value="Upload"></form>', mimetype='text/html')

run_simple('', 3000, application, use_reloader=True, use_debugger=True)
