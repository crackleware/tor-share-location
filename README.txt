HOW IT WORKS:

	you run tor-share-location.py. it's a console program. it will start
	tor subprocess and generate secret onion url to web page on internal
	web server showing current device location on a map. you can send this
	secret onion url to anyone who should be able to see your location.
	when they receive the onion url they browse to it in tor browser on
	their device. they see your location. the program will notify you each
	time they request your location. when you press enter the program will
	exit, stopping tor subprocess and internal web server.

	the program uses tor control protocol over unix domain socket
	to create ephemeral hidden service which is forwarding all requests to
	internal web server. internal web server is also accepting HTTP
	requests only over unix domain socket. internal web server will serve
	static html page containing map images for several zoom levels. filled
	blue circle on a map indicates current location of device.

TO USE IT IN Termux (https://termux.com):

    install Termux (https://play.google.com/store/apps/details?id=com.termux)

    install Termux:API (https://play.google.com/store/apps/details?id=com.termux.api)

    you do this once:

        git clone https://github.com/crackleware/tor-share-location
        cd tor-share-location
        ./install-deps-in-termux.sh

    then before the first use or when you change region or city:

        ./download-osm-tiles.py

    then each time you want to share your location to a friend over tor network:

        ./tor-share-location.py

    temporary onion link will be generated. when someone opens this link in
    tor browser, map and location of your device will be displayed.  press
    enter to stop sharing.
