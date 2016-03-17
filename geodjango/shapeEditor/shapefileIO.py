import os, os.path, tempfile, zipfile, shutil, traceback
from osgeo import ogr, osr
import utils
from shapeEditor.models import Shapefile, Attribute, Feature, AttributeValue
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.http import HttpResponse
from wsgiref.util import FileWrapper

def importData(shapefile, characterEncoding):
	fd,fname = tempfile.mkstemp(suffix=".zip")
	os.close(fd)
	
	f = open(fname, "wb")
	for chunk in shapefile.chunks():
		f.write(chunk)
	f.close()
	
	if not zipfile.is_zipfile(fname):
		os.remove(fname)
		return "Not a valid zip archive."
	
	zip = zipfile.ZipFile(fname)
	
	required_suffixes = [".shp", ".shx", ".dbf", ".prj"]
	hasSuffix = {}
	for suffix in required_suffixes:
		hasSuffix[suffix] = False
		
	for info in zip.infolist():
		extension = os.path.splitext(info.filename)[1].lower()
		if extension in required_suffixes:
			hasSuffix[extension] = True
			
	for suffix in required_suffixes:
		if not hasSuffix[suffix]:
			zip.close()
			os.remove(fname)
			return "Archive missing required "+suffix+" file."
			
	zip = zipfile.ZipFile(fname)
	shapefileName = None
	dirname = tempfile.mkdtemp()
	for info in zip.infolist():
		if info.filename.endswith(".shp"):
			shapefileName = info.filename
		
		dstFile = os.path.join(dirname, info.filename)
		f = open(dstFile, "wb")
		f.write(zip.read(info.filename))
		f.close()
	zip.close()
	
	try:
		datasource = ogr.Open(os.path.join(dirname, shapefileName))
		layer = datasource.GetLayer(0)
		shapefileOK = True
	
	except:
		traceback.print_exc()
		shapefileOK = False
		
	if not shapefileOK:
		os.remove(fname)
		shutil.rmtree(dirname)
		return "Not a valid shapefile."
	
	SrcSpatialRef = layer.GetSpatialRef()
	geometryType = layer.GetLayerDefn().GetGeomType()
	geometryName = utils.ogrTypeToGeometryName(geometryType)
	shapefile = Shapefile(filename=shapefileName, 
						  srs_wkt=SrcSpatialRef.ExportToWkt(),
						  geom_type=geometryName,
						  encoding=characterEncoding)
	shapefile.save()
	
	attributes = []
	layerDef = layer.GetLayerDefn()
	for i in range(layerDef.GetFieldCount()):
		fieldDef = layerDef.GetFieldDefn(i)
		attr = Attribute(shapefile=shapefile,
						 name=fieldDef.GetName(),
						 type=fieldDef.GetType(),
						 width=fieldDef.GetWidth(),
						 precision=fieldDef.GetPrecision())
		attr.save()
		attributes.append(attr)
		
	dstSpatialRef = osr.SpatialReference()
	dstSpatialRef.ImportFromEPSG(4326)
	
	coordTransform = osr.CoordinateTransformation(SrcSpatialRef, dstSpatialRef)
	
	for i in range(layer.GetFeatureCount()):
		srcFeature = layer.GetFeature(i)
		srcGeometry = srcFeature.GetGeometryRef()
		srcGeometry.Transform(coordTransform)
		geometry = GEOSGeometry(srcGeometry.ExportToWkt())
		geometry = utils.wrapGEOSGeometry(geometry)
		geometryField = utils.calcGeometryField(geometryName)
													 
						 
	args = {}
	args['shapefile'] = shapefile
	args[geometryField] = geometry
	feature = Feature(**args)
	feature.save()
	
	for attr in attributes:
		success,result = utils.getOGRFeatureAttribute(attr, srcFeature, characterEncoding)
		
		if not success:
			os.remove(fname)
			shutil.rmtree(dirname)
			shapefile.delete()
			return result
		attrValue = AttributeValue(feature=feature,
								   attribute=attr,
								   value=result)
		attrValue.save()
	os.remove(fname)
	shutil.rmtree(dirname)
	return None
		
def exportData(shapefile):
	dstDir = tempfile.mkdtemp()
	dstFile = str(os.path.join(dstDir, shapefile.filename))
	
	dstSpatialRef = osr.SpatialReference()
	dstSpatialRef.ImportFromWkt(shapefile.srs_wkt)
	
	driver = ogr.GetDriverByName("ESRI Shapefile")
	datasource = driver.CreateDataSource(dstFile)
	layer = datasource.CreateLayer(str(shapefile.filename),
								   dstSpatialRef)
	for attr in shapefile.attribute_set.all():
		field = ogr.FieldDefn(str(attr.name), attr.type)
		field.SetWidth(attr.width)
		field.SetPrecision(attr.precision)
		layer.CreateField(field)
	
	srcSpatialRef = osr.SpatialReference()
	srcSpatialRef.ImportFromEPSG(4326)
	
	coordTransform = osr.CoordinateTransformation(srcSpatialRef,
												  dstSpatialRef)
	geomField = utils.calcGeometryField(shapefile.geom_type)
	
	for feature in shapefile.feature_set.all():
		geometry = getattr(feature, geomField)
		geometry = utils.unwrapGEOSGeometry(geometry)
		dstGeometry = ogr.CreateGeometryFromWkt(geometry.wkt)
		dstGeometry.Transform(coordTransform)
		
		dstFeature = ogr.Feature(layer.GetLayerDefn())
		dstFeature.SetGeometry(dstGeometry)
		
		for attrValue in feature.attributevalue_set.all():
			utils.setOGRFeatureAttribute(attrValue.attribute,
										 attrValue.value,
										 dstFeature,
										 shapefile.encoding)
		
		layer.CreateFeature(dstFeature)
		dstFeature.Destroy()
		
	datasource.Destroy()
	
	temp = tempfile.TemporaryFile()
	zip = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
	
	shapefileBase = os.path.splitext(dstFile)[0]
	shapefileName = os.path.splitext(shapefile.filename)[0]
	
	for fName in os.listdir(dstDir):
		zip.write(os.path.join(dstDir, fName), fName)
		
	zip.close()
	shutil.rmtree(dstDir)
	
	f = FileWrapper(temp)
	response = HttpResponse(f, content_type="application/zip")
	response['Content-Disposition'] = \
	    "attachment; filename=" + shapefileName + ".zip"
	response['Content-Length'] = temp.tell()
	temp.seek(0)
	return response

		
	
		
	
		
		
				  

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
		
