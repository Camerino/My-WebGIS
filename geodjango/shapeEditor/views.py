from django.shortcuts import render_to_response

# Create your views here.
from django.http import HttpResponseRedirect
from shapeEditor.models import Shapefile
from shapeEditor.forms import ImportShapefileForm
import shapefileIO

def listShapefiles(request):
    shapefiles = Shapefile.objects.all().order_by('filename')
    return render_to_response("listShapefiles.html", {'shapefiles' : shapefiles})

def importShapefile(request):
	if request.method == "GET":
		form = ImportShapefileForm()
		return render_to_response("importShapefile.html",
								  {'form' : form,
								   'errMsg' : None})
	elif request.method == "POST":
		errMsg = None
		form = ImportShapefileForm(request.POST,
								   request.FILES)
		if form.is_valid():
			shapefile = request.FILES['import_file']
			encoding = request.POST['character_encoding']
			errMsg = shapefileIO.importData(shapefile, encoding)
			if errMsg == None:
				return HttpResponseRedirect("/shape-editor")
		return render_to_response("importShapefile.html", {'form' : form, 'errMsg' : errMsg})
	
def exportShapefile(request, shapefile_id):
	try:
		shapefile = Shapefile.objects.get(id=shapefile_id)
	except Shapefile.DoesNotExist:
		raise Http404
	return shapefileIO.exportData(shapefile)

def editShapefile(request, shapefile_id):
	try:
		shapefile = Shapefile.objects.get(id=shapefile_id)
	except:
		raise Http404
	tmsURL = "http://"+request.get_host()+"/shape-editor/tms/"
	return render_to_response("selectFeature.html",
							 {'shapefile' : shapefile, 'tmsURL' : tmsURL})
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
