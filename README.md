# yottu

#### Important: I'm using this project to learn python, for security reasons I do not recommend running it without privilege separation
##### docker image: https://gist.github.com/yottu/e67344e915964cc384094e5df32d6bca

![alt tag](https://raw.github.com/yottu/yottu/master/screenshot.png)
_imageboard appliances for professional shitposting in an enterprise environment_

## INSTALL (FIXME: missing packages)
### Debian GNU/Linux
```
sudo aptitude install python python-requests python-bs4 python-pil \ 
                      w3m-img libimlib2 ranger feh xterm mpv sxiv
git clone git://github.com/yottu/yottu.git
cd yottu/
python yottu.py
```

### Arch Linux
```
sudo pacman -S python python2-pip w3m ranger imlib2 git feh
sudo pip2 install bs4 requests
git clone git://github.com/yottu/yottu.git
cd yottu/
python2 yottu.py
```

## Dependencies
- python2.7 with Beautiful Soup 4 and requests
- w3m-img for displaying images in the terminal
- ranger and xterm for selecting attachments
- feh and libimlib2 for viewing jpg and png files
- mpv for viewing webm files
- sxiv for viewing gif files

## Keys
```
w 		- 	scroll up (Alt: Cursor up)
s 		- 	scroll down (Alt: Curser down)
r		-	refresh thread
D		-	download all images
Alt+c		-	Open in browser (/set app.browser)
Alt+q 		-	quit
x		-	close window
p, n 		- 	previous/next window
1-0 		-	switch to window 1-10
```

### Command mode: / or i
```
board 		- set board context (e.g. /board int for /int/)
catalog 	- list threads of board context
join <thread>	- open thread
join board/<search term>	- join thread or open catalog for multiple matches
Curser Up/Down 	- Cycle through command/text mode history

autojoin 		- list threads to join on program start
	autojoin save 	- save current threads in autojoin list
	autojoin clear	- removes all thread from autojoin list

find <re>		- search for regular expression in thread  

mpv	<source>	- play video from source with comments from current board as subtitles
playall			- play all youtube videos in thread (mpv)
twitch <channel>	- stream from twitch channel (mpv)
youtube <source>	- play video from youtube (mpv)
	
set 				- lists options saved in ~/.config/yottu/config
	set default_context 	- board context on program start
	set nickname 		- Name#Trip
	
```

### Text mode: t
```
Alt+r 		-	 Start ranger in --choosefile mode (file location written to /tmp/file)
Alt+f 		- 	 Attach file (currently content of /tmp/file/ (not /tmp/file itself!))
Alt+Return 	-	 Insert newline
```

### Global
```
Page Up 			- scroll 5 lines up (Opposite: Page Down)
Pos1				- scroll up to start (Opposite: End)
Mouse Wheel Up/Down 		- scroll up/down (scrolls through windows if curser placed on title bar)
Left Mouse Button 		- mark line, displays thumb 
	v/right mouse button 	- show full image
	f 			- windowed feh
	F 			- fullscreen feh
	t 			- reply to post number
	b			- set image as background (requires feh)
```

### I'm not rich
BTC: 135Hedzpgbhsiye5TnCus9QY31pCZHKYYJ
