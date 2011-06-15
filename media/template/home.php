<?php include "./inc/template.php"; 
head(
  $title = 'Mozilla Developer Network',
  $pageid = 'home', 
  $bodyclass = '',
  
  $extra_headers = '
  <link rel="stylesheet" type="text/css" href="./media/css/demos.css"/>
  '
); ?>
<header id="welcome-bar">
<div class="wrap">

  <h1>It's the Web. <b>You drive.</b></h1>
  <h2>Welcome to the Mozilla Developer Network.</h2>
  <p>We are an open community of developers building resources for a better web, 
  regardless of brand, browser or platform. Anyone can contribute and each person 
  who does makes us stronger. Together we can continue to drive innovation on the 
  Web to serve the greater good. It starts here, with you.</p>
  
  <button type="button" id="welcome-close">Close</button>

  <script type="text/javascript">
  // <![CDATA[
  	$("#welcome-bar").ready(function(){
  		$("#welcome-close").click(function(){
  		  $("#welcome-bar").slideUp("fast");
  		});
  	});
  // ]]>
  </script>

</div>
</header>

<section id="content">
<div class="wrap">

  <section id="content-main" role="main" class="full">
    
    <section id="top-docs">
      <h1>Browse Thousands of Docs for <b>Web Developers</b></h1>
      <ul>
        <li>
          <ul>
            <li><a href="https://developer.mozilla.org/en/HTML">HTML</a></li>
            <li><a href="https://developer.mozilla.org/en/HTML/HTML5">HTML5</a></li>
            <li><a href="https://developer.mozilla.org/en/CSS">CSS</a></li>
            <li><a href="https://developer.mozilla.org/en/JavaScript">JavaScript</a></li>
            <li><a href="https://developer.mozilla.org/en/DOM">DOM</a></li>
          </ul>
        </li>
        <li>
          <ul> 
            <li><a href="https://developer.mozilla.org/en/HTML/Canvas">Canvas</a></li>
            <li><a href="https://developer.mozilla.org/en/SVG">SVG</a></li>
            <li><a href="https://developer.mozilla.org/en/WebGL">WebGL</a></li>
            <li><a href="https://developer.mozilla.org/en/Using_audio_and_video_in_Firefox">Video</a></li>
            <li><a href="https://developer.mozilla.org/en/Using_audio_and_video_in_Firefox">Audio</a></li>
          </ul>
        </li>
        <li>
          <ul>
            <li><a href="https://developer.mozilla.org/en/Using_gradients">Gradients</a></li>
            <li><a href="https://developer.mozilla.org/en/CSS/Using_CSS_transforms">Transforms</a></li>
            <li><a href="https://developer.mozilla.org/en/CSS/CSS_transitions">Transitions</a></li>
            <li><a href="https://developer.mozilla.org/en/CSS/CSS_animations">Animations</a></li>
            <li><a href="https://developer.mozilla.org/en/CSS/Media_queries">Media Queries</a></li>
          </ul>
        </li>
        <li>
          <ul>
            <li><a href="https://developer.mozilla.org/en/Ajax">AJAX</a></li>
            <li><a href="https://developer.mozilla.org/en/WebSockets">WebSockets</a></li>
            <li><a href="https://developer.mozilla.org/en/Offline_resources_in_Firefox">Offline Cache</a></li>
            <li><a href="https://developer.mozilla.org/en/DOM/Storage">Local Storage</a></li>
            <li><a href="https://developer.mozilla.org/en/IndexedDB">IndexedDB</a></li>
          </ul>
        </li>
        <li>
          <ul>
            <li><a href="https://developer.mozilla.org/en/Using_geolocation">Geolocation</a></li>
            <li><a href="https://developer.mozilla.org/en/DragDrop/Drag_and_Drop">Drag &amp; Drop</a></li>
            <li><a href="https://developer.mozilla.org/en/Using_files_from_web_applications">File API</a></li>
            <li><a href="https://developer.mozilla.org/en/Using_web_workers">Web Workers</a></li>
            <li>and more&hellip;</li>
          </ul>
        </li>
      </ul>
      <p class="more">And even more resources for: 
        <a href="section-mobile.php">Mobile Web Apps</a> &middot; 
        <a href="section-addons.php">Firefox Add-ons</a> &middot; 
        <a href="section-apps.php">Mozilla Applications</a>
      </p>
    </section><!-- /#top-docs -->
    
    <section id="home-promos">
    
      <div class="promo" id="promo-learn">
        <a href="learn-landing.php">
          <h2>Learn</h2>
          <p>Our collection of resources shows you how to use the technologies that power the Web.</p>
        </a>
        <div></div>
      </div>
      
      <div class="promo" id="promo-demos">
        <a href="demos-landing.php">
          <h2>Demos</h2>
          <p>Check out what developers are doing with the latest Web standards and open technologies.</p>
        </a>
        <div></div>
      </div>
      
      <div class="promo" id="promo-foxdev">
        <a href="#">
          <h2>Firefox for Devs</h2>
          <p>See what's new for Web developers in the latest version of Firefox.</p>
        </a>
        <div></div>
      </div>
    
      <div class="promo" id="promo-aurora">
        <a href="#">
          <h2>Aurora</h2>
          <p>Experience the very latest features before they go to beta by trying out the new Aurora builds.</p>
        </a>
        <div></div>
      </div>
    
    </section><!-- /#home-promos -->
    
    <section id="home-news">
      <h1>Latest News &amp; Updates</h1>
      
      <ul class="hfeed">
        <li class="hentry">
          <h2 class="entry-title"><a href="#" rel="bookmark">Integer vitae libero ac risus egestas placerat</a></h2>
          <p class="entry-summary">Sed adipiscing ornare risus. Morbi est est, blandit sit amet, sagittis vel, euismod vel, velit. Pellentesque egestas sem. Suspendisse commodo ullamcorper magna.</p>
          <p class="entry-meta vcard">Posted <time class="published" datetime="<?php echo date('Y-m-d'); ?>" title="<?php echo date('Y-m-d'); ?>">June 13, 2011</time> by <cite class="author fn">Chris Heilmann</cite> under <a href="#" rel="tag">CSS3</a>, <a href="#" rel="tag">HTML5</a></p>
        </li>
        <li class="hentry">
          <h2 class="entry-title"><a href="#" rel="bookmark">Lorem ipsum dolor sit amet</a></h2>
          <p class="entry-summary">Ante et vulputate volutpat, eros pede semper est, vitae luctus metus libero eu augue. Morbi purus libero, faucibus adipiscing, commodo quis, gravida id, est. Aenean dignissim pellentesque felis.</p>
          <p class="entry-meta vcard">Posted <time class="published" datetime="<?php echo date('Y-m-d'); ?>" title="<?php echo date('Y-m-d'); ?>">June 10, 2011</time> by <cite class="author fn">Jay Patel</cite> under <a href="#" rel="tag">Firefox</a>, <a href="#" rel="tag">Thunderbird</a>, <a href="#" rel="tag">Seamonkey</a></p>
        </li>
        <li class="hentry">
          <h2 class="entry-title"><a href="#" rel="bookmark">Aliquam quam lectus, facilisis auctor, ultrices ut, elementum vulputate, nunc</a></h2>
          <p class="entry-summary">Consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore tincidunt.</p>
          <p class="entry-meta vcard">Posted <time class="published" datetime="<?php echo date('Y-m-d'); ?>" title="<?php echo date('Y-m-d'); ?>">May 23, 2011</time> by <cite class="author fn">Brian Dils</cite> under <a href="#" rel="tag">Web</a>, <a href="#" rel="tag">Mobile</a></p>
        </li>
        <li class="hentry">
          <h2 class="entry-title"><a href="#" rel="bookmark">Fusce pellentesque suscipit nibh</a></h2>
          <p class="entry-summary">Morbi in sem quis dui placerat ornare. Pellentesque odio nisi, euismod in, pharetra a, ultricies in, diam. Sed arcu. Cras consequat. Praesent dapibus, neque id cursus faucibus, tortor neque egestas augue, eu vulputate magna eros eu erat. Aliquam erat volutpat. Nam dui mi, tincidunt quis, accumsan porttitor, facilisis luctus, metus.</p>
          <p class="entry-meta vcard">Posted <time class="published" datetime="<?php echo date('Y-m-d'); ?>" title="<?php echo date('Y-m-d'); ?>">May 14, 2011</time> by <cite class="author fn">Janet Swisher</cite> under <a href="#" rel="tag">Mobile</a></p>
        </li>
      </ul>
    </section><!-- /#home-news -->
    
    <section id="home-demos">
      <h1>Awesome Demos</h1>
      <p class="more"><a href="demos-landing.php">More Demos&hellip;</a></p>
      
      <ul class="gallery">
        <li class="demo row-first">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;The Incredible Machine&rdquo; by Neil Gauldin">
              <img src="./media/img/fpo55.png" alt="" width="180" height="133"> The Incredible Machine
            </a>
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
        <li class="demo featured">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;Fantastic Voyage&rdquo; by Alejandra Divens">
              <img src="./media/img/fpo55.png" alt="" width="180" height="133"> Fantastic Voyage
            </a>
            <strong class="flag">Featured</strong>
          </h2>
          <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Alejandra Divens">Alejandra Divens</a></p>
          <div class="extra">
            <ul class="stats">
              <li class="views" title="This demo has been viewed 1,234 times">1,234</li>
              <li class="likes" title="151 people liked this demo">151</li>
              <li class="comments"><a href="demo-detail.php#comments" title="There are 100 comments for this demo">3</a></li>
            </ul>
            <p class="desc">Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
            <p class="launch"><a href="#" class="button" title="Launch &ldquo;Fantastic Voyage&rdquo;">Launch</a></p>
          </div>
        </li>

        <li class="demo row-first">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;It's a Mad Mad Mad Mad Mad Mad World&rdquo; by Darryl McConnaughy">
              <img src="./media/img/fpo55.png" alt="" width="180" height="133"> It&#8217;s a Mad Mad Mad Mad Mad Mad World
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
              <img src="./media/img/fpo55.png" alt="" width="180" height="133"> Twenty Years to Midnight
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

        <li class="demo row-first">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;Bloodeye&rdquo; by Jefferson Twilight">
              <img src="./media/img/fpo55.png" alt="" width="180" height="133"> Bloodeye
            </a>
          </h2>
          <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Jefferson Twilight">Jefferson Twilight</a></p>
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
        <li class="demo-submit">          
          <p><a href="demo-submit.php">Have an awesome demo of your own? <strong>Submit It</strong></a></p>
        </li>
      </ul>
    </section><!-- /#home-demos -->
    
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

    
  </section>

</div>
</section><!-- /#content -->

<?php foot(); ?>
