=====
Usage
=====

To use ROS Bag Python Controller in a project, just import whatever components you need::

    import pyrosbag as prb

For instance, to forward user input::

    with prb.BagPlayer("example.bag") as example:
        example.play()
        while example.is_running():
            inputs = input()
            kotaro.send(inputs)

Or, to play the bag file intermittently::

    import time

    INTERVAL = 3  # seconds

    with BagPlayer("example.bag") as example:
        example.play()
        while example.is_running():
            # Run for INTERVAL seconds.
            time.sleep(INTERVAL)

            # Pause for INTERVAL seconds.
            # While paused, step through at a rate of once a second.
            example.pause()
            for _ in range(INTERVAL - 1):
                time.sleep(1)
                example.step()
            time.sleep(1)

            # Resume playing the bag file.
            example.resume()
