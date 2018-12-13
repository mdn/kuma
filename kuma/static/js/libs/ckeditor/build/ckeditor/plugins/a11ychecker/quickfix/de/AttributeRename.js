/*
 Copyright (c) 2014-2016, CKSource - Frederico Knabben. All rights reserved.
 For licensing, see LICENSE.md or http://ckeditor.com/license
*/
(function(){CKEDITOR.plugins.a11ychecker.quickFixes.get({langCode:"de",name:"QuickFix",callback:function(b){function a(a){b.call(this,a)}a.prototype=new b;a.prototype.constructor=a;a.prototype.attributeName="title";a.prototype.attributeTargetName="alt";a.prototype.display=function(a){var c=this.issue.element.getAttribute(this.attributeName)||"";a.setInputs({value:{type:"text",label:"Value",value:c}})};a.prototype.fix=function(a,c){var b=this.issue.element;b.setAttribute(this.attributeTargetName,a.value);
b.removeAttribute(this.attributeName);c&&c(this)};a.prototype.lang={};CKEDITOR.plugins.a11ychecker.quickFixes.add("de/AttributeRename",a)}})})();