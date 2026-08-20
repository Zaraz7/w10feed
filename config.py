# W10Feed configuration file
#
# !!! Lines starting with '#' will be ignored
# Example:

#PROFILES={
#   "myblog":{
#       "type":"blog",
#       "host":"ftp.w10.host",
#       "user":"example",
#       "passwd":"example_password",
#       "url":"https://example.w10.site",
#       "lang":"en-EN",
#       "title":"Title",
#       "out":"blog.xml",
#       "maxitems":50
#   }
#}

# To run "myblog" profile, use:
# w1f.py profile  myblog
# 
# This config is equivalent to
# w1f.py gen --type blog --host ftp.w10.host --user example --passwd example_password --url https://example.w10.site --lang en-EN --title 'Title' --out blog.xml --maxitems 50
#
# If you don't want to store password in configuration, 
# you can write profile without 'passwd'. 
# Then w1f ask you to enter it. 