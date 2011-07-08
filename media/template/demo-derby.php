<?php include "./inc/template.php"; 
head(
  $title = 'Dev Derby | Mozilla Developer Network',
  $pageid = 'devderby-home', 
  $bodyclass = 'section-demos devderby',
  $extra_headers = '
  <link rel="stylesheet" type="text/css" href="./media/css/devderby.css"/>
  <link rel="stylesheet" type="text/css" href="./media/css/demos.css"/>
  '
); ?>


<section id="content">
<div class="wrap">

  <header id="page-head">
    <nav id="nav-derby">
      <ul>
        <li><em>Home</em></li>
        <li><a href="#upcoming">Challenges</a></li>
        <li><a href="demo-derby-rules.php">Rules</a></li>
        <li><a href="#tab-judging" rel="tab">Judging</a></li>
        <li><a href="#challenge-prizes">Prizes</a></li>
        <li><a href="#resources">Resources</a></li>
      </ul>
    </nav>
  </header>

  <section id="content-main" class="full" role="main">
    <header id="derby-head">
      <p class="presents"><a href="demos-landing.php">Mozilla Demo Studio</a> presents:</p>
      <h1>Dev Derby</h1>
      <h2>Show us what you can do with CSS animations</h2>
      <p class="info">Join the Dev Derby now and submit your demo to win an Android phone or other prizes.</p>
      <p class="submit"><a href="demo-submit.php"><b>Submit</b> Your Demo</a></p>
    </header>

  <div class="main">
    <section id="upcoming">
      <header>
        <h1>Upcoming Challenges for 2011</h1>
      </header>
      <ol>
        <li class="first">
          <h2 class="title">CSS3 Animations</h2>
          <h3 class="date">June</h3>
          <h4 class="tagline">Make the Web move</h4>
          <h5 class="current"><span><b>Current</b> Derby</span></h5>
          <p class="desc">CSS3 Animations let you change property values over time, to animate the appearance or position of elements, with no or minimal JavaScript, and with greater control than transitions.</p>
        </li>
        <li class="second">
          <h2 class="title">HTML5 &lt;video&gt;</h2>
          <h3 class="date">July</h3>
          <h4 class="tagline">Lights, camera, action!</h4>
          <p class="desc">The HTML5 &lt;video&gt; element lets you embed and control video media directly in web pages, without resorting to plug-ins.</p>
        </li>
        <li class="third">
          <h2 class="title">Touch</h2>
          <h3 class="date">August</h3>
          <h4 class="tagline">Touch and go</h4>
          <p class="desc">Touch events let you track the movements of a user's fingers on a touch screen.</p>
        </li>
      </ol>
    </section>
    
    <section id="current-challenge">
      <ul class="tabs">
        <li class="current"><a href="#tab-challenge">Current</a></li>
        <li><a href="#tab-submissions">Submissions</a></li>
        <li><a href="#tab-rules">Rules</a></li>
        <li><a href="#tab-judging">Judging</a></li>
        <li><a href="#tab-previous">Previous</a></li>
      </ul>
      
      <section id="tab-challenge" class="block">
        <header>
          <h1 class="title">CSS3 Animations</h1>
          <h2 class="date">June</h2>
        </header>
        <p class="tagline">Show us what CSS can really do! Make the Web move with CSS3 Animations.</p>
        <p>CSS3 Animations are a new feature of modern browsers like Firefox, which add even more flexibility and control to the style and experience of the Web.  CSS3 Animations let you change property values over time with no or minimal JavaScript, and with greater control than CSS Transitions. Go beyond static properties to animate the appearance and positions of HTML elements. You can achieve these effects without Flash or Silverlight, to make creative dynamic interfaces and engaging animations with CSS3.</p>
        <p><a href="demo-submit.php">Submit your CSS3 Animations demo</a> for the June Dev Derby today!</p>
      </section>
    
      <section id="tab-submissions" class="block">
      <!-- If no submissions...
        <p class="none">Developers must be busy tinkering with their demos. No submissions yet. Be the first!</p>
        <p class="demo-submit"><a href="demo-submit.php" class="button">Submit Your Demo</a></p>
      -->
      
    <!-- NOTES:
         First item in each row needs the class "row-first". It's a strictly presentational class that only serves to 
         clear the floats of the row above, but it's necessary to preserve the layout.
    -->
        <ul class="gallery">
          <li class="demo row-first">
            <h2 class="demo-title">
              <a href="demo-detail.php" title="See more about &ldquo;The Incredible Machine&rdquo; by Neil Gauldin">
                <img src="./media/img/fpo55.png" alt="" width="180" height="135"> The Incredible Machine
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
          <li class="demo">
            <h2 class="demo-title">
              <a href="demo-detail.php" title="See more about &ldquo;Fantastic Voyage&rdquo; by Alejandra Divens">
                <img src="./media/img/fpo55.png" alt="" width="180" height="135"> Fantastic Voyage
              </a>
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
          <li class="demo">
            <h2 class="demo-title">
              <a href="demo-detail.php" title="See more about &ldquo;It's a Mad Mad Mad Mad Mad Mad World&rdquo; by Darryl McConnaughy">
                <img src="./media/img/fpo55.png" alt="" width="180" height="135"> It&#8217;s a Mad Mad Mad Mad Mad Mad World
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
          
          <li class="demo row-first">
            <h2 class="demo-title">
              <a href="demo-detail.php" title="See more about &ldquo;Twenty Years to Midnight&rdquo; by Thaddeus Venture">
                <img src="./media/img/fpo55.png" alt="" width="180" height="135"> Twenty Years to Midnight
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
          <li class="demo">
            <h2 class="demo-title">
              <a href="demo-detail.php" title="See more about &ldquo;Bloodeye&rdquo; by Jefferson Twilight">
                <img src="./media/img/fpo55.png" alt="" width="180" height="135"> Bloodeye
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
    
        </ul><!-- /.gallery -->

      </section><!-- /#tab-submissions -->
      
      <section id="tab-rules" class="block">
        <p>A summary of the rules can be found below.  For a complete look at the terms of the contest please see the <a href="demo-derby-rules.php">Dev Derby Contest Official Rules</a>.</p>
        <ul class="prose">
          <li>Almost anyone can enter (<a href="demo-derby-rules.php">see the rules</a> for exceptions).</li>
          <li>There will be a new contest every month.</li>
          <li>Your entry must meet certain criteria; <a href="demo-derby-rules.php">see the rules</a> for the overall criteria and the Current Challenge section for any special criteria for each contest.</li>
          <li>Each contest runs from the first day of the month to the last day of the month (based on <strong>US Pacific time</strong>).</li>
          <li>Entries will be judged by a panel of qualified reviewers, who may or may not take into account how many &ldquo;likes&rdquo; your entry receives.</li>
          <li>The winners of each month's contest will be announced by the <strong>20th of the following month</strong>.</li>
          <li>You can't win more than once in the same calendar year.</li>
          <li>Please read the <a href="demo-derby-rules.php">Dev Derby Contest Official Rules</a> before submitting your entry.</li>
        </ul>
      </section>
    
      <section id="tab-judging" class="block">
        <p>Entries will be reviewed by the Mozilla team and a panel of expert judges. We will rate the demos on a 1&ndash;5 scale across 4 dimensions:</p>
        <ul class="prose">
          <li><strong>Technology</strong> &ndash; Does the demo showcase the power of open Web technologies?</li>
          <li><strong>Originality</strong> &ndash; How innovative and unique is the demo?</li>
          <li><strong>Aesthetics</strong> &ndash; How good is the visual design and interaction experience?</li>
          <li><strong>Practicality</strong> &ndash; How useful is this demo in enhancing the Web today?</li>
        </ul>
        <p>The overall score will be the average of all 4 components (technology, orginality, aesthetics, and practicality). In the event of a tie, the judges will re-evaluate the tied entries to determine the winner.</p>
        <p>The judges may also take into account how many &ldquo;likes&rdquo; the entries have received from the community. So make sure to share your demo with others and encourage them to visit Dev Derby to &ldquo;vote.&rdquo;</p>
      
        <h2>Expert Judges</h2>
        <ul class="judges">
          <li class="vcard">
             <h3><a href="http://leaverou.me" class="fn url">Lea Verou <img src="./media/img/devderby/judges/leaverou.jpg" alt="" class="photo" width="100" height="100"></a></h3>
             <h4 class="title">Web developer, Co-founder of Fresset Ltd.</h4>
             <p class="twitter"><a href="http://twitter.com/leaverou" class="url nickname">@leaverou</a></p>
             <p>Lea Verou is the lead web developer and designer of Fresset Ltd, which she co-founded in 
             2008. Fresset owns and manages some of the largest greek community websites. Lea has a 
             long-standing passion for open web standards, especially CSS and JavaScript. She loves 
             researching  new ways to use them and shares her findings through her blog, 
             <a href="http://leaverou.me">leaverou.me</a>. She speaks at a number of the largest web 
             development conferences and writes for leading industry publications. Lea also co-organized 
             and occasionally lectures the web development course at the Athens University of Economics 
             and Business.</p>
          </li>
          <li class="vcard">
             <h3><a href="http://ethanmarcotte.com" class="fn url">Ethan Marcotte <img src="./media/img/devderby/judges/ethanmarcotte.jpg" alt="" class="photo" width="100" height="100" title="Photo by Anton Peck"></a></h3>
             <h4 class="title">Web designer, author</h4>
             <p class="twitter"><a href="http://twitter.com/beep" class="url nickname">@beep</a></p>
             <p><a href="http://ethanmarcotte.com/">Ethan Marcotte</a> is a web designer &amp; developer 
             who cares deeply about beautiful design, elegant code, and the intersection of the two. Over 
             the years, Ethan has enjoyed working with such clients as the Sundance Film Festival, Stanford 
             University, <cite>New&nbsp;York Magazine</cite> and The Today Show. He swears profusely 
             <a href="http://twitter.com/beep">on Twitter</a>, and would like to be an 
             <a href="http://unstoppablerobotninja.com/" class="url">unstoppable robot ninja</a> when he grows up. His 
             most recent book is <cite><a href="http://www.abookapart.com/products/responsive-web-design">Responsive Web Design</a></cite>.</p>
          </li>
          <li class="vcard">
             <h3><a href="http://nimbupani.com" class="fn url">Divya Manian <img src="./media/img/devderby/judges/divyamanian.jpg" alt="" class="photo" width="100" height="100"></a></h3>
             <h4 class="title">Web Opener at Opera, Open Web Vigilante</h4>
             <p class="twitter"><a href="http://twitter.com/divya" class="url nickname">@divya</a></p>
             <p>Divya Manian is a Web Opener for Opera Software in Seattle. She made the jump from 
             developing device drivers for Motorola phones to designing websites and has not looked 
             back since. She takes her duties as an Open Web vigilante seriously which has resulted 
             in collaborative projects such as <a href="http://html5readiness.com">HTML5 Readiness</a> 
             and <a href="http://html5boilerplate.com">HTML5 Boilerplate</a>.</p>
          </li> 
        </ul>
      
      </section>
      
      <section id="tab-past">
        <h3>Previous Dev Derby Challenges</h3>
      </section>
    
    </section><!-- /#current-challenge -->
  </div><!-- /.main -->
      
  <div class="sub">
    <section id="prev-winner">
      <h1>Previous Winner</h1>
      <h2 class="title"><a href="demo-detail.php">The Call of Cthulhu</a></h2>
      <h3 class="author"><img src="./media/img/blank.gif" alt="" width="70" height="70"> Art Vandelay</h3>
      <p class="desc">Some brief description of the demo and the challenge that it won.</p>
      <p class="launch"><a href="demo-detail.php">See the Demo</a></p>
    </section><!-- /#prev-winner -->
      
    <section id="challenge-prizes">
      <h1>Prizes</h1>
      <img src="./media/img/devderby/prize-androids.png" alt="" width="135" height="150" class="prize"/>
      <ol>
        <li class="first">
          <h3>Android mobile device</h3>
          <p>Winner gets an Android mobile device from <a rel="external" href="http://www.motorola.com/Consumers/US-EN/Consumer-Product-and-Services/Mobile-Phones/">Motorola</a> or <a rel="external" href="http://www.google.com/url?q=http%3A%2F%2Fwww.samsung.com%2Fus%2Fmobile%2Fcell-phones&sa=D&sntz=1&usg=AFQjCNHM0Afc6Zf3_wxLQyMwN9vBE658Tw">Samsung</a>.</p>
        </li>
        <li class="second">
          <h3>Rickshaw laptop bag</h3>
          <p>Runner-up gets a hand-crafted laptop messenger bag from <a rel="external" href="http://www.rickshawbags.com/bags/laptop-messenger-bag/standard/standard-commuter-laptop-bag-black.html">Rickshaw</a>.</p>
        </li>
        <li class="third">
          <h3>MDN t-shirt</h3>
          <p>3rd place gets a limited edition MDN t-shirt to show off their geek cred.</p>
        </li>
      </ol>
    </section><!-- /#challenge-prizes -->
  </div><!-- /.sub -->
    
    
    <section id="resources">
      <h3>Resources</h3>
      <ul>
        <li class="res-docs"><a href="http://developer.mozilla.org/docs/">Docs</a></li>
        <li class="res-demos"><a href="http://developer.mozilla.org/demos/">Demos</a></li>
        <li class="res-articles"><a href="http://hacks.mozilla.org">Articles</a></li>
      </ul>
    </section>
    
  </section><!-- /#content-main -->

