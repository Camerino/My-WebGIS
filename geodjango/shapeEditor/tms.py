from django.http import HttpResponse
import traceback
import math
from django.http import Http404
from shapeEditor.models import Shapefile
from django.conf import settings
import mapnik
import utils

MAX_ZOOM_LEVEL = 10
TILE_WIDTH = 256
TILE_HEIGHT = 256

def root(request):
	try:
		baseURL = request.build_absolute_uri()
		xml = []
		xml.append('<?xml version="1.0" encoding="utf-8" ?>')
		xml.append('<Services>')
		xml.append('  <TileMapService ' + 
				   'title="ShapeEditor Tile Map Service" ' + 
				   'version="1.0" href="' + baseURL + '/1.0"/>')
		xml.append('</Services>')
		return HttpResponse("\n".join(xml), content_type="text/xml")
	except:
		traceback.print_exc()
		return HttpResponse("")

def service(request, version):
	try:
		if version != "1.0":
			raise Http404
			
		baseURL = request.build_absolute_uri()
		xml = []
		xml.append('<?xml version="1.0" encoding="utf-8"?>')
		xml.append('<TileMapService version="1.0" services="' + 
				   baseURL + '">')
		xml.append('  <Title>ShapeEditor Tile Map Service' + 
				  '</Title>')
		xml.append(' <Abstract></Abstract>')
		xml.append(' <TileMaps>')
		for shapefile in Shapefile.objects.all():
			id = str(shapefile.id)
			xml.append('    <TileMap title="' +
					   shapefile.filename + '"')
			xml.append('             srs="EPSG=4326"')
			xml.append('             href="'+baseURL+'/'+id+'"/>')
		xml.append('  </TileMaps>')
		xml.append('</TileMapService>')
		return HttpResponse("\n".join(xml), content_type="text/xml")
	except:
		traceback.print_exc()
		return HttpResponse("")

def tileMap(request, version, shapefile_id):
	try:
		if version != "1.0":
			raise Http404
			
		try:
			shapefile = Shapefile.objects.get(id=shapefile_id)
		except Shapefile.DoesNotExist:
			raise Http404
			
		baseURL = request.build_absolute_uri()
		xml = []
		xml.append('<?xml version="1.0" encoding="utf-8" ?>')
		xml.append('<TileMap version="1.0" ' +
				   'tilemapservice="' + baseURL + '">')
		xml.append(' <Title>' + shapefile.filename + '</Title>')
		xml.append(' <Abstract></Abstract>')
		xml.append(' <SRS>EPSG:4326</SRS>')
		xml.append(' <BoundingBox minx="-180" miny="-90" ' + 
				   'maxx="180" maxy="90"/>')
		xml.append('  <Origin x="-180" y="-90"/>')
		xml.append('  <TileFormat width="' + str(TILE_WIDTH) + 
				   '" height="' + str(TILE_HEIGHT) + '" ' + 
				   'content_type="image/png" extension="png"/>')
		xml.append('  <TileSets profile="global-geodetic">')
		for zoomLevel in range(0, MAX_ZOOM_LEVEL+1):
			unitsPerPixel = _unitsPerPixel(zoomLevel)
			xml.append('    <TileSet href="' + 
					   baseURL + '/' + str(zoomLevel) + 
					   '" units-per-pixel="' +str(unitsPerPixel) + 
					   '" order="' + str(zoomLevel) + '"/>')
		xml.append('  </TileSets>')
		xml.append('</TileMap>')
		return HttpResponse("\n".join(xml), content_type="text/xml")
	except:
		traceback.print_exc()
		return HttpResponse("")


def tile(request, version, shapefile_id, zoom, x, y):
	shapefile = None
	try:
		if version != "1.0":
			raise Http404
		try:
			shapefile = Shapefile.objects.get(id=shapefile_id)
		except Shapefile.DoesNotExist:
			raise Http404
		zoom = int(zoom)
		x = int(x)
		y = int(y)
		
		if zoom < 0 or zoom > MAX_ZOOM_LEVEL:
			raise Http404
		
		xExtent = _unitsPerPixel(zoom) * TILE_WIDTH
		yExtent = _unitsPerPixel(zoom) * TILE_HEIGHT
		
		minLong  = xExtent * x - 180.0
		minLat   = yExtent * y -  90.0
		maxLong  = minLong + xExtent
		maxLat   = minLat  + xExtent
	
		if (minLong < -180 or maxLong > 180 or 
			minLat < -90 or maxLat > 90):
			raise Http404
			
		map = mapnik.Map(TILE_WIDTH, TILE_HEIGHT,
						"+proj=longlat +datum=WGS84")
		map.background = mapnik.Color("#7391ad")
		
		dbSettings = settings.DATABASES['default']
		datasource = mapnik.PostGIS(host = 'localhost',
									user='alim',
									password='120507',
									dbname='spatial',
									table='"shapeEditor_basemap"',
									srid=4326,
									geometry_field="geometry",
									geometry_table='"shapeEditor_basemap"'
								   )
		
		baseLayer = mapnik.Layer("baseLayer")
		baseLayer.datasource = datasource
		baseLayer.styles.append("baseLayerStyle")
		
		rule = mapnik.Rule()
		rule.symbols.append(mapnik.PolygonSymbolizer(mapnik.Color("#b5d19c")))
		rule.symbols.append(mapnik.LineSymbolizer(mapnik.Color("#000000"), 0.1))
		style = mapnik.Style()
		style.rules.append(rule)
		
		map.append_style("baseLayerStyle", style)
		map.layers.append(baseLayer)
		
		geometryField = utils.calcGeometryField(shapefile.geom_type)
		query = '(select ' + geometryField + ' from "shapeEditor_feature" where' + ' shapefile_id=' + str(shapefile.id) + ') as geom'
		datasource = mapnik.PostGIS(host = 'localhost',
									user='alim',
									password='120507',
									dbname='spatial',
									table=query,
									srid=4326,
									geometry_field=geometryField,
									geometry_table='"shapeEditor_feature"')
		
		featureLayer = mapnik.Layer("featureLayer")
		featureLayer.datasource = datasource
		featureLayer.styles.append("featureLayerStyle")
		
		rule = mapnik.Rule()
		if shapefile.geom_type in ["Point", "MultiPoint"]:
			rule.symbols.append(mapnik.PointSymbolizer())
		elif shapefile.geom_type in ["LineString", "MultiLineString"]:
			rule.symbols.append(mapnik.LineSymbolizer(mapnik.Color("#000000"), 0.5))
		elif shapefile.geom_type in ["Polygon", "MultiPolygon"]:
			rule.symbols.append(mapnik.PolygonSymbolizer(mapnik.Color("#f7edee")))
			rule.symbols.append(mapnik.LineSymbolizer(mapnik.Color("#000000"), 0.5))
		style = mapnik.Style()
		style.rules.append(rule)
		
		map.append_style("featureLayerStyle", style)
		map.layers.append(featureLayer)
		map.zoom_to_box(mapnik.Envelope(minLong, minLat, maxLong, maxLat))
		image = mapnik.Image(TILE_WIDTH, TILE_HEIGHT)
		mapnik.render(map, image)
		imageData = image.tostring('png')
		return HttpResponse(imageData, content_type = "image/png")
	
	except:
		traceback.print_exc()
		return HttpResponse("")

def _unitsPerPixel(zoomLevel):
	return 0.703128 / math.pow(2, zoomLevel)












	