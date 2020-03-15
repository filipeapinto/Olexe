/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


dojo.require("dojox.widget.FisheyeList");
dojo.require("dojo.parser");
dojo.addOnLoad(
   function()
     {
		 dojo.parser.parse();
	 }
);
function load_app(id)
     {
		 alert("icon "+id+" was clicked");
     };