# -*- coding: utf-8 -*-

"""
    Script that backs up all the Youtube videos in a users favorites list and sends an asynchronous alert after successful downloads.

    Please edit the "Settings" section below before running the script.

    Requires youtube-dl (http://rg3.github.com/youtube-dl/).
    Notifications require Nofify OSD (https://launchpad.net/notify-osd), which ships with Ubuntu.

    See http://www.github.com/nospampleasemam/youtube_backup for more information and the latest version.

    -------

    This is a derivative work based off the original youtube_backup script written by Henry Hagnäs and available here:
    https://github.com/hagnas/youtube_backup

    The original source is subject to the following copyright:

    Copyright (c) 2010, Henry Hagnäs <henry@hagnas.com>
    All rights reserved.

    The original source and the derived work contained here is subject to the following license:

    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of Henry Hagnäs nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

__authors__ = ("Henry Hagnäs <henry@hagnas.com>", "Dylan Lloyd <dylan@psu.edu>")
__license__ = "BSD"

# Settings

# Edit User and download-directory info. Directory will NOT be
# automatically created. DEFAULT_ICON will display in notifications if
# the script is unable to fetch the video thumbnail from Youtube.
USER = 'nospampleasemam'
DIR = '/home/dylan/youtube_backup/'
YT_DL = '/usr/bin/youtube-dl' # Path to youtube-dl
NOTIFICATIONS = True
DEFAULT_ICON ='/usr/share/icons/gnome/48x48/mimetypes/gnome-mime-application-x-shockwave-flash.png'
YT_OPT = '--no-progress --ignore-errors --continue --max-quality=22 -o "%(stitle)s---%(id)s.%(ext)s"'
# END OF SETTINGS

from xml.etree import cElementTree as ET
import urllib2
import os
import re
import copy
import shlex, subprocess

import pynotify
import tempfile
import string
import hashlib

def get_urls(startindex):
    """ Fetches the next 10 video-URL's from startindex of USER's favourites.
     Modified from example found here: http://stackoverflow.com/questions/1452144/simple-scraping-of-youtube-xml-to-get-a-python-list-of-videos.
    """
    results = []
    data = urllib2.urlopen('http://gdata.youtube.com/feeds/api/users/{user}/favorites?max-results=10&start-index={startindex}'.format(user=USER, startindex=startindex))
    tree = ET.parse(data)
    ns = '{http://www.w3.org/2005/Atom}'
    for entry in tree.findall(ns + 'entry'):
        for link in entry.findall(ns + 'link'):
            if link.get('rel') == 'alternate':
                results.append(link.get('href'))
    return results

def get_all_urls():
    results = []
    result = ['dummy']
    startindex = 1
    while len(result)>0:
        result = get_urls(startindex)
        results = results + result
        startindex = startindex + 10
    return results

def get_video_ids():
    """ Cleans up url_list and returns a list with only the Youtube-video id's. """
    url_list = get_all_urls()
    re_videoid = re.compile('watch\?v=(?P<videoid>.*?)&')
    videolist = {}
    for i in url_list:
        t = re_videoid.search(i)
        videolist[t.group('videoid')] = i
    return videolist

def check_for_existing():
    """ Checks the download-folder for existing videos with same id and removes from videolist. """
    videolist = get_video_ids()
    filelist = os.listdir(DIR)
    for video in copy.deepcopy(videolist):
        for files in filelist:
            if re.search(video,files):
                del videolist[video]
    return videolist

def download_files(videolist):
    """ Uses subprocess to trigger a download using youtube-dl of the list created earlier. """
    os.chdir(DIR)
    args = shlex.split(YT_DL + ' ' + YT_OPT)
    if NOTIFICATIONS: regex = re.compile("\[download\] Destination: (.+)")
    for item in videolist:
        if item:
            thread = subprocess.Popen(args + [item], stdout=subprocess.PIPE)
            output = thread.stdout.read()
            if NOTIFICATIONS:
                video_file = regex.findall(output)
                if len(video_file) == 0:
                    break
                thumbnail = hashlib.md5('file://' + DIR + video_file[0]).hexdigest() + '.png'
                # Two '/'s instead of three because the path is
                # absolute; I'm not sure how this'd work on windows.
                title, sep, vid_id = video_file[0].rpartition('---')
                title = string.replace(title, '_', ' ')
                thumbnail = os.path.join(os.path.expanduser('~/.thumbnails/normal'), thumbnail)
                if not os.path.isfile(thumbnail):
                    opener = urllib2.build_opener()
                    try:
                        page = opener.open('http://img.youtube.com/vi/' + item + '/1.jpg')
                        thumb = page.read()
                        # The thumbnail really should be saved to
                        # ~/.thumbnails/normal (Thumbnail Managing
                        # Standard)
                        # [http://jens.triq.net/thumbnail-spec/]
                        # As others have had problems anyway
                        # (http://mail.gnome.org/archives/gnome-list/2010-October/msg00009.html)
                        # I decided not to bother at the moment.
                        temp = tempfile.NamedTemporaryFile(suffix='.jpg')
                        temp.write(thumb)
                        temp.flush()
                        note = pynotify.Notification(title, 'video downloaded', temp.name)
                    except:
                        note = pynotify.Notification(title, 'video downloaded', DEFAULT_ICON)
                else:
                    # Generally, this will never happen, because the
                    # video is a new file.
                    note = pynotify.Notification(title, 'video downloaded', thumbnail)
                note.show()

def main():
    videolist = check_for_existing()
    if len(videolist)>0:
        download_files(videolist)

if __name__ == '__main__':
    main()
