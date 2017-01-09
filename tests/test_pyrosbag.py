#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for ``pyrosbag`` module.

"""
try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch
import logging
import subprocess as sp

import hypothesis as hyp
import hypothesis.strategies as hst
import pytest

from pyrosbag import pyrosbag as prb


class TestErrors(object):
    def test_MissingBagError(self):
        with pytest.raises(prb.MissingBagError,
                message="No Bag files were specified."):
            raise prb.MissingBagError()

    def test_BagNotRunningError_no_args(self):
        with pytest.raises(prb.BagNotRunningError,
                message="Cannot talk to process while bag is not running."):
            raise prb.BagNotRunningError()

    @hyp.given(hst.text())
    def test_BagNotRunningError_with_args(self, action):
        message = u"Cannot {} process while bag is not running.".format(action)
        with pytest.raises(prb.BagNotRunningError, message=message):
            raise prb.BagNotRunningError(action)


class TestBag(object):
    @hyp.given(hst.text())
    def setup(self, filename):
        mock_process = MagicMock()
        try:
            self.stopped_bag = prb.Bag(filename)
            self.running_bag = prb.Bag(filename)
        except prb.MissingBagError:
            hyp.reject()
        self.running_bag.process = mock_process

    @hyp.given(hst.text())
    def test_init_single_filename(self, filename):
        try:
            bag = prb.Bag(filename)
        except prb.MissingBagError:
            hyp.reject()
        assert bag.filenames == [filename]

    @hyp.given(hst.lists(hst.text()))
    def test_init_multiple_filenames(self, filenames):
        try:
            bag = prb.Bag(filenames)
        except prb.MissingBagError:
            hyp.reject()
        assert bag.filenames == filenames

    @hyp.given(hst.one_of(hst.text(), hst.lists(hst.text())))
    def test_init_process_always_none(self, filenames):
        try:
            bag = prb.Bag(filenames)
        except prb.MissingBagError:
            hyp.reject()
        assert bag.process is None

    @hyp.given(hst.text())
    def test_send_sends_when_running(self, command):
        self.running_bag.send(command)
        assert self.running_bag.process.stdin.write.called_with(command)

    @hyp.given(hst.text())
    def test_send_raises_error_when_not_running(self, command):
        with pytest.raises(prb.BagNotRunningError):
            self.stopped_bag.send(command)
    
    def test_stop_stops_when_running(self):
        self.running_bag.stop()
        assert self.running_bag.process.terminate.called_once()
        assert self.running_bag.process.kill.called_once()

    def test_stop_raises_error_when_not_running(self):
        with pytest.raises(prb.BagNotRunningError):
            self.stopped_bag.stop()

    def test_wait_waits_when_running(self):
        self.running_bag.wait()
        assert self.running_bag.process.wait.called_once()

    def test_wait_raises_error_when_not_running(self):
        with pytest.raises(prb.BagNotRunningError):
            self.stopped_bag.wait()

    def test_is_running_is_false_when_stopped(self):
        assert self.stopped_bag.is_running == False

    @hyp.given(hst.integers())
    def test_is_running_is_false_when_finished(self, retcode):
        self.running_bag.process.poll.return_value = retcode
        assert self.running_bag.is_running == False

    def test_is_running_is_true_when_running(self):
        self.running_bag.process.poll.return_value = None
        assert self.running_bag.is_running == True

    @hyp.given(hst.one_of(hst.text(), hst.lists(hst.text())))
    def test_enter_returns_self(self, filenames):
        with patch.object(prb, "time", autospec=True):
            try:
                raw_bag = prb.Bag(filenames)
                with prb.Bag(filenames) as context_bag:
                    assert context_bag.filenames == raw_bag.filenames
                    assert context_bag.process == raw_bag.process
            except prb.MissingBagError:
                hyp.reject()

    def test_exit_while_running_generates_warning(self):
        with patch.object(prb, "logger", autospec=True) as mock_logger:
            with patch.object(prb, "time", autospec=True):
                with prb.Bag("example.bag") as context_bag:
                    context_bag.process = MagicMock()
                    context_bag.process.poll.return_value = None
                assert mock_logger.warning.called
                assert mock_logger.info.called

    def test_exit_while_running_with_error_stops_but_no_warning(self):
        with patch.object(prb, "logger", autospec=True) as mock_logger:
            with patch.object(prb, "time", autospec=True):
                with patch.object(prb.Bag, "stop", autospec=True) as mock_stop:
                    try:
                        with prb.Bag("example.bag") as context_bag:
                            context_bag.process = MagicMock()
                            context_bag.process.poll.return_value = None
                            raise prb.BagError
                    except prb.BagError:
                        assert not mock_logger.warning.called
                        assert mock_logger.critical.called
                        assert not mock_logger.info.called
                        mock_stop.assert_called_once_with(context_bag)

    def test_normal_exceptions_get_reraised(self):
        with patch.object(prb, "time", autospec=True):
            for exception in (prb.BagError, AssertionError):
                with pytest.raises(exception):
                    with prb.Bag("example.bag") as context_bag:
                        context_bag.process = MagicMock()
                        context_bag.process.poll.return_value = None
                        raise exception

    def test_keyboard_interrupt_does_not_reraise_exception(self):
        with patch.object(prb, "logger", autospec=True) as mock_logger:
            with patch.object(prb, "time", autospec=True):
                with prb.Bag("example.bag") as context_bag:
                    context_bag.process = MagicMock()
                    context_bag.process.poll.return_value = None
                    raise KeyboardInterrupt
                assert not mock_logger.warning.called
                assert not mock_logger.critical.called
                assert mock_logger.info.called

    @hyp.given(hst.text())
    def test_repr_with_single_filename(self, filename):
        try:
            assert repr(prb.Bag(filename)) == u"<Bag({})>".format([filename])
        except prb.MissingBagError:
            hyp.reject()

    @hyp.given(hst.lists(hst.text()))
    def test_repr_with_multiple_filenames(self, filenames):
        try:
            assert repr(prb.Bag(filenames)) == u"<Bag({})>".format(filenames)
        except prb.MissingBagError:
            hyp.reject()

class TestBagPlayer(object):
    @hyp.given(hst.text())
    def setup(self, filename):
        mock_process = MagicMock()
        try:
            self.running_bag = prb.BagPlayer(filename)
        except prb.MissingBagError:
            hyp.reject()
        self.running_bag.process = mock_process

    def test_pause_sends_space(self):
        with patch.object(prb.BagPlayer, "send", autospec=True) as mock_send:
            self.running_bag.pause()
            mock_send.assert_called_once_with(self.running_bag, " ")

    def test_resume_sends_space(self):
        with patch.object(prb.BagPlayer, "send", autospec=True) as mock_send:
            self.running_bag.resume()
            mock_send.assert_called_once_with(self.running_bag, " ")

    def test_step_sends_s(self):
        with patch.object(prb.BagPlayer, "send", autospec=True) as mock_send:
            self.running_bag.step()
            mock_send.assert_called_once_with(self.running_bag, "s")

    def test_play_with_one_filename(self):
        with patch.object(prb, "sp", autospec=True) as mock_sp:
            mock_sp.PIPE = sp.PIPE
            self.running_bag.play()
            arguments = ["rosbag", "play", self.running_bag.filenames[0]]
            mock_sp.Popen.assert_called_once_with(arguments,
                    stdin=mock_sp.PIPE, stdout=None, stderr=None)

    @hyp.given(hst.lists(hst.text()))
    def test_play_with_multiple_filenames(self, filenames):
        with patch.object(prb, "sp", autospec=True) as mock_sp:
            mock_sp.PIPE = sp.PIPE
            try:
                with patch.object(prb, "time", autospec=True):
                    with prb.BagPlayer(filenames) as running_bag:
                        running_bag.play()
                        arguments = ["rosbag", "play"] + running_bag.filenames
                        mock_sp.Popen.assert_called_once_with(arguments,
                                stdin=mock_sp.PIPE, stdout=None, stderr=None)
            except prb.MissingBagError:
                hyp.reject()

    def _run_argument_true(self, argument, addition):
        with patch.object(prb, "sp", autospec=True) as mock_sp:
            mock_sp.PIPE = sp.PIPE
            kwargs = {argument: True}
            self.running_bag.play(**kwargs)
            arguments = ["rosbag", "play", self.running_bag.filenames[0],
                         addition]
            mock_sp.Popen.assert_called_once_with(arguments,
                    stdin=mock_sp.PIPE, stdout=None, stderr=None)

    def _run_argument_false(self, argument, addition=None):
        with patch.object(prb, "sp", autospec=True) as mock_sp:
            mock_sp.PIPE = sp.PIPE
            kwargs = {argument: False}
            self.running_bag.play(**kwargs)
            if addition is None:
                arguments = ["rosbag", "play", self.running_bag.filenames[0]]
            else:
                arguments = ["rosbag", "play", self.running_bag.filenames[0],
                             addition]
            mock_sp.Popen.assert_called_once_with(arguments,
                    stdin=mock_sp.PIPE, stdout=None, stderr=None)

    def _run_boolean_argument(self, argument, addition, addition_if_false=None):
        self._run_argument_true(argument, addition)
        self._run_argument_false(argument, addition_if_false)

    def test_play_with_quiet(self):
        self._run_boolean_argument("quiet", "-q")

    def test_play_with_immediate(self):
        self._run_boolean_argument("immediate", "-i")

    def test_play_with_start_paused(self):
        self._run_boolean_argument("start_paused", "--pause")

    def test_play_with_publish_clock(self):
        self._run_boolean_argument("publish_clock", "--clock")

    def test_play_with_loop(self):
        self._run_boolean_argument("loop", "-l")

    def test_play_with_keep_alive(self):
        self._run_boolean_argument("keep_alive", "-k")

    def _run_argument_numeric(self, argument, addition, input_type):
        @hyp.given(input_type())
        def numeric_argument_run(number):
            with patch.object(prb, "sp", autospec=True) as mock_sp:
                mock_sp.PIPE = sp.PIPE
                kwargs = {argument: number}
                self.running_bag.play(**kwargs)
                arguments = ["rosbag", "play", self.running_bag.filenames[0],
                             "--{}={}".format(addition, number)]
                mock_sp.Popen.assert_called_once_with(arguments,
                        stdin=mock_sp.PIPE, stdout=None, stderr=None)

        numeric_argument_run()

    def test_play_with_queue_size(self):
        self._run_argument_numeric("queue_size", "queue", hst.integers)

    def test_play_with_clock_publish_freq(self):
        self._run_argument_numeric("clock_publish_freq", "hz", hst.floats)

    def test_play_with_delay(self):
        self._run_argument_numeric("delay", "delay", hst.floats)

    def test_play_with_publish_rate_multiplier(self):
        self._run_argument_numeric("publish_rate_multiplier", "rate",
                                   hst.floats)

    def test_play_with_start_time(self):
        self._run_argument_numeric("start_time", "start", hst.floats)

    def test_play_with_duration(self):
        self._run_argument_numeric("duration", "duration", hst.floats)

    def test_wait_waits_when_running(self):
        with patch.object(prb, "sp", autospec=True) as mock_sp:
            with patch.object(prb.BagPlayer, "wait",
                              autospec=True) as mock_wait:
                self.running_bag.play(wait=True)
                mock_wait.assert_called_once_with(self.running_bag)
