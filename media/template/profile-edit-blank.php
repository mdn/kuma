<?php include "./inc/template.php"; 
head(
  $title = 'Edit Your Profile | Mozilla Developer Network',
  $pageid = '', 
  $bodyclass = 'profile',
  $extra_headers = '
  <link rel="stylesheet" type="text/css" href="./media/css/demos.css">
  '
); ?>

<section id="content">
<div class="wrap">

  <section id="content-main" class="full">

    <form id="profile-edit" class="submission" method="post" action="profile-edit.php">
      <h1 class="page-title">neilhimself</h1>
      
      <div class="extra">
        <figure class="acc-avatar">
          <img src="./media/img/blank.gif" alt="" width="120" height="120" class="photo avatar">
          <figcaption>
            Change your avatar at <a href="http://gravatar.com" rel="external">gravatar.com</a>
          </figcaption>
        </figure>
        
        <ul>
          <li><a href="profile-blank.php">View profile</a></li>
          <li><a href="#">Change password or email</a></li>
          <li class="delete"><a href="#">Delete my account</a></li>
        </ul>
      </div>
      
      <fieldset class="section notitle" id="personal">
        <ul>
          <li><label for="pers-displayname">Name</label> <input type="text" id="pers-displayname" name="display_name"></li>
          <li><label for="pers-title">Title</label> <input type="text" id="pers-title" name="title"></label></li>
          <li><label for="pers-company">Company</label> <input type="text" id="pers-company" name="company"></label></li>
          <li><label for="pers-location">Location</label> <input type="text" id="pers-location" name="location"></li>
          <li class="wordcount">
            <label for="acc-bio">About Me <span class="note"><b id="bio_wordcount" class="counter">150</b> words remaining</span></label> 
            <textarea id="acc-bio" name="bio" cols="50" rows="7"></textarea>          
          </li>
          <li>
            <label for="pers-interests">Interests (tags)</label>
            <p class="note">Separate tags with commas or spaces. Join multi-word tags with double quotes, like "web standards".</p>
            <input type="text" name="interests" id="pers-interests">
		        <button type="button">Add</button>
          </li>
        </ul>
      </fieldset>

      <fieldset class="section" id="elsewhere">
        <legend><b>My Other Profiles</b></legend>
        
        <ul>
          <li class="site website">
            <label for="site_website">Website/blog</label> 
            <input type="text" id="site_website" name="website" class="url" value="http://">
          </li>
          <li class="site twitter">
            <label for="site_twitter">Twitter</label> 
            <input type="text" id="site_twitter" name="twitter" class="url" value="http://twitter.com/">
          </li>
          <li class="site github">
            <label for="site_github">GitHub</label> 
            <input type="text" id="site_github" name="github" class="url" value="http://github.com/">
          </li>
          <li class="site stackover">
            <label for="site_stackover">StackOverflow</label> 
            <input type="text" id="site_stackover" name="stackover" class="url" value="http://stackoverflow.com/users/">
          </li>
          <li class="site linkedin">
            <label for="site_linkedin">LinkedIn</label> 
            <input type="text" id="site_linkedin" name="linkedin" class="url" value="http://www.linkedin.com/in/">
          </li>
        </ul>

      </fieldset>
      
      <p class="fm-submit"><button type="submit">Save Changes</button></p>

    </form>



  </section><!-- /#content-main -->

<script type="text/javascript">
// <![CDATA[
$(document).ready(function(){
  
  $("#elsewhere .site select").change(function(){
    if (this.value === "website") {
      $(this).parents().find(".url").val("http://").focus();
    }
    else if (this.value === "twitter") {
      $(this).parents().find(".url").val("http://twitter.com/").focus();
    }
    else if (this.value === "github") {
      $(this).parents().find(".url").val("http://github.com/").focus();
    }
    else if (this.value === "stackover") {
      $(this).parents().find(".url").val("http://stackoverflow.com/users/").focus();
    }
    else if (this.value === "linkedin") {
      $(this).parents().find(".url").val("http://www.linkedin.com/in/").focus();
    }
  });


  // word count
  $('.wordcount').each(function(i,el){
    function updateWordCount(){
      var words = $.trim( field.val() ).split(' ');
      if( words[0] == '' ){ words.length = 0; }
      currcount = limit - words.length;
      placeholder.text( currcount );
      if ( words.length >= limit &&
           placeholder.parent().css('color') != '#900' )
      {
        placeholder.parent().css('color','#900');
      }
      else if ( words.length < limit &&
                placeholder.parent().css('color') == '#900' )
      {
        placeholder.parent().css('color','');
      }
    }
    var placeholder = $(el).find('.counter');
    var limit = parseInt( placeholder.text() );
    var currcount = 0;
    var field = $(el).children('textarea');
    updateWordCount();
    field.keypress(updateWordCount);
  })

});	
// ]]>
</script>

</div>
</section>
<?php foot(); ?>
