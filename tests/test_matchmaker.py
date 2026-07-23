import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import contextlib
import pytest
from shared.model.piece import Color
from server.services.matchmaker import Matchmaker


pytestmark = pytest.mark.asyncio


async def _cancel(task):
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def test_first_two_compatible_players_are_paired():
    mm = Matchmaker()
    task_a = asyncio.create_task(mm.join(object(), "alice", 1200))
    await asyncio.sleep(0)  # let alice register as waiting before bob joins

    color_b, session_b = await mm.join(object(), "bob", 1250)
    color_a, session_a = await task_a

    assert session_a is session_b
    assert color_a == Color.WHITE  # first joiner
    assert color_b == Color.BLACK
    assert session_a.names[Color.WHITE] == "alice"
    assert session_a.names[Color.BLACK] == "bob"
    assert session_a.ratings[Color.WHITE] == 1200
    assert session_a.ratings[Color.BLACK] == 1250
    assert mm._waiting == []


async def test_out_of_rating_range_does_not_pair_and_cleans_up_on_timeout():
    mm = Matchmaker()
    task_a = asyncio.create_task(mm.join(object(), "alice", 1200))
    await asyncio.sleep(0)

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(mm.join(object(), "carol", 1400), timeout=0.05)

    # Carol's entry was removed by join()'s finally block once her wait was cancelled.
    assert [w.username for w in mm._waiting] == ["alice"]

    await _cancel(task_a)


async def test_matches_first_compatible_waiting_player_not_closest_rated():
    mm = Matchmaker()
    # alice and eve must NOT be mutually compatible, or eve would auto-pair with
    # alice the instant she joins — both must independently be within range of
    # frank (the actual test subject) so frank has two eligible candidates.
    task_alice = asyncio.create_task(mm.join(object(), "alice", 1100))  # queued first
    await asyncio.sleep(0)
    task_eve = asyncio.create_task(mm.join(object(), "eve", 1250))      # queued second, closer to frank
    await asyncio.sleep(0)

    color_frank, session_frank = await mm.join(object(), "frank", 1200)
    color_alice, session_alice = await task_alice

    # First-fit: frank pairs with alice (queued earlier), not eve (closer rating).
    assert session_frank is session_alice
    assert session_alice.names[Color.WHITE] == "alice"
    assert session_alice.names[Color.BLACK] == "frank"
    assert [w.username for w in mm._waiting] == ["eve"]

    await _cancel(task_eve)
