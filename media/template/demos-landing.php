<?php include "./inc/template.php"; 
head(
  $title = 'Demo Studio | Mozilla Developer Network',
  $pageid = 'demostudio', 
  $bodyclass = 'section-demos landing',
  $headerclass = 'compact',
  $extraheaders = '
  <link rel="stylesheet" type="text/css" href="./media/css/demos.css"/>
  '
); ?>

<section id="content">
<div class="wrap">

  <header id="demos-head">
    <h1>Mozilla Demo Studio</h1>
    <ul class="demo-buttons">
      <li class="learnmore"><a href="#" class="button">Learn More</a></li>
      <li class="submit"><a href="demo-submit.php" class="button">Submit a Demo</a></li>
    </ul>
    <p id="derby-cta">
      <a href="demo-derby.php"><span>Join the</span> <em>Dev Derby</em> &amp; Win Prizes <br/><strong>Learn More</strong></a>
    </p>
  </header>

  <section id="featured-demos">
    <header>
      <h2>Featured Demos</h2>
    </header>

    <ul class="nav-slide">
      <li class="nav-prev"><a href="#" class="prev" title="See the previous demo">Previous</a></li>
  		<li class="nav-next"><a href="#" class="next" title="See the next demo">Next</a></li>
    </ul>
  
    <div id="demo-main">
      <strong class="flag">Derby Winner</strong>
      <div class="preview">
        <a href="demo-detail.php">
          <img src="./media/img/fpo2.jpg" alt="" width="435" height="326">
        </a>
        <div class="demo-details">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;The Incredible Machine&rdquo; by Neil Gauldin">The Incredible Machine</a>  
          </h2>
          <p class="byline vcard">
            <a href="demo-gallery-author.php" class="url fn" title="See more demos by Neil Gauldin">
            <img class="photo avatar" alt="" src="./media/img/blank.gif" width="50" height="50">
            Neil Gauldin</a>
          </p>
          <p class="desc">Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
          <p class="launch"><a href="demo-wrapper.html" class="button" title="Launch &ldquo;The Incredible Machine&rdquo;">Launch</a></p>
        </div>
      </div>
    </div>
    
    <div id="demo-prev" class="side">
      <div class="preview">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Fantastic Voyage&rdquo; by Alejandra Divens">
            <img class="preview" src="./media/img/fpo1.jpg" alt="" width="261" height="195">
            <b>Fantastic Voyage</b>
          </a>
        </h2>
      </div>
    </div>
    
    <div id="demo-next" class="side">
      <div class="preview">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Return to the House of Mummies, Part Two&rdquo; by Stephanie Acuba">
            <img class="preview" src="./media/img/fpo3.jpg" alt="" width="261" height="195">
            <b>Return to the House of Mummies, Part Two</b>
          </a>
        </h2>
      </div>
    </div>
  </section>

  <section id="content-main" class="full" role="main">
  
    <div id="search-browse">
      <form class="demo-search" method="post" action="/path/to/handler">
        <p>
          <input type="search" id="search-demos" placeholder="Search" />
          <noscript><button type="submit">Search</button></noscript>
        </p>
      </form>
      
      <b>or</b>
      
      <div id="demo-tags">
        <a href="#tags-list" class="button">Browse by Technology</a>
        <ul id="tags-list" class="menu">
          <li><a href="demo-gallery.php">Audio</a></li>
          <li><a href="demo-gallery.php">Canvas</a></li>
          <li><a href="demo-gallery.php">CSS3</a></li>
          <li><a href="demo-gallery.php">Device</a></li>
          <li><a href="demo-gallery.php">Drag and Drop</a></li>
          <li><a href="demo-gallery.php">Files</a></li>
          <li><a href="demo-gallery.php">Fonts</a></li>
          <li><a href="demo-gallery.php">Forms</a></li>
          <li><a href="demo-gallery.php">Geolocation</a></li>
          <li><a href="demo-gallery.php">History</a></li>
          <li><a href="demo-gallery.php">HTML5</a></li>
          <li><a href="demo-gallery.php">IndexedDB</a></li>
          <li><a href="demo-gallery.php">JavaScript</a></li>
          <li><a href="demo-gallery.php">MathML</a></li>
          <li><a href="demo-gallery.php">Mobile</a></li>
          <li><a href="demo-gallery.php">Multi-touch</a></li>
          <li><a href="demo-gallery.php">Offline Storage</a></li>
          <li><a href="demo-gallery.php">SVG</a></li>
          <li><a href="demo-gallery.php">Video</a></li>
          <li><a href="demo-gallery.php">WebGL</a></li>
          <li><a href="demo-gallery.php">Websockets</a></li>
          <li><a href="demo-gallery.php">Web Workers</a></li>
          <li><a href="demo-gallery.php">XMLHttpRequest</a></li>
        </ul>
      </div> 
    </div>

    <div id="gallery-sort">
      <p class="count">11,024 Demos</p>
      <ul class="sort">
        <li><strong title="You are viewing the most recent demos">Recent</strong></li>
        <li><a href="#" title="Sort demos by popularity">Popular</a></li>
        <li><a href="#" title="Sort demos by current trend">Trending</a></li>
      </ul>
    </div>
    
