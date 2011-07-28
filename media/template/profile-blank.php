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
        <!-- Only shown for the user and admins -->
        <p class="edit"><a href="profile-edit-blank.php" class="button">Edit Profile</a></p>
      </div>
      <div class="extra">
        <figure class="avatar">
          <img src="./media/img/blank.gif" alt="" width="120" height="120" class="photo">
        </figure>
        <ul class="links">
          <li class="docs"><a href="#" rel="me">Docs user page</a></li>
        </ul>
      </div>
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
