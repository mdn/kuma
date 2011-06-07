<?php include "./inc/template.php"; 
head(
  $title = 'New Article | MDN Docs',
  $pageid = '', 
  $bodyclass = 'section-docs',
  $headerclass = 'compact',
  $extra_headers = '
  <!--[if !IE 6]><!--><link rel="stylesheet" type="text/css" media="screen,projection" href="./css/wiki-screen.css"><!--<![endif]-->
  <link rel="stylesheet" type="text/css" media="print" href="./css/wiki-print.css">
  <script src="./js/ckeditor/ckeditor.js"></script>
  <script src="./js/ckeditor/adapters/jquery.js"></script>
  '
); ?>

<section id="nav-toolbar">
<div class="wrap">
  <nav class="crumbs" role="navigation">
    <ol>
      <li class="crumb-one"><a href="/">MDN</a></li>
      <li class="crumb-two"><a href="/docs">Docs</a></li>
      <li><a href="wiki-article.php">Parent Article Title</a></li>
    </ol>
  </nav>
</div>
</section>
  
<section id="content">
<div class="wrap">

  <section id="content-main" class="full" role="main">
    <article class="article" role="main">
    
    <form id="wiki-page-edit" class="editing" method="post" action="path/to/handler">
      <fieldset>
      <header id="article-head">
        <div class="title">
          <input type="text" id="article-title" placeholder="Name Your Article">
          <button type="button" id="btn-properties" title="Edit Page Title and Properties">Edit Page Title and Properties</button>
        </div>
      
        <ul id="page-buttons">
          <li><button type="submit" id="btn-save" class="btn-save" onclick="window.location.href='wiki-article.php';return false;">Save Changes</button></li>
          <li><button type="button" id="btn-preview" class="btn-preview" onclick="window.location.href='wiki-preview.php';">Preview Changes</button></li>
          <li><button type="reset" id="btn-discard" class="btn-discard" onclick="window.location.href='wiki-article.php';">Discard Changes</button></li>
        </ul>

      </header>

      <textarea id="wikiArticle">
<p>Add your content here.</p>
      </textarea>
      
    </fieldset>
    </form>
    
    </article>

<script>
$("#wikiArticle").ckeditor(function() {
  // Callback functions after CKE is ready

    var $head      = $("#article-head");
    var $tools     = $(".cke_toolbox");
    var contentTop = $("#content").offset();
  	var headHeight = $head.height();
  	var toolHeight = $tools.height();
    var fixed = false;
  
    // Switch header and toolbar styles on scroll to keep them on screen
    $(document).scroll(function() {
    	if( $(this).scrollTop() >= contentTop.top ) {
    	  if( !fixed ) {
    	    fixed = true;
    	    $head.css({position:'fixed', top:20, width:"96%"});
    	    $tools.css({position:'fixed', top:headHeight+29, width:$("#cke_wikiArticle").width()-10});
        	$("td.cke_top").css({ height: toolHeight+29 });
        	$("#cke_wikiArticle").css({ marginTop: headHeight });
    	  }
    	} else {
    	  if( fixed ) {
    	    fixed = false;
    	    $head.css({position:'relative', top:"auto", width:"auto"});
    	    $tools.css({position:'relative', top:"auto", width:"auto"});
        	$("td.cke_top").css({ height: "auto" });
        	$("#cke_wikiArticle").css({ marginTop: 0 });
    	  }
    	}
    });
    
    $(window).resize(function() { // Recalculate box width on resize
      if ( fixed ) {
        $tools.css({width:$("#cke_wikiArticle").width()-10}); // Readjust toolbox to fit
      }
    });
	
  }, { 
  // Set up CKE
  skin : 'kuma', // Our custom skin
  extraPlugins : 'autogrow', // Expand the editor around the page content
  startupFocus : true // But the cursor in the editor
});

</script>

  </section><!-- /#content-main -->

</div>
</section>
<?php foot(); ?>
