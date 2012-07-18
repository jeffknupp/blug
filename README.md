# Blug #

*Because "I just blogged about it" is too difficult to say*

## Intro ##

Blug is a static site generator for Markdown based blogs. It currently
uses the Octopress based theme from www.jeffknupp.com, but this will change shortly.

## Installation ##
Blug currently requires no installation, though running '''python setup.py install''' 
will create 'install' the blug.py script. You can also get it from pip using '''pip install blug'''.

## Usage ##
Edit the '''config.yaml''' file with values appropriate for your site. They should be pretty self-explanatory.
Once done, place your posts in a directory called '''content''' (this is the default location Blug checks for
posts). Each post follows the Octopress/Jekyll naming convention for posts: year-month-day-title-of-post-as-slug.
Once you've got everything set up, there are three components to the '''blug.py''' script.

### Creating a New Post ###
'''python blug.py post 
