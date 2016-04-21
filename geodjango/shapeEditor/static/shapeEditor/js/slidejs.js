// JavaScript Document

var Image1=document.getElementById("habitat_maps1");
var Image2=document.getElementById("habitat_maps2");
var Image3=document.getElementById("habitat_maps3");
var Image4=document.getElementById("habitat_maps4");

var imageArray=[Image1,image2,image3,image4];
var imageIndex=0;

function changeImage(){
	Image1.setAttribute("src", imageArray[imageIndex]);
	imageIndex++;
	if (imageIndex>=imageArray.length) {
		imageIndex=0;
	}
}

var intervalHandle = setInterval(changeImage,2000);

habitat_maps.onclick=function(){
	clearInterval(intervalHandle);
}