<script type="text/javascript" src="./media/js/jquery.hoverIntent.minified.js"></script>
<script type="text/javascript">
// <![CDATA[
/* Demo detail boxes */
  $(document).ready(function(){
		$(".gallery").addClass("js");
    $(".gallery .demo").hoverIntent({
      interval: 250,
      over: function() {
        var demo    = $(this), 
            content = $(this).html(),
            offs    = $(this).offset();
        $("#content").prepend('<div class="demo demohover"><div class="in">'+content+'<\/div><\/div>');
        if (demo.parents("#featured-demos").length) {
          $("#content").find("div.demohover").addClass("featured");
        };
        $("div.demohover").css({ left: offs.left, top: offs.top }).fadeIn(200).mouseleave(function() {
          $(this).fadeOut(200, function(){ 
            $(this).remove(); 
          });
        });
      }, 
      out: function() { /* do nothing */ }
    });
  });
  
	
/* Browse by Tech menu */
	$("#demo-tags").addClass("js");
  $("#demo-tags .button").click(function() {
    $("#tags-list").slideToggle(150);
    return false;
  });

  $("#tags-list").hover(
    function() {
      $(this).show().removeAttr("aria-hidden");
    },
    function() {
      $(this).slideUp('fast');
      $("#demo-tags .button").blur();
    }
  );

  $(document).bind('click', function(e) {
    var $clicked = $(e.target);
    if (! $clicked.parents().hasClass("menu"))
      $("#tags-list").hide().attr("aria-hidden", "true");
  });
  
  $("a, input, textarea, button").bind('focus', function(e) {
    var $focused = $(e.target);
    if (! $focused.parents().hasClass("menu"))
      $("#tags-list").hide().attr("aria-hidden", "true");
  });


/* Featured demos */
  $("#featured-demos").addClass("js");
  $("#featured-demos").ready(function(){
    $("#demo-main .demo-details, #featured-demos .side .demo-title b").hide().attr("aria-hidden", "true");
    
    $("#demo-main .preview").hoverIntent({
      interval: 150,
      over: function(){
        $("#demo-main .demo-details").fadeIn().removeAttr("aria-hidden");
      },
      out: function(){
        $("#demo-main .demo-details").fadeOut("fast").attr("aria-hidden", "true");
      }
    });
    
    $("#featured-demos .side .preview").hoverIntent({
      interval: 250,
      over: function(){
        $(this).find("img").animate({ opacity: "1" }, 150);
        $(this).find(".demo-title b").fadeIn(150).removeAttr("aria-hidden");
      },
      out: function(){
        $(this).find("img").animate({ opacity: ".6" }, 250);
        $(this).find(".demo-title b").fadeOut(250).attr("aria-hidden", "true");
      }
    });
  
  });

// ]]>
</script>

<!-- NOTES:
     First item in each row needs the class "row-first". It's a strictly presentational class that only serves to 
     clear the floats of the row above, but it's necessary to preserve the layout.
