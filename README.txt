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
