<?php include "./inc/template.php"; 
head(
  $title = 'Neil Gauldin | Mozilla Developer Network',
  $pageid = '', 
  $bodyclass = 'profile',
  $extra_headers = '
  <link rel="stylesheet" type="text/css" href="./media/css/demos.css">
  '
); ?>

<section id="content">
<div class="wrap">

  <section id="content-main" class="full">

    <section id="profile-head" class="vcard">
      <div class="main">
        <h1 class="page-title"><span class="nickname">neilhimself</span></h1>

        <ul class="info">
          <li class="title">Web Developer</li>
          <li class="loc">San Francisco, CA</li>
        </ul>
  
        <div class="bio">
          <p>I make websites.</p>
        </div>
      </div>
      
      <div class="extra">
        <figure class="avatar">
          <img src="./media/img/blank.gif" alt="" width="120" height="120" class="photo">
        </figure>
        
        <ul class="links">
          <li class="web"><a href="#" rel="me external" class="url">Website</a></li>
          <li class="github"><a href="#"rel="me external" class="url">GitHub</a></li>
          <li class="docs"><a href="#" rel="me">Docs user page</a></li>
        </ul>
      </div>

      <!-- Only shown for the user and admins -->
      <p class="edit"><a href="profile-edit.php" class="button">Edit Profile</a></p>
    </section>

    <section id="profile-demos" class="profile-section">
      <header class="gallery-head">
        <h2 class="count">No Demos</h2>
      </header>
      <p class="none">You haven't submitted any web technology demos. Build something awesome and <a class="button positive" href="demo-submit.php">Submit a Demo</a></p>
    </section>
    
    <section id="docs-activity" class="profile-section">
      <header>
        <h2>Recent Docs Activity</h2>
      </header>
      <p class="none">You haven't contributed to any MDN docs. <a href="docs-landing.php">Pitch in!</a></p>
    </section>

  </section><!-- /#content-main -->

<script type="text/javascript" src="./media/js/jquery.hoverIntent.minified.js"></script>
<script type="text/javascript">
// <![CDATA[
	$(".gallery").ready(function(){
		$(".gallery").addClass("js");

    $(".gallery .demo").hoverIntent({
      interval: 250,
      over: function() {
        var content = $(this).html(),
            demo = $(this), 
            offs = $(this).offset();
        $("#content").prepend('<div class="demo demohover"><div class="in">'+content+'<\/div><\/div>');
        $("div.demohover").css({ left: offs.left, top: offs.top }).fadeIn(200).mouseleave(function() {
          $(this).fadeOut(200, function(){ 
            $(this).remove(); 
          });
        });
      }, 
      out: function() { /* do nothing */ }
    });

	});
// ]]>
</script>

</div>
</section>
<?php foot(); ?>
