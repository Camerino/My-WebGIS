"""geodjango URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import patterns, include, url
from django.contrib.gis import admin
from shapeEditor import views
from shapeEditor import tms
admin.autodiscover()

urlpatterns = [
    url(r'^shape-editor$', views.listShapefiles, name="listShapefiles"),
    url(r'^admin/', admin.site.urls),
	url(r'^shape-editor/import$', views.importShapefile, name="importShapefile"),
	url(r'^shape-editor/findFeature$', views.findFeature, name="findFeature"),
	url(r'^shape-editor/edit/(?P<shapefile_id>\d+)$', views.editShapefile, name = "editShapefile"),
	url(r'^shape-editor/delete/(?P<shapefile_id>\d+)$', views.deleteShapefile, name = "deleteShapefile"),
	url(r'^shape-editor/editFeature/(?P<shapefile_id>\d+)$', views.editFeature, name = "addOrEditFeature"),
	url(r'^shape-editor/editFeature/(?P<shapefile_id>\d+)/' + 
		r'(?P<feature_id>\d+)$', views.editFeature, name = "editFeature"),
	url(r'^shape-editor/deleteFeature/(?P<shapefile_id>\d+)/' + 
		r'(?P<feature_id>\d+)$', views.deleteFeature, name = "deleteFeature"),
	url(r'^shape-editor/export/(?P<shapefile_id>\d+)$', views.exportShapefile, name = "exportShapefile"),
	url(r'^shape-editor/tms$', tms.root, name="Tile Map Server"),
	url(r'^shape-editor/tms/(?P<version>[0-9.]+)$', tms.service, name="Tile Map Service"),
	url(r'^shape-editor/tms/(?P<version>[0-9.]+)/' + r'(?P<shapefile_id>\d+)$', tms.tileMap, name="Tile Map"),
	url(r'^shape-editor/tms/(?P<version>[0-9.]+)/' + r'(?P<shapefile_id>\d+)/(?P<zoom>\d+)/' + r'(?P<x>\d+)/(?P<y>\d+)\.png$', tms.tile, name="Map Tile"),
	
]
