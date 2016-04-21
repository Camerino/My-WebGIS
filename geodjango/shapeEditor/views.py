from django.shortcuts import render_to_response
from django.contrib.gis.geos import Point
from django.http import HttpResponseRedirect, HttpResponse
from shapeEditor.models import Shapefile, Feature
from shapeEditor.forms import ImportShapefileForm
import shapefileIO
import traceback
import utils

def homePage(request):
    return render_to_response("base.html", {})


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

def editShapefile (request, shapefile_id) : 

    shapefile = None
    try:
        shapefile = Shapefile.objects.get (id=shapefile_id )
    except:
        raise Http404

    tmsURL         = "http://" + request.get_host () + "/shape-editor/tms/"
    findFeatureURL = "http://" + request.get_host () + "/shape-editor/findFeature" 
    addFeatureURL  = "http://" + request.get_host () + "/shape-editor/editFeature/" + str(shapefile_id) 

    return render_to_response ("selectFeature.html", 
                               {  'shapefile'     : shapefile,
                                  'findFeatureURL': findFeatureURL, 
                                  'addFeatureURL' : addFeatureURL,
                                  'tmsURL'        : tmsURL 
                               } )

def findFeature(request):
    try:
        shapefile_id = int(request.GET['shapefile_id'])
        latitude = float(request.GET['latitude'])
        longitude = float(request.GET['longitude'])
        
        shapefile = Shapefile.objects.get(id=shapefile_id)
        pt = Point(longitude, latitude)
        radius = utils.calcSearchRadius(latitude, longitude, 100)
        
        if shapefile.geom_type == "Point":
            query = Feature.objects.filter(
                geom_point__dwithin=(pt, radius))
        elif shapefile.geom_type in ["LineString", "MultiLineString"]:
            query = Feature.objects.filter ( geom_multilinestring__dwithin =( pt, radius))
        elif shapefile.geom_type in ["Polygon", "MultiPolygon"]:
            query = Feature.objects.filter(geom_multipolygon__dwithin =(pt, radius))
        elif shapefile.geom_type == "MultiPoint":
            query = Feature.objects.filter(geom_multipoint__dwithin =(pt, radius))
        elif shapefile.geom_type == "GeometryCollection":
            query = Feature.objects.filter(geom_geometrycollection__dwithin =(pt, radius))
        else:
            print "Unsupported geometry: "+ shapefile.geom_type
            return HttpResponse("")
        
        if query.count() != 1:
            return HttpResponse("")
        
        feature = query.all()[0]
        return HttpResponse("/shape-editor/editFeature/" + 
                            str(shapefile_id)+"/"+str(feature.id))
    except:
        traceback.print_exc()
        return HttpResponse("")
    
def editFeature(request, shapefile_id, feature_id=None):
    if request.method == "POST" and "delete" in request.POST:
        return HttpResponseRedirect("/shape-editor/deleteFeature/"
                                   +shapefile_id+"/"+feature_id)
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)
    except Shapefile.DoesNotExist:
        raise Http404
        
    if feature_id == None:
        feature = Feature(shapefile=shapefile)
    else:
        try:
            feature = Feature.objects.get(id=feature_id)
        except Feature.DoesNotExist:
            raise Http404
        
    attributes = []
    for attrValue in feature.attributevalue_set.all():
        attributes.append([attrValue.attribute.name,
                               attrValue.value])
    attributes.sort()
        
    geometryField = utils.calcGeometryField(shapefile.geom_type)
    formType = utils.getMapForm(shapefile)
        
    if request.method == "GET":
        wkt = getattr(feature, geometryField)
        form = formType({'geometry' : wkt})
        return render_to_response("editFeature.html",
                                 {'shapefile' : shapefile,
                                  'form' : form,
                                  'attributes' : attributes})
    elif request.method == "POST":
        form = formType(request.POST)
        try:
            if form.is_valid():
                wkt = form.cleaned_data['geometry']
                setattr(feature, geometryField, wkt)
                feature.save()
                return HttpResponseRedirect("/shape-editor/edit/" + 
                                               shapefile_id)
        except ValueError:
            pass
        return render_to_response("editFeature.html",
                                 {'shapefile' : shapefile,
                                  'form' : form,
                                  'attributes' : attributes})
        
def deleteFeature(request, shapefile_id, feature_id):
    try:
        feature = Feature.objects.get(id=feature_id)
    except Feature.DoesNotExist:
        raise Http404
        
    if request.method == "POST":
        if request.POST['confirm'] == "1":
            reature.delete()
        return HttpResponseRedirect("/shape-editor/edit/"+shapefile_id)
    return render_to_response("deleteFeature.html")

def deleteShapefile(request, shapefile_id):
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)
    except Shapefile.DoesNotExist:
        raise Http404
        
    if request.method == "GET":
        return render_to_response("deleteShapefile.html",
                                 {'shapefile' : shapefile})
    
    elif request.method == "POST":
        if request.POST['confirm'] == "1":
            shapefile.delete()
        return HttpResponseRedirect("/shape-editor")
    
    
    
    
    
    
    
    
    
    
        



















          
          
            
            
            
            
            
            
    

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
