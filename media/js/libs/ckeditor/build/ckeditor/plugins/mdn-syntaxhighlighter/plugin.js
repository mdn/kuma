﻿CKEDITOR.config.mdnSyntaxhighlighter_brushes=[{name:"Bash",brush:"bash"},{name:"C/C++",brush:"cpp"},{name:"CSS",brush:"css"},{name:"HTML",brush:"html"},{name:"Java",brush:"java"},{name:"JavaScript",brush:"js"},{name:"JSON",brush:"json"},{name:"PHP",brush:"php"},{name:"Python",brush:"python"},{name:"SQL",brush:"sql"},{name:"XML",brush:"xml"}];
CKEDITOR.plugins.add("mdn-syntaxhighlighter",{requires:"menubutton,mdn-format",icons:"mdn-syntaxhighlighter-moono",init:function(a){var b=this,g=a.config.mdnSyntaxhighlighter_brushes,h=gettext("Syntax Highlighter"),c={};c.none={label:gettext("No Highlight"),group:"mdn-syntaxhighlighter",order:0,onClick:function(){a.execCommand("mdn-syntaxhighlighter","none")}};g.forEach(function(d,b){c[d.brush]={label:d.name,brushId:d.brush,group:"mdn-syntaxhighlighter",order:b+1,onClick:function(){a.execCommand("mdn-syntaxhighlighter",
this.brushId)}}});a.addMenuGroup("mdn-syntaxhighlighter",1);a.addMenuItems(c);a.addCommand("mdn-syntaxhighlighter",{contextSensitive:!0,exec:function(a,b){var e=c[b],f=a.elementPath().contains("pre");if(e){if(!f&&(a.execCommand("mdn-format-pre"),f=a.elementPath().contains("pre"),!f))return;f.$.className="none"==b?"":"brush: "+b;this.refresh(a,a.elementPath())}},refresh:function(a,c){this.setState("none"!=b.getBrushId(c)?CKEDITOR.TRISTATE_ON:CKEDITOR.TRISTATE_OFF)}});a.ui.add("MdnSyntaxhighlighter",
CKEDITOR.UI_MENUBUTTON,{icon:"mdn-syntaxhighlighter-moono",label:h,toolbar:"blocks,200",command:"mdn-syntaxhighlighter",onMenu:function(){var d={},g=b.getBrushId(a.elementPath()),e;for(e in c)d[e]=g==e?CKEDITOR.TRISTATE_ON:CKEDITOR.TRISTATE_OFF;return d}})},getBrushId:function(a){var b=a.contains("pre");if(!b)return"none";a="none";if(b=b.$.className)b=b.match(/brush\:(.*?);?$/),null!=b&&(a=b[1].split(";"),a=a[0].replace(/^\s+|\s+$/g,""));return a}});