#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Programmatically control a ROS bag file.

This module implements the base class, and the various functions.

Currently implemented are:

    * ``rosbag play``

"""
import logging
import subprocess as sp
import time
try:
    from types import StringTypes
except ImportError:
    StringTypes = str


try:
    input = raw_input
except NameError:
    pass


logger = logging.getLogger("bag_player")


class BagError(Exception):
    """
    Catch bag player exceptions.

    """


class MissingBagError(BagError):
    """
    Bag file was not specified.

    """
    msg = "No Bag files were specified."


class BagNotRunningError(BagError):
    """
    Raised when interaction is attempted with a bag file which is not running.

    """
    def __init__(self, action="talk to"):
        message = u"Cannot {} process while bag is not running.".format(action)
        super(BagNotRunningError, self).__init__(message)


class Bag(object):
    """
    Open and manipulate a bag file programmatically.

    Parameters
    ----------
    filenames : StringTypes | List[StringTypes]
        The location of the bag files.

    Attributes
    ----------
    filenames : List[StringTypes]
        The location of the bag files.
    process : subprocess.Popen
        The process containing the running bag file.

    """
    def __init__(self, filenames):
        if filenames in ("", u"", []):
            raise MissingBagError
        if isinstance(filenames, StringTypes):
            filenames = [filenames]
        self.filenames = filenames
        self.process = None

    def send(self, string):
        """
        Write something to process stdin.

        Parameters
        ----------
        string : str
            The string to write.

        Raises
        ------
        BagNotRunningError
            If interaction is attempted when the bag file is not running.

        """
        try:
            self.process.stdin.write(string)
        except AttributeError:
            raise BagNotRunningError()

    def stop(self):
        """
        Stop a running bag file.

        Raises
        ------
        BagNotRunningError
            If the bag file is not running.

        """
        try:
            self.process.terminate()
            self.process.kill()
        except AttributeError:
            raise BagNotRunningError("stop")

    def wait(self):
        """
        Block until process is complete.

        Raises
        ------
        BagNotRunningError
            If the bag file is not running.

        """
        try:
            self.process.wait()
        except AttributeError:
            raise BagNotRunningError("wait for")

    @property
    def is_running(self):
        """
        Check whether the bag file is running.

        Returns
        -------
        bool
            The bag file is running.

        """
        try:
            return self.process.poll() is None
        except AttributeError:
            return False

    def __enter__(self):
        """
        Context manager entry point.

        """
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager exit point.

        """
        time.sleep(1)  # For pretty output.
        if self.is_running:
            if exc_type is None:
                logger.warning("Exited while process is still running.")
                logger.info("Hint: Use Bag.wait() or Bag.play(wait=True) "
                            "to wait until completion.")
            else:
                self.stop()

        if exc_type == KeyboardInterrupt:
            logger.info("User exit.")
            return True
        elif exc_type is not None:
            logger.critical("An error occurred. Exiting.")
        else:
            logger.info("Goodbye!")

    def __repr__(self):
        return "<Bag({})>".format(self.filenames)


class BagPlayer(Bag):
    """
    Play Bag files.

    """
    def play(self, wait=False, stdin=sp.PIPE, stdout=None, stderr=None,
             quiet=None, immediate=None, start_paused=None, queue_size=None,
             publish_clock=None, clock_publish_freq=None, delay=None,
             publish_rate_multiplier=None, start_time=None, duration=None,
             loop=None, keep_alive=None):
        """
        Play the bag file.

        Parameters
        ----------
        wait : Optional[Bool]
            Wait until completion.
        stdin : Optional[file]
            The stdin buffer. Default is subprocess.PIPE.
        stdout : Optional[file]
            The stdout buffer.
        stderr : Optional[file]
            The stderr buffer.
        quiet : Optional[Bool]
            Suppress console output.
        immediate : Optional[Bool]
            Play back all messages without waiting.
        start_paused : Optional[Bool]
            Start in paused mode.
        queue_size : Optional[int]
            Set outgoing queue size. Default is 100.
        publish_clock : Optional[Bool]
            Publish the clock time.
        clock_publish_freq : Optional[float]
            The frequency, in Hz, at which to publish the clock time. Default is
            100.
        delay : Optional[float]
            The number of seconds to sleep afer every advertise call (e.g., to
            allow subscribers to connect).
        publish_rate_multiplier : Optional[float]
            The factor by which to multiply the publish rate.
        start_time : Optional[float]
            The number of seconds into the bag file at which to start.
        duration : Optional[float]
            The number of seconds from the start to play.
        loop : Optional[Bool]
            Loop playback.
        keep_alive : Optional[Bool]
            Keep alive past end of bag (e.g. for publishing latched topics).

        """
        arguments = ["rosbag", "play"]
        arguments.extend(self.filenames)

        if quiet:
            arguments.append("-q")
        if immediate:
            arguments.append("-i")
        if start_paused:
            arguments.append("--pause")
        if queue_size is not None:
            arguments.append("--queue={}".format(queue_size))
        if publish_clock:
            arguments.append("--clock")
        if clock_publish_freq is not None:
            arguments.append("--hz={}".format(clock_publish_freq))
        if delay is not None:
            arguments.append("--delay={}".format(delay))
        if publish_rate_multiplier is not None:
            arguments.append("--rate={}".format(publish_rate_multiplier))
        if start_time is not None:
            arguments.append("--start={}".format(start_time))
        if duration is not None:
            arguments.append("--duration={}".format(duration))
        if loop:
            arguments.append("-l")
        if keep_alive:
            arguments.append("-k")

        self.process = sp.Popen(arguments,
                                stdin=stdin, stdout=stdout, stderr=stderr)
        if wait:
            self.wait()

    def pause(self):
        """
        Pause the bag file.

        """
        self.send(" ")

    def resume(self):
        """
        Resume the bag file.

        """
        self.send(" ")

    def step(self):
        """
        Step through a paused bag file.

        """
        self.send("s")