-->
    <ul class="gallery">
      <li class="demo featured row-first">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;The Incredible Machine&rdquo; by Neil Gauldin">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> The Incredible Machine
          </a>
          <strong class="flag">Featured</strong>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Neil Gauldin">Neil Gauldin</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 20,000 times">20,000</li>
            <li class="likes" title="3,000 people liked this demo">3,000</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 100 comments for this demo">100</a></li>
          </ul>
          <p class="desc">Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;The Incredible Machine&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Fantastic Voyage&rdquo; by Alejandra Divens">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Fantastic Voyage
          </a>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Alejandra Divens">Alejandra Divens</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 1,234 times">1,234</li>
            <li class="likes" title="151 people liked this demo">151</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 3 comments for this demo">3</a></li>
          </ul>
          <p class="desc">Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum ipsum dolor sit amet consecutor minum elit.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Fantastic Voyage&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;It's a Mad Mad Mad Mad Mad Mad World&rdquo; by Darryl McConnaughy">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> It&#8217;s a Mad Mad Mad Mad Mad Mad World
          </a>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Darryl McConnaughy">Darryl McConnaughy</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo hasn't been viewed by anyone yet">0</li>
            <li class="likes" title="Nobody has liked this demo yet">0</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are no comments yet for this demo">0</a></li>
          </ul>
          <p class="desc">Morbi in sem quis dui placerat ornare.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;It's a Mad Mad Mad Mad Mad Mad World&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Twenty Years to Midnight&rdquo; by Thaddeus Venture">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Twenty Years to Midnight
          </a>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Thaddeus Venture">Thaddeus Venture</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 1,234 times">1,234</li>
            <li class="likes" title="151 people liked this demo">151</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 3 comments for this demo">3</a></li>
          </ul>
          <p class="desc">Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Twenty Years to Midnight&rdquo;">Launch</a></p>
        </div>
      </li>

      <li class="demo featured row-first">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Bloodeye&rdquo; by Jefferson Twilight">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Bloodeye
          </a>
        </h2>
        <p class="byline vcard"><a href="#" class="url fn" title="See Jefferson Twilight's profile">Jefferson Twilight</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 55 times">55</li>
            <li class="likes" title="7 people liked this demo">7</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are no comments yet for this demo">0</a></li>
          </ul>
          <p class="desc">Pellentesque fermentum dolor. Aliquam quam lectus, facilisis auctor, ultrices ut, elementum vulputate, nunc.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Bloodeye&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;&rdquo; by Amanda Parth">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Modern Alchemy
          </a>
          <strong class="flag">Featured</strong>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Amanda Parth">Amanda Parth</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 355 times">355</li>
            <li class="likes" title="27 people liked this demo">27</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 11 comments for this demo">11</a></li>
          </ul>
          <p class="desc">Pellentesque fermentum dolor. Aliquam quam lectus, facilisis auctor, ultrices ut, elementum vulputate, nunc.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Bloodeye&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Careers in Science&rdquo; by Stephanie Acuba">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Return to the House of Mummies, Part Two
          </a>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Stephanie Acuba">Stephanie Acuba</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 1,234 times">1,234</li>
            <li class="likes" title="151 people liked this demo">151</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 3 comments for this demo">3</a></li>
          </ul>
          <p class="desc">Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Careers in Science&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;A Tangled Skein&rdquo; by Byron Orpheus">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> A Tangled Skein
          </a>
          <strong class="flag">Featured</strong>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Byron Orpheus">Byron Orpheus</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 1,234 times">1,234</li>
            <li class="likes" title="151 people liked this demo">151</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 3 comments for this demo">3</a></li>
          </ul>
          <p class="desc">Sed adipiscing ornare risus. Morbi est est, blandit sit amet, sagittis vel, euismod vel, velit.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;The Incredible Machine&rdquo;">Launch</a></p>
        </div>
      </li>

      <li class="demo row-first">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Pork Feathers&rdquo; by Benjamin Jonathan Jonah Jameson-Parker III, Esq.">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Pork Feathers
          </a>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Benjamin Jonathan Jonah Jameson-Parker III, Esq.">Benjamin Jonathan Jonah Jameson-Parker III, Esq.</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 21,092 times">21,092</li>
            <li class="likes" title="703 people liked this demo">703</li>
            <li class="comments" title="There are 19 comments for this demo">19</li>
          </ul>
          <p class="desc">Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;The Incredible Machine&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Big Time&rdquo; by Felicia Hardy">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Big Time
          </a>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Felicia Hardy">Felicia Hardy</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 95 times">95</li>
            <li class="likes" title="4 people liked this demo">4</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 3 comments for this demo">3</a></li>
          </ul>
          <p class="desc">Pellentesque egestas sem. Suspendisse commodo ullamcorper magna.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Big Time&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Nova Prime&rdquo; by Richard Rider">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Nova Prime
          </a>
          <strong class="flag">Featured</strong>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Richard Rider">Richard Rider</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 202 times">202</li>
            <li class="likes" title="19 people liked this demo">19</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 7 comments for this demo">7</a></li>
          </ul>
          <p class="desc">Pellentesque egestas sem. Suspendisse commodo ullamcorper magna.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Nova Prime&rdquo;">Launch</a></p>
        </div>
      </li>
      <li class="demo">
        <h2 class="demo-title">
          <a href="demo-detail.php" title="See more about &ldquo;Last Chance for a Slow Dance&rdquo; by Will Forsmythe">
            <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Last Chance for a Slow Dance
          </a>
        </h2>
        <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Will Forsmythe">Will Forsmythe</a></p>
        <div class="extra">
          <ul class="stats">
            <li class="views" title="This demo has been viewed 202 times">202</li>
            <li class="likes" title="19 people liked this demo">19</li>
            <li class="comments"><a href="demo-detail.php#comments" title="There are 7 comments for this demo">7</a></li>
          </ul>
          <p class="desc">Pellentesque egestas sem. Suspendisse commodo ullamcorper magna.</p>
          <p class="launch"><a href="#" class="button" title="Launch &ldquo;Last Chance for a Slow Dance&rdquo;">Launch</a></p>
        </div>
      </li>
    </ul>
    
    <div id="gallery-foot">
      <p class="showing">1&ndash;9 of 11,024</p>
      <ul class="paging">
        <li class="next"><a href="#" title="Go to the next page">Next</a></li>
        <li class="last"><a href="#" title="Go to the last page">Last</a></li>
      </ul>
      <p class="feed"><a href="#" rel="alternate" title="Subscribe to a feed of all demos">RSS</a></p>
    </div>

  </section><!-- /#content-main -->

</div>
</section>
<?php foot(); ?>
