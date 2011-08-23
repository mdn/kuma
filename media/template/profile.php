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
        <h1 class="page-title"><span class="nickname">neilhimself</span> <b>(<span class="fn">Neil Gauldin</span>)</b></h1>
  
        <ul class="info">
          <li class="title">Web Developer</li>
          <li class="org">The Collective Group</li>
          <li class="loc">San Francisco, CA</li>
        </ul>
  
        <div class="bio">
          <p>The details of my life are quite inconsequential... very well, where do I begin? My father was a relentlessly self-improving boulangerie owner from Belgium with low grade narcolepsy and a penchant for buggery. My mother was a fifteen year old French prostitute named Chloe with webbed feet. My father would womanize, he would drink. He would make outrageous claims like he invented the question mark. Sometimes he would accuse chestnuts of being lazy. The sort of general malaise that only the genius possess and the insane lament.</p>
          <p>My childhood was typical. Summers in Rangoon, luge lessons. In the spring we'd make meat helmets. When I was insolent I was placed in a burlap bag and beaten with reeds- pretty standard really.</p>
        </div>
        
        <div class="tags">
          <h2>Interests</h2>
        	<ul class="int-taglist taglist">
            <li>CSS</li>
            <li>CSS3</li>
            <li>JavaScript</li>
            <li>web standards</li>
            <li>monster movies</li>
            <li>bacon</li>
            <li>HTML</li>
            <li>HTML5</li>
            <li>open source</li>
            <li>PHP</li>
            <li>BBQ</li>
            <li>SOL</li>
            <li>Cambot</li>
            <li>Gypsy</li>
            <li>Tom Servo</li>
            <li>Crooooooooow</li>
          </ul>
        </div>
        
        <div class="tags">
          <h2>Areas of Expertise</h2>
          <ul class="exp-taglist taglist">
            <li>CSS</li>
            <li>HTML</li>
            <li>JavaScript</li>
          </ul>
        </div>
      </div>
      
      <div class="extra">
        <figure class="avatar">
          <img src="./media/img/blank.gif" alt="" width="120" height="120" class="photo">
        </figure>
        
        <ul class="links">
          <li class="web"><a href="#" rel="me external" class="url">Website</a></li>
          <li class="twitter"><a href="#"rel="me external" class="url">@neilhimself</a></li>
          <li class="github"><a href="#"rel="me external" class="url">GitHub</a></li>
          <li class="stackoverflow"><a href="#"rel="me external" class="url">StackOverflow</a></li>
          <li class="linkedin"><a href="#"rel="me external" class="url">LinkedIn</a></li>
          <li class="docs"><a href="#" rel="me">Docs user page</a></li>
        </ul>
      </div>

      <!-- Only shown for the user and admins -->
      <p class="edit"><a href="profile-edit.php" class="button">Edit Profile</a></p>
    </section>

    <section id="profile-demos" class="profile-section">
      <header class="gallery-head">
        <h2 class="count">7 Demos <a class="button positive" href="demo-submit.php">Submit a Demo</a></h2>
        <ul class="sort">
          <li><strong title="You are viewing these demos sorted by most views">Most Viewed</strong></li>
          <li><a href="#" title="Sort demos by most likes">Most Liked</a></li>
          <li><a href="#" title="Sort demos by most recently submitted">Most Recent</a></li>
        </ul>
      </header>
  
  <!-- NOTES:
       First item in each row needs the class "row-first". It's a strictly presentational class that only serves to 
       clear the floats of the row above, but it's necessary to preserve the layout.
  -->
      <ul class="gallery">
        <li class="demo row-first">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;The Incredible Machine&rdquo; by Neil Gauldin">
              <img src="./media/img/fpo55.png" alt="" width="200" height="150"> The Incredible Machine
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
            <a href="demo-detail.php" title="See more about &ldquo;Fantastic Voyage&rdquo; by Neil Gauldin">
              <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Fantastic Voyage
            </a>
            <strong class="flag">Featured</strong>
          </h2>
          <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Neil Gauldin">Neil Gauldin</a></p>
          <div class="extra">
            <ul class="stats">
              <li class="views" title="This demo has been viewed 1,234 times">1,234</li>
              <li class="likes" title="151 people liked this demo">151</li>
              <li class="comments"><a href="demo-detail.php#comments" title="There are 3 comments for this demo">3</a></li>
            </ul>
            <p class="desc">Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
            <p class="launch"><a href="#" class="button" title="Launch &ldquo;Fantastic Voyage&rdquo;">Launch</a></p>
          </div>
        </li>
        <li class="demo">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;It's a Mad Mad Mad Mad Mad Mad World&rdquo; by Neil Gauldin">
              <img src="./media/img/fpo55.png" alt="" width="200" height="150"> It&#8217;s a Mad Mad Mad Mad Mad Mad World
            </a>
          </h2>
          <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Neil Gauldin">Neil Gauldin</a></p>
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
        <li class="demo featured">
          <h2 class="demo-title">
            <a href="demo-detail.php" title="See more about &ldquo;Twenty Years to Midnight&rdquo; by Neil Gauldin">
              <img src="./media/img/fpo55.png" alt="" width="200" height="150"> Twenty Years to Midnight
            </a>
            <strong class="flag">Featured</strong>
          </h2>
          <p class="byline vcard"><a href="demo-gallery-author.php" class="url fn" title="See more demos by Neil Gauldin">Neil Gauldin</a></p>
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
      </ul>
      
      <div class="gallery-foot">
        <p class="showing">1&ndash;4 of 7</p>
        <ul class="paging">
          <!-- No first or prev when we're on the first page, no next or last when we're on the last page -->
          <li class="next"><a href="#" title="Go to the next page">Next</a></li>
          <li class="last"><a href="#" title="Go to the last page">Last</a></li>
        </ul>
        <p class="feed"><a href="#" rel="alternate" title="Subscribe to a feed of Neil Gauldin's demos">RSS</a></p>
      </div>
    </section>
    
    <section id="docs-activity" class="profile-section">
      <header>
        <h2>Recent Docs Activity</h2>
        <p class="more"><a href="https://developer.mozilla.org/Special:Contributions?target=Sheppy">See more history</a></p>
      </header>
      
      <table class="activity">
        <thead>
          <th scope="col" class="page">Page</th>
          <th scope="col" class="date">Date</th>
          <th scope="col" class="summary">Edit summary</th>
        </thead>
        <tbody>
          <tr>
            <th scope="row">
              <h3><a href="http://developer.mozilla.org/en/DOM/FileReader">en/DOM/element.removeEventListener</a></h3>
              <ul class="actions">
                <li><a href="#">Edit page</a></li>
                <li><a href="#">View complete diff</a></li>
                <li><a href="#">View page history</a></li>
              </ul>
            </th>
            <td>July 19, 2011 <br>6:36 AM</td>
            <td>1 words added, 53 words removed</td>
          </tr>
          <tr>
            <th scope="row">
              <h3><a href="http://developer.mozilla.org/en/DOM/document.doctype">en/DOM/document.doctype</a></h3>
              <ul class="actions">
                <li><a href="#">Edit page</a></li>
                <li><a href="#">View complete diff</a></li>
                <li><a href="#">View page history</a></li>
              </ul>
            </th>
            <td>July 16, 2011 <br>11:33 AM</td>
            <td>Removed tags: !DOCTYPE, DOCTYPE, DTD, ECMAScript, PUBLIC, SYSTEM, TEASER, W3C, create</td>
          </tr>
          <tr>
            <th scope="row">
              <h3><a href="http://developer.mozilla.org/en/DOM/document">en/DOM/document</a></h3>
              <ul class="actions">
                <li><a href="#">Edit page</a></li>
                <li><a href="#">View complete diff</a></li>
                <li><a href="#">View page history</a></li>
              </ul>
            </th>
            <td>July 15, 2011 <br>5:47 PM</td>
            <td>5 words added</td>
          </tr>
          <tr>
            <th scope="row">
              <h3><a href="http://developer.mozilla.org/en/DOM/TouchEvent">en/DOM/TouchEvent</a></h3>
              <ul class="actions">
                <li><a href="#">Edit page</a></li>
                <li><a href="#">View complete diff</a></li>
                <li><a href="#">View page history</a></li>
              </ul>
            </th>
            <td>July 15, 2011 <br>1:43 PM</td>
            <td>28 words added</td>
          </tr>
          <tr>
            <th scope="row">
              <h3><a href="https://developer.mozilla.org/en/Firefox_6_for_developers">en/Firefox 6 for developers</a></h3>
              <ul class="actions">
                <li><a href="#">Edit page</a></li>
                <li><a href="#">View complete diff</a></li>
                <li><a href="#">View page history</a></li>
              </ul>
            </th>
            <td>July 14, 2011 <Br>11:17 AM</td>
            <td>clean up a tad; 11 words added, 28 words removed</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="3">
              <a href="https://developer.mozilla.org/index.php?title=Special:Contributions&feed=rss&target=Sheppy" rel="alternate" class="feed">RSS</a>
            </td>
          </tr>
        </tfoot>
      </table>
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