</div>
</section>

<script type="text/javascript" src="./media/js/jquery.hoverIntent.minified.js"></script>
<script type="text/javascript">
// <![CDATA[
  function derbyTabs(targetblock) {
    var currentblock;
  	$("#current-challenge .block").addClass("block-hidden");

    if (targetblock) {
      currentblock = targetblock.replace( /.*?#(.*)/g, "$1" ); // determine which block to show by extracting the id from the href
      tabSwitch(currentblock);
    }
    else if ( !targetblock && (/.*?#tab-*/.test(window.location)) ) { // if no target is supplied, check the url for a fragment id prefixed with "tab-" (this means inbound links can point directly to a tab)
      currentblock = window.location.href.replace( /.*?#(.*)/g, "$1" );
      $("html,body").animate({scrollTop: $("#current-challenge").offset().top - 150}, 0); // HACK: compensate for overshooting the tabs when the page loads
      tabSwitch(currentblock);
    }
    else {
      currentblock = $("#current-challenge .tabs li.current a").attr("href").replace( /.*?#(.*)/g, "$1" );
      tabSwitch(currentblock);
    }
  	$("#"+currentblock).removeClass("block-hidden"); // make the current block visible
  }
  
  function tabSwitch(targettab) {
    var tabs = $("#current-challenge .tabs li a");    
    if (targettab) {
      for (var i = 0; i < tabs.length; i++) { // loop through the tabs
        var tab = $(tabs[i]).attr("href").replace( /.*?#(.*)/g, "$1" ); // strip down the href
        if ( targettab == tab ) { // if one of them matches our target
          $("#current-challenge .tabs li").removeClass("current"); // first clean the slate
          $("#current-challenge .tabs li a[href$=#"+targettab+"]").parents("li").addClass("current"); // then set that tab as current
        }    
      }
    } 
  };
  
  $("#current-challenge .tabs li a").click(function(){
    $("#current-challenge .tabs li").removeClass("current");
    $(this).parents("li").addClass("current");
    derbyTabs( $(this).attr("href").replace( /.*?#(.*)/g, "$1" ) ); // transmit target
    return false;
	});
	
  $("#nav-derby a[rel=tab]").click(function(){
    derbyTabs( $(this).attr("href").replace( /.*?#(.*)/g, "$1" ) ); // transmit target
  });
  
  $(document).ready(function(){
    derbyTabs();
    $("body").addClass("hasJS"); // I think this class is already added by another global script in production, added here for mockup

    $("#upcoming li").hover(
      function(){
        $(this).children(".desc").fadeIn('fast');
      },
      function(){
        $(this).children(".desc").fadeOut('fast');
      }
    );
  });
    
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

<?php foot(); ?>
