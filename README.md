# Blug #

*Because "I just blogged about it" is too difficult to say*

## Intro ##

Blug is a static site generator for Markdown based blogs. It currently
uses the Octopress based theme from www.jeffknupp.com, but this will change shortly.
While Blug generates static pages, the ultimate purpose of Blug is to run as a standalone process capable of 'psuedo-dynamic' site
interaction. Today's blogs are static, so much so that static blog generation tools have become the new 'Create a Twitter Clone'
for tutorials topics. I envision Blug as an intelligent agent, a daemon able to dynamically regenerate
your site and insert content when triggered by external events. Stuff like dynamically re-generating a post to include a link
to comments on your post on HackerNews or reddit when Blug sees this event has occurred. Or re-generating to scale back the included css/javascript when Blug sees your webserver is getting hammered. These are the kinds of things I'm interested in exploring.

## Installation ##
Blug currently requires no installation, though running ```python setup.py install``` 
will create 'install' the blug.py script. You can also get it from pip using ```pip install blug```.

## Usage ##
Edit the ```config.yaml``` file with values appropriate for your site. They should be pretty self-explanatory.
Once done, place your posts in a directory called ```content``` (this is the default location Blug checks for
posts). Each post follows the Octopress/Jekyll naming convention for posts: year-month-day-title-of-post-as-slug.
Once you've got everything set up, there are three components to the ```blug.py``` script.

### Creating a New Post ###
```python blug.py post 'How Javascript is Ruining a Generation of Programmers' ``` This will create a new post
in your ```content``` directory with the appropriate filename and yaml front matter. 

### Generating the Site ###
```python blug.py generate``` This **deletes and regenerates the current generated content**. Run this whenever you
make a change to a post or after finishing a new one. The output in the ```generated``` directory is the complete site.

### Viewing Your Site Locally ###
```python blug.py serve <port> <host> <path>``` This starts a webserver locally to allow you to preview your site. Use
```generated``` as the ```path``` argument to serve files using your generated site as the root.

## Coming Soon ##
A number of features have either been committed or are in the process of being committed

* **Live Mardown Post Editing**- Start up the included webserver and navigate to host:port/create to
create a new post with live Markdown translation. In the left pane you enter normal Markdown test. The right
pane is updated with the translated HTML in real time. No more regenerating your entire site just to see if you
remembered how to do a nested list in Markdown.

* **Git(hub)/Dropbox Integration**- Automatically deploy new posts and changes to your blog on the back of commits
to your local git repository, commit to Github, or Dropbox file uploads

* **The Blug Server**- The real reason I created Blug. Stay tuned.